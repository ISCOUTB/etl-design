import type { sendUnaryData, ServerUnaryCall } from "@grpc/grpc-js";
import type { formula_parser } from "@sloth/packages-proto-utils-js";
import { Server, ServerCredentials } from "@grpc/grpc-js";
import { SpanStatusCode, trace } from "@opentelemetry/api";
import {
    requestDeserialize,
    requestSerialize,
    responseDeserialize,
    responseSerialize,
} from "@sloth/packages-proto-utils-js";
import { Effect } from "effect";
import { BindPortError, settings } from "@/core/";
import { handler } from "@/handlers/handler";
import { setupTelemetry } from "@/instrumentation";
import { logger } from "@/utils/";

const tracer = trace.getTracer("formula-parser");

export function parseFormula(
    call: ServerUnaryCall<
        formula_parser.FormulaParserRequest,
        formula_parser.FormulaParserResponse
    >,
    callback: sendUnaryData<formula_parser.FormulaParserResponse>,
) {
    const span = tracer.startSpan("grpc.ParseFormula", {
        attributes: {
            "rpc.system": "grpc",
            "rpc.service": "formul_parser.FormulaParser",
            "rpc.method": "ParseFormula",
            "rpc.request.formula": call.request.formula,
            "rpc.request.peer": call.getPeer(),
        },
    });

    const startTime = Date.now();
    logger.info("[parseFormula] request received", {
        formula: call.request.formula,
        peer: call.getPeer(),
    });

    Effect.runPromise(handler(call.request.formula))
        .then((response) => {
            const duration = Date.now() - startTime;

            span.setStatus({ code: SpanStatusCode.OK });
            span.setAttributes({
                "rpc.response.status": "ok",
                "rpc.response.duration_ms": duration,
            });

            logger.info("[parseFormula] request completed", {
                duration_ms: duration,
                peer: call.getPeer(),
            });

            callback(null, response);
        })
        .catch((error) => {
            const duration = Date.now() - startTime;

            span.setStatus({ code: SpanStatusCode.ERROR, message: String(error) });
            span.recordException(error);
            span.setAttributes({
                "rpc.response.status": "error",
                "rpc.response.duration_ms": duration,
                "error.type": error?.constructor?.name ?? "UnknownError",
            });

            logger.error(`[parseFormula] request failed`, {
                duration_ms: duration,
                error: String(error),
                peer: call.getPeer(),
            });

            callback(error, null);
        })
        .finally(() => span.end());
}

export function getServer() {
    return Effect.sync(() => {
        const server = new Server();

        server.addService(
            {
                parseFormula: {
                    path: "/formula_parser.FormulaParser/ParseFormula",
                    requestStream: false,
                    responseStream: false,
                    requestDeserialize,
                    requestSerialize,
                    responseDeserialize,
                    responseSerialize,
                },
            },
            { parseFormula },
        );

        return server;
    });
}

function loadSettings() {
    return settings.pipe(
        Effect.withSpan("node.loadSettings", {
            attributes: {
                "rpc.system": "grpc",
                "rpc.service": "formula_parser.FormulaParser",
                "rpc.method": "LoadSettings",
            },
        }),
        Effect.catchTag("EnvParseError", (error) => {
            return Effect.gen(function* () {
                yield* Effect.sync(() => {
                    logger.crit("[server] failed to parse env", {
                        message: error.error.message,
                        error: String(error),
                    });
                });

                return yield* Effect.fail(error);
            });
        }),
    );
}

function main() {
    return Effect.gen(function* () {
        const {
            FORMULA_PARSER_HOST,
            FORMULA_PARSER_PORT,
            DEBUG_FORMULA_PARSER,
            OTEL_SERVICE_NAME,
            OTEL_SERVICE_VERSION,
            OTEL_EXPORTER_OTLP_ENDPOINT,
            OTEL_TRACE_CONTEXT_ENABLED,
        } = yield* loadSettings();

        yield* Effect.sync(() => {
            setupTelemetry({
                serviceName: OTEL_SERVICE_NAME,
                serviceVersion: OTEL_SERVICE_VERSION,
                endpoint: OTEL_EXPORTER_OTLP_ENDPOINT,
                enabled: OTEL_TRACE_CONTEXT_ENABLED,
            });
        });

        const server = yield* getServer();

        yield* Effect.async<void, BindPortError>((resume) => {
            server.bindAsync(
                `${FORMULA_PARSER_HOST}:${FORMULA_PARSER_PORT}`,
                ServerCredentials.createInsecure(),
                (error, port) => {
                    if (error) {
                        logger.error("failed to bind server", {
                            message: error.message,
                            error: String(error),
                        });
                        resume(Effect.fail(new BindPortError({ error })));
                        return;
                    }

                    logger.info("formula-parser service running", {
                        uri: `${FORMULA_PARSER_HOST}:${port}`,
                    });
                    logger.info("debug", { value: DEBUG_FORMULA_PARSER });

                    resume(Effect.void);
                },
            );
        });
    });
}

Effect.runPromise(
    main().pipe(
        Effect.catchTag("BindPortError", (error) => {
            logger.crit("[main] port binding failed", {
                message: error.message,
                error: String(error),
            });
            return Effect.void;
        }),
    ),
);
