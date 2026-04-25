export function extractAvatarFallback(name: string | undefined): string {
    if (!name) {
        return "User";
    }

    return name
        .split(" ")
        .map((slice) => slice.charAt(0))
        .slice(0, 2)
        .join("");
}
