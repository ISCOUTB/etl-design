import type { sendUnaryData, Server, ServerUnaryCall } from "@grpc/grpc-js";
import type { Settings } from "@/core";
import process from "node:process";
import { Server as GrpcServer, ServerCredentials, status } from "@grpc/grpc-js";
import { context, trace } from "@opentelemetry/api";
import { formula_parser } from "@sloth/packages-proto-utils-js";
import { Effect } from "effect";
import { settings } from "@/core";
import { handler } from "@/handlers/handler";
import { logger } from "@/utils/logger";
import {
    getGrpcMetricBaseLabels,
    incrementGrpcServerHandled,
    incrementGrpcServerMsgReceived,
    incrementGrpcServerMsgSent,
    incrementGrpcServerStarted,
    startGrpcServerHandledLatencyTimer,
    startGrpcServerHandlingTimer,
    startPrometheusMetricsServer,
} from "@/utils/metrics";
import { configureOtelTracing, getGrpcTracer, shutdownOtelTracing } from "@/utils/telemetry";
import { extractTraceContextFromCall } from "@/utils/trace-context";

const SERVICE_NAME = "formula-parser";
const METHOD_PATH = "/formula_parser.FormulaParser/ParseFormula";

interface TraceLogContext {
    trace_id?: string;
    span_id?: string;
    trace_flags?: string;
}

function getStatusName(code: status): string {
    return status[code] ?? "UNKNOWN";
}

function getTraceContextEnabled(): boolean {
    const rawValue =
        // eslint-disable-next-line dot-notation
        process.env["FORMULA_TRACE_CONTEXT_ENABLED"] ?? process.env["OTEL_TRACE_CONTEXT_ENABLED"];

    if (rawValue === undefined || rawValue === "") {
        return true;
    }

    return ["true", "1", "yes", "on"].includes(rawValue.toLowerCase());
}

function getTraceLogContext(): TraceLogContext {
    const activeSpan = trace.getActiveSpan();
    const spanContext = activeSpan?.spanContext();

    if (!spanContext) {
        return {};
    }

    return {
        trace_id: spanContext.traceId,
        span_id: spanContext.spanId,
        trace_flags: spanContext.traceFlags.toString(16).padStart(2, "0"),
    };
}

function toGrpcError(error: unknown): Error {
    if (error instanceof Error) {
        return error;
    }

    return new Error(String(error));
}

export function getServer(): Effect.Effect<Server> {
    return Effect.succeed(new GrpcServer());
}

export function parseFormula(
    call: ServerUnaryCall<
        formula_parser.FormulaParserRequest,
        formula_parser.FormulaParserResponse
    >,
    callback: sendUnaryData<formula_parser.FormulaParserResponse>,
): void {
    const grpcLabels = getGrpcMetricBaseLabels(METHOD_PATH);
    incrementGrpcServerStarted(grpcLabels);
    incrementGrpcServerMsgReceived(grpcLabels);

    const stopHandlingTimer = startGrpcServerHandlingTimer(grpcLabels);
    let grpcStatus: status = status.OK;

    const traceContext = getTraceContextEnabled()
        ? extractTraceContextFromCall(call)
        : context.active();
    const tracer = getGrpcTracer();

    context.with(traceContext, async () => {
        await tracer.startActiveSpan("grpc.ParseFormula", async (span) => {
            try {
                const response = await Effect.runPromise(
                    handler(call.request.formula ?? "", getTraceLogContext()),
                );

                incrementGrpcServerMsgSent(grpcLabels);
                incrementGrpcServerHandled({ ...grpcLabels, grpc_code: "OK" });

                callback(null, response);
            } catch (error) {
                grpcStatus = status.INTERNAL;
                incrementGrpcServerHandled({ ...grpcLabels, grpc_code: getStatusName(grpcStatus) });

                const grpcError = toGrpcError(error);
                logger.error("[SERVER] ParseFormula request failed", {
                    module: "server",
                    funcName: "parseFormula",
                    error: grpcError.message,
                });

                callback(grpcError, null);
            } finally {
                stopHandlingTimer();
                startGrpcServerHandledLatencyTimer(grpcLabels)({
                    grpc_code: getStatusName(grpcStatus),
                });
                span.end();
            }
        });
    });
}

async function configureServerRuntime(config: Settings): Promise<void> {
    await configureOtelTracing({
        enabled: config.OTEL_TRACING_ENABLED,
        serviceName: config.OTEL_SERVICE_NAME,
        serviceVersion: config.OTEL_SERVICE_VERSION,
        environment: config.DEBUG_FORMULA_PARSER ? "debug" : "production",
        endpoint: config.OTEL_EXPORTER_OTLP_ENDPOINT,
        debug: config.DEBUG_FORMULA_PARSER,
    });

    if (config.ENABLE_PROMETHEUS_METRICS) {
        startPrometheusMetricsServer(config.PROMETHEUS_METRICS_PORT);
    }
}

export async function serve(): Promise<void> {
    const config = await Effect.runPromise(settings);

    await configureServerRuntime(config);

    const server = new GrpcServer();

    server.addService(formula_parser.UnimplementedFormulaParserService.definition, {
        ParseFormula: parseFormula,
    });

    const bindAddress = `${config.FORMULA_PARSER_HOST}:${config.FORMULA_PARSER_PORT}`;

    await new Promise<void>((resolve, reject) => {
        server.bindAsync(bindAddress, ServerCredentials.createInsecure(), (error) => {
            if (error) {
                reject(error);
                return;
            }
            resolve();
        });
    });

    logger.info("[SERVER] Formula Parser server started", {
        module: "server",
        funcName: "serve",
        host: config.FORMULA_PARSER_HOST,
        port: config.FORMULA_PARSER_PORT,
        service_name: SERVICE_NAME,
    });

    const shutdown = async (signal: NodeJS.Signals) => {
        logger.info("[SERVER] Shutdown signal received", {
            module: "server",
            funcName: "serve",
            signal,
        });

        await new Promise<void>((resolve) => {
            server.tryShutdown(() => resolve());
        });

        await shutdownOtelTracing();
    };

    process.once("SIGINT", () => {
        void shutdown("SIGINT");
    });
    process.once("SIGTERM", () => {
        void shutdown("SIGTERM");
    });
}

export async function main(): Promise<void> {
    try {
        await serve();
    } catch (error) {
        const grpcError = toGrpcError(error);
        logger.error("[MAIN] Fatal error while starting Formula Parser", {
            module: "server",
            funcName: "main",
            error: grpcError.message,
        });

        process.exitCode = 1;
    }
}

void (async () => {
    await main();
})();
