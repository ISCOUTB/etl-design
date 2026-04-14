import { getServerSession } from "#auth";
import { ModelResponse } from "#shared/utils/schemas/model";
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
    const completion = await $fetch(runtimeConfig.keys.MODEL_ENDPOINT, {
        method: "POST",
        headers: {
            Authorization: `Bearer ollama`,
            "Content-Type": "application/json",
        },
        body: {
            model: "gemma4",
            system: PROMPTS.QUERY_BUILDER_GENERATE.SYSTEM,
            prompt: PROMPTS.interpolate(PROMPTS.QUERY_BUILDER_GENERATE.USER, {
                userMessage,
                schemas,
            }),
            stream: false,
        },
    });

    const parsed = ModelResponse.safeParse(completion);
    if (!parsed.success) {
        throw createError({
            status: 500,
            statusMessage: ResponseCodesRecord.Server.BadPayload,
        });
    }

    return {
        response: parsed.data.response,
    };
});
