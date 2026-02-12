import { useWebSocket } from "@vueuse/core";

export default defineNuxtPlugin({
    name: "websocket",
    parallel: true,
    setup() {
        const config = useAppConfig();
        const socket = useWebSocket<WebSocket.Message>(config.handlers.websocket.url, {
            autoReconnect: true,
        });

        return {
            provide: {
                socket,
            },
        };
    },
});
