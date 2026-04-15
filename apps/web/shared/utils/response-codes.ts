export const ResponseCodesRecord = {
    WebSocket: {
        BadPayload: "socket:bad-payload",
    },
    Server: {
        BadPayload: "server:bad-payload",
        UnAuthorized: "error:unauthorized",
        UnAutenticated: "error:unauthenticated",
        UnknownError: "server:unknown-error",
        Auth: {
            SignIn: {
                BadPayload: "server:auth:sign-in:bad-payload",
                InvalidCredentials: "error:invalid-credentials",
                UserNotFound: "error:user-not-found",
            },
            SignUp: {
                EmailAlreadyInUse: "error:user-already-exists",
            },
            Validation: {
                InvalidUserData: "error:invalid-user-data",
                InvalidEmailFormat: "error:invalid-email-format",
            },
            TokenExpired: "error:token-expired",
            UnAuthenticated: "error:unauthenticated",
        },
        Project: {
            NotFound: "error:project-not-found",
            CouldNotDelete: "error:could-not-delete-project",
            Schema: {
                NoFileProvided: "error:project:schema:no-file-provided",
            },
            MissingConnectionParams: "error:project:connection-invalid",
            InvalidParams: "error:projectr:invalid-params",
            CouldNotConnect: "error:project:",
            QueryBuilder: {
                GenerateError: "error:project:query-builder:generate-error",
                InvalidColumns: "error:project:query-builder:invalid-columns",
                InvalidOrderBY: "error:project:query-builder:invalid-order-by",
            },
        },
    },
} as const;
