import process from "node:process";
import { Effect } from "effect";
import { z } from "zod";
import { EnvParseError } from "@/core/errors";

export type Settings = z.infer<typeof EnvSchema>;

const firstDefinedEnv = (keys: string[], fallback: string) => {
    for (const key of keys) {
        const value = process.env[key];

        if (value !== undefined && value !== "") {
            return value;
        }
    }

    return fallback;
};

const stringEnv = (keys: string[], fallback: string) =>
    z.preprocess(() => firstDefinedEnv(keys, fallback), z.string());

const numberEnv = (keys: string[], fallback: number) =>
    z.preprocess(() => firstDefinedEnv(keys, String(fallback)), z.coerce.number());

const booleanEnv = (keys: string[], fallback: boolean) =>
    z.preprocess(() => {
        for (const key of keys) {
            const value = process.env[key];

            if (value === undefined || value === "") {
                continue;
            }

            return ["true", "1", "yes", "on"].includes(value.toLowerCase());
        }

        return fallback;
    }, z.boolean());

const EnvSchema = z.object({
    FORMULA_PARSER_HOST: stringEnv(["FORMULA_PARSER_HOST"], "0.0.0.0"),
    FORMULA_PARSER_PORT: numberEnv(["FORMULA_PARSER_PORT"], 50052).pipe(
        z.number().min(1).max(65535),
    ),
    DEBUG_FORMULA_PARSER: booleanEnv(["DEBUG_FORMULA_PARSER", "FORMULA_PARSER_DEBUG"], false),
    ENABLE_PROMETHEUS_METRICS: booleanEnv(["ENABLE_PROMETHEUS_METRICS"], false),
    PROMETHEUS_METRICS_PORT: numberEnv(["PROMETHEUS_METRICS_PORT"], 9090).pipe(
        z.number().min(1).max(65535),
    ),
    FORMULA_TRACE_CONTEXT_ENABLED: booleanEnv(
        ["FORMULA_TRACE_CONTEXT_ENABLED", "OTEL_TRACE_CONTEXT_ENABLED"],
        true,
    ),
    FORMULA_TRACE_CONTEXT_LOG_HEADERS: booleanEnv(["FORMULA_TRACE_CONTEXT_LOG_HEADERS"], false),
    OTEL_TRACING_ENABLED: booleanEnv(["OTEL_TRACING_ENABLED"], true),
    OTEL_SERVICE_NAME: stringEnv(["OTEL_SERVICE_NAME"], "formula-parser"),
    OTEL_SERVICE_VERSION: stringEnv(["OTEL_SERVICE_VERSION"], "1.0.0"),
    OTEL_EXPORTER_OTLP_ENDPOINT: stringEnv(["OTEL_EXPORTER_OTLP_ENDPOINT"], "http://localhost:4318"),
});

export const settings: Effect.Effect<Settings, EnvParseError> = Effect.try({
    try: () => EnvSchema.parse(process.env),
    catch: (error) => new EnvParseError({ error: error as z.ZodError }),
});
