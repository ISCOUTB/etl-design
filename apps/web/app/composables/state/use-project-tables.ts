import type { z } from "zod";

export default function (projectId: MaybeRefOrGetter<string | undefined>) {
    const errorToast = useErrorToast();

    const id = computed(() => toValue(projectId));

    const { data: _schemas } = useApiFetch(`/schemas/search/${id.value}`, {
        method: "GET",
    });
    const tableSchemas = computed<z.infer<typeof MongoGetSchemasResponse>>(() => {
        const parseResult = MongoGetSchemasResponse.safeParse(_schemas.value);
        if (!parseResult.success) {
            errorToast.handle(ResponseCodesRecord.Server.BadPayload);
            return { schemas: [] };
        }

        return parseResult.data;
    });

    return {
        state: {
            tableSchemas,
        },
    };
}
