import type { UserRole } from "#shared/utils/schemas/auth";
import type { DefaultSession } from "next-auth";
import type { z } from "zod";

declare module "next-auth" {
    interface User {
        id: string;
        name: string;
        email: string;
        role: z.infer<typeof UserRole>;
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
