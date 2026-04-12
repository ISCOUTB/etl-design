import { getServerSession } from "#auth";
import { z } from "zod";

const BodySchema = z.object({
    projectId: z.string(),
    userMessage: z.string(),
});

export default defineWrappedResponseHandler(async (event) => {
    const session = await getServerSession(event);
    if (!session) {
        throw createError({ status: 401, statusMessage: ResponseCodesRecord.Server.UnAuthorized });
    }

    const { projectId, userMessage } = await UtilsRepository.readBody(event, BodySchema);
    const tables = await ProjectRepository.getTables(session, projectId);

    const schemas = tables.schemas.map((schema) => ({
        import_name: schema.import_name,
        active_schema: schema.active_schema,
    }));

    const runtimeConfig = useRuntimeConfig(event);
    const completion = await $fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${runtimeConfig.keys.MODEL_API_KEY}`,
            "Content-Type": "application/json",
        },
        body: {
            model: "gpt-4o-mini",
            messages: [
                {
                    role: "system",
                    content: PROMPTS.QUERY_BUILDER_GENERATE.SYSTEM,
                },
                {
                    role: "user",
                    content: PROMPTS.interpolate(PROMPTS.QUERY_BUILDER_GENERATE.USER, {
                        userMessage,
                        schemas,
                    }),
                },
            ],
        },
    });

    console.warn(completion);
});
