import type { H3Event } from "#imports";
import type { z } from "zod";

export const UtilsRepository = {
    async readBody<T extends z.ZodType>(event: H3Event, schema: T): Promise<z.infer<T>> {
        const body = await readBody(event);
        const parsed = schema.safeParse(body);
        if (!parsed.success) {
            throw createError({
                status: 400,
                statusText: ResponseCodesRecord.Server.BadPayload,
            });
        }
        return parsed.data;
    },
};
