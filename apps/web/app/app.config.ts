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
    composables: {
        useModal: {
            maxStorageLength: 3,
        },
    },
    pagination: {
        defaultPageSize: 10,
    },
    files: {
        supportedFormats: ["json", "xlsx", "xls", "csv"],
        supportedMimeTypes: [
            "application/json",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "text/csv",
        ],
    },
});
