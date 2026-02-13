import { $makeWebSocketMessage } from "#shared/utils/websocket";

export default defineNuxtPlugin({
    name: "websocket",
    parallel: true,
    setup() {
        const config = useAppConfig();
        const socket = useWebSocket<WebSocket.Message>(config.handlers.websocket.url, {
            autoReconnect: true,
            heartbeat: {
                message: $makeWebSocketMessage({ key: "ping" }).serialize(),
                pongTimeout: config.handlers.websocket.pongTimeout,
                scheduler: (callback) =>
                    useIntervalFn(callback, config.handlers.websocket.pingInterval),
            },
        });

        return {
            provide: {
                socket,
            },
        };
    },
});
