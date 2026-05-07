import type { Session } from "next-auth";

export class ApiClient {
    static getInstance(session: Session | null = null) {
        const config = useRuntimeConfig();
        return $fetch.create({
            baseURL: config.public.API_BASE,
            onRequest({ options }) {
                const accessToken = session?.accessToken;
                if (accessToken) {
                    options.headers.set("Authorization", `Bearer ${accessToken}`);
                }
            },
        });
    }
}
