interface Params {
    user?: string | null;
    password?: string | null;
    host: string;
    port: number | string;
    database?: string | null;
    params?: string | null;
}

export function buildPgConnectionString(config: Params) {
    let userInfo = "";
    if (config.user) {
        userInfo = config.user;
        if (config.password) {
            userInfo += `:${config.password}`;
        }
        userInfo += "@";
    }

    let dbInfo = "";
    if (config.database) {
        dbInfo = `/${config.database}`;
    }

    let paramInfo = "";
    if (config.params) {
        paramInfo = `?${config.params}`;
    }

    return `postgresql://${userInfo}${config.host}:${config.port}${dbInfo}${paramInfo}`;
}
