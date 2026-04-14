import { createConsola } from "consola";

export default defineNuxtPlugin({
    name: "logger",
    setup() {
        if (import.meta.dev) {
            const logger = createConsola({ level: 4 });

            return {
                provide: {
                    logger,
                },
            };
        }

        const logger = createConsola({ level: -999 });
        return {
            provide: {
                logger,
            },
        };
    },
});
