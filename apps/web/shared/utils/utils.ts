export function ifEmpty<T extends string | undefined | null>(payload: T, defaultValue: string) {
    if (payload && payload.length > 0) {
        return payload;
    }

    return defaultValue;
}

export function deepParseJSON(value: unknown): unknown {
    if (typeof value === "string") {
        try {
            const parsed = JSON.parse(value);
            return deepParseJSON(parsed);
        } catch {
            return value;
        }
    }

    if (Array.isArray(value)) {
        return value.map(deepParseJSON);
    }

    if (typeof value === "object" && value !== null) {
        return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, deepParseJSON(v)]));
    }

    return value;
}

export const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
