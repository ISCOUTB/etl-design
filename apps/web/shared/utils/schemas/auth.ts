import { z } from "zod";

export const UserRole = z.enum(["user", "sudo"]);
export const UserStatus = z.enum(["active", "inactive"]);

export const UserResponse = z.object({
    id: z.string(),
    name: z.string(),
    email: z.email(),
    role: UserRole,
    status: UserStatus,
    created_at: z.iso.datetime({ offset: true }),
    updated_at: z.iso.datetime({ offset: true }),
});
