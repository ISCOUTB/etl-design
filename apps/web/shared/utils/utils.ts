export function ifEmpty<T extends string | undefined | null>(payload: T, defaultValue: string) {
    if (payload && payload.length > 0) {
        return payload;
    }

    return defaultValue;
}
