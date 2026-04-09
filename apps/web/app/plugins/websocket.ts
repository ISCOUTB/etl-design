import { $makeWebSocketMessage } from "#shared/utils/websocket";

export default defineNuxtPlugin({
    name: "websocket",
    parallel: true,
    setup() {
        const auth = useAuth();
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

        watch(
            [socket.status, auth.status],
            ([socketStatus, authStatus]) => {
                if (
                    socketStatus === "OPEN" &&
                    authStatus === "authenticated" &&
                    auth.data.value?.user
                ) {
                    socket.send(
                        $makeWebSocketMessage({
                            key: "user-logged",
                            userId: auth.data.value.user.id,
                            accessToken: auth.data.value.accessToken,
                        }).serialize(),
                    );
                }
            },
            { immediate: true },
        );

        return {
            provide: {
                socket,
            },
        };
    },
});
