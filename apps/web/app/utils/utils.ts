export function extractAvatarFallback(name: string | undefined): string {
    if (!name) {
        return "User";
    }

    return name
        .split(" ")
        .map((slice) => slice.charAt(0).toUpperCase())
        .slice(0, 2)
        .join("");
}
