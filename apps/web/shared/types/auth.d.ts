import type { DefaultSession } from "next-auth";

declare module "next-auth" {
    interface User {
        id: string;
        name: string;
        email: string;
    }

    interface Session {
        user: User & DefaultSession["user"];
        accessToken: string;
    }
}

declare module "next-auth/jwt" {
    interface JWT {
        id?: string;
        email?: string;
        name?: string;
    }
}
