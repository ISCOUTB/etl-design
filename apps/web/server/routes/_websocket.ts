import { $makeWebSocketMessage, WebSocketMessageSchema } from "#shared/utils/websocket";

export default defineWebSocketHandler({
    message(peer, message) {
        const parsedMessage = WebSocketMessageSchema.safeParse(JSON.parse(message.toString()));

        if (parsedMessage.error || !parsedMessage.success) {
            peer.send($makeWebSocketMessage({ key: "socket:bad-payload" }).serialize());
            return;
        }

        switch (parsedMessage.data.key) {
            case "ping":
            case "pong": {
                peer.send($makeWebSocketMessage({ key: "pong" }).serialize());
                break;
            }

            case "user-logged": {
                /**
                 * Manage user logged here
                 * Should send and http notification to backend to be
                 * registered
                 */

                break;
            }

            default: {
                peer.send($makeWebSocketMessage({ key: "socket:bad-payload" }).serialize());
            }
        }
    },
});
