import { z } from "zod";

export const ApiErrorSchema = z.looseObject({
    error: z.string(),
    message: z.string(),
});

const PaginatedResponseObject = z.object({
    total: z.coerce.number().int(),
    page: z.coerce.number().int(),
    limit: z.coerce.number().int(),
    total_pages: z.coerce.number().int(),
    has_prev: z.boolean(),
    has_next: z.boolean(),
});

export function PaginatedResponse(object: z.ZodObject) {
    return PaginatedResponseObject.extend({ items: z.array(object) });
}

export const BaseProjectSchema = z.object({
    name: z.string().min(1),
    description: z.string().nullable().default(null),
    provider: z.string().nullable().default(null),
    db_host: z.string().nullable().default(null),
    db_port: z.number().int().nullable().default(null),
    db_user: z.string().nullable().default(null),
    db_password: z.string().nullable().default(null),
    db_name: z.string().nullable().default(null),
    db_params: z.string().nullable().default(null),
});

export const ResponseProjectSchema = z
    .object({
        id: z.string(),
        created_at: z.iso.datetime({ offset: true }),
        updated_at: z.iso.datetime({ offset: true }),
    })
    .extend(BaseProjectSchema.shape);
