import type { ServerUnaryCall } from "@grpc/grpc-js";
import { context, propagation, type Context } from "@opentelemetry/api";

const TRACE_HEADER_KEYS = new Set(["traceparent", "tracestate", "baggage"]);

export function extractTraceHeadersFromCall(
    call: ServerUnaryCall<unknown, unknown>,
): Record<string, string> {
    const headers: Record<string, string> = {};
    const metadata = call.metadata?.getMap?.() ?? {};

    for (const [key, value] of Object.entries(metadata)) {
        const normalizedKey = key.toLowerCase();

        if (!TRACE_HEADER_KEYS.has(normalizedKey)) {
            continue;
        }

        if (typeof value === "string") {
            headers[normalizedKey] = value;
        }
    }

    return headers;
}

export function extractTraceContext(headers: Record<string, string>): Context {
    return propagation.extract(context.active(), headers);
}

export function extractTraceContextFromCall(call: ServerUnaryCall<unknown, unknown>): Context {
    return extractTraceContext(extractTraceHeadersFromCall(call));
}
