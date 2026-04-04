import winston from "winston";

export const logger = winston.createLogger({
    levels: {
        error: 0,
        warn: 1,
        info: 2,
        debug: 3,
    },
    format: winston.format.combine(
        winston.format.timestamp({ format: "YYYY-MM-DD HH:mm:ss,SSS" }),
        winston.format.printf(({ level, message, timestamp, ...meta }) => {
            return JSON.stringify({
                asctime: timestamp,
                levelname: level.toUpperCase(),
                name: "formula-parser",
                message,
                ...meta,
            });
        }),
    ),
    transports: [new winston.transports.Console()],
});
