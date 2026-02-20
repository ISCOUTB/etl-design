export const ResponseCodesRecord = {
    WebSocket: {
        BadPayload: "socket:bad-payload",
    },
    Server: {
        UnAuthorized: "server:unauthorized",
        Auth: {
            SignIn: {
                BadPayload: "server:auth:sign-in:bad-payload",
                InvalidCredentials: "error:invalid-credentials",
                UserNotFound: "",
            },
        },
    },
} as const;
