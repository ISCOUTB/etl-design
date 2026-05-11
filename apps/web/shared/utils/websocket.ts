import { ResponseCodesRecord } from "#shared/utils/response-codes";
import { z } from "zod";

function $message<T extends string>(key: T): z.ZodObject<{ key: z.ZodLiteral<T> }>;
function $message<T extends string, S extends z.ZodRawShape>(
    key: T,
    schema: S,
): z.ZodObject<
    {
        key: z.ZodLiteral<T>;
    } & S
>;
function $message<T extends string>(key: T, schema?: z.ZodRawShape) {
    if (schema) {
        return z.object({ key: z.literal(key) }).extend(schema);
    }

    return z.object({ key: z.literal(key) });
}

export function $makeWebSocketMessage<M extends WebSocket.Message>(message: M) {
    return {
        data: message,
        serialize: () => JSON.stringify(message),
    };
}

export const WebSocketMessageSchema = z.discriminatedUnion("key", [
    $message("ping", { userId: z.string().optional() }),
    $message("pong"),
    $message(ResponseCodesRecord.WebSocket.BadPayload),
    $message("user-logged", { userId: z.string(), accessToken: z.string() }),
]);
