import type { WebSocketMessageSchema } from "#shared/utils/websocket";
import type { z } from "zod";

declare global {
    namespace WebSocket {
        type Message = z.infer<typeof WebSocketMessageSchema>;
    }
}
