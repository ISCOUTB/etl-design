export default defineAppConfig({
    handlers: {
        websocket: {
            url: "/_websocket",
            pingInterval: 1 * 1000 * 60,
            pongTimeout: 1000,
        },
    },
    auth: {
        validation: {
            minPasswordLength: 8,
            maxPasswordLength: 50,
        },
    },
});
