import { WebSocketMessage } from "#shared/utils/websocket";

export default defineWebSocketHandler({
    async message(peer, message) {
        const logger = Logger.getInstance();

        try {
            const parsedMessage = WebSocketMessage.deserialize(message.toString());

            if (parsedMessage.error || !parsedMessage.success) {
                peer.send(WebSocketMessage.new({ key: "socket:bad-payload" }).serialize());
                return;
            }

            const redis = RedisService.getInstance();

            switch (parsedMessage.data.key) {
                case "ping": {
                    if (parsedMessage.data.userId) {
                        await redis.expire(
                            WebSocketKeys.User.Connected(parsedMessage.data.userId),
                            300,
                        );
                    }
                    peer.send(WebSocketMessage.new({ key: "pong" }).serialize());
                    break;
                }

                case "pong": {
                    peer.send(WebSocketMessage.new({ key: "ping" }).serialize());
                    break;
                }

                case "user-logged": {
                    await redis.set(
                        WebSocketKeys.User.Connected(parsedMessage.data.userId),
                        peer.id,
                        "EX",
                        300,
                    );
                    break;
                }

                default: {
                    peer.send(WebSocketMessage.new({ key: "socket:bad-payload" }).serialize());
                }
            }
        } catch (e) {
            logger.error(`socket: ${e}`);
        }
    },
});
