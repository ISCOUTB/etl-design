import { z } from "zod";

export const ModelResponse = z.object({
    model: z.string(),
    response: z.string(),
    done: z.boolean(),
    done_reason: z.string(),
});
