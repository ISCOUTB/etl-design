import { z } from "zod";

export const ApiErrorSchema = z.looseObject({
    error: z.string(),
    message: z.string(),
});
