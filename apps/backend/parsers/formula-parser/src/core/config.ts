import process from "node:process";
import { Effect } from "effect";
import { z } from "zod";
import { EnvParseError } from "@/core/errors";

export type Settings = z.infer<typeof EnvSchema>;

const EnvSchema = z.object({
    FORMULA_PARSER_HOST: z.string().default("localhost"),
    FORMULA_PARSER_PORT: z.coerce.number().min(1).max(65535).default(50052),
    DEBUG_FORMULA_PARSER: z
        .string()
        .refine((value) => ["true", "false"].includes(value.toLowerCase()))
        .transform((value) => value.toLowerCase() === "true")
        .default(false),

    OTEL_SERVICE_NAME: z.string().default("formula-parser"),
    OTEL_SERVICE_VERSION: z.string().default("1.0.0"),
    OTEL_EXPORTER_OTLP_ENDPOINT: z.string().default("http://localhost:4318"),
    OTEL_TRACE_CONTEXT_ENABLED: z
        .string()
        .transform((value) => value.toLowerCase() === "true")
        .default(true),
});

export const settings: Effect.Effect<Settings, EnvParseError> = Effect.suspend(() => {
    const result = EnvSchema.safeParse(process.env);

    if (!result.success) {
        return Effect.fail(new EnvParseError({ error: result.error }));
    }

    return Effect.succeed(result.data);
});
