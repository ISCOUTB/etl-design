export function ifEmpty<T extends string | undefined | null>(payload: T, defaultValue: string) {
    if (payload && payload.length > 0) {
        return payload;
    }

    return defaultValue;
}

export const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function getFileExtension(name: string): string {
    const ext = name.split(".").pop()?.toLowerCase();
    return ext ?? "";
}

export function normalizeMime(mime: string | undefined): string {
    return (mime ?? "").toLowerCase().trim();
}
