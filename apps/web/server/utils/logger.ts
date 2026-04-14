import { createConsola } from "consola";

export class Logger {
    @Singleton()
    static getInstance() {
        if (import.meta.dev) {
            return createConsola({ level: 4 });
        }

        return createConsola({ level: -999 });
    }
}
