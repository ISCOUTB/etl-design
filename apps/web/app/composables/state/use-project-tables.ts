import type { z } from "zod";

interface State {
    tableSchemas: z.infer<typeof MongoRawSchema>[];
    selectedSchema: z.infer<typeof MongoRawSchema> | undefined;
}

export default function (projectId: MaybeRefOrGetter<ResponseProject["id"] | undefined>) {
    const errorToast = useErrorToast();

    const id = computed(() => toValue(projectId));

    const state = useState<State>(NuxtKeys.Projects.Tables.TableState(id.value), () => ({
        tableSchemas: [],
        selectedSchema: undefined,
    }));

    const { data: _schemas } = useApiFetch(() => `/schemas/search/${id.value}`, {
        method: "GET",
        key: NuxtKeys.Projects.Tables.RawSchemas(id.value),
    });

    function setSchemas(schemas: z.infer<typeof MongoRawSchema>[]) {
        state.value = { ...state.value, tableSchemas: schemas };
    }

    function setSelectedSchema(schema: z.infer<typeof MongoRawSchema> | undefined) {
        state.value = { ...state.value, selectedSchema: schema };
    }

    watch(
        _schemas,
        (schemas) => {
            if (!schemas) {
                return;
            }

            const parseResult = MongoGetSchemasResponse.safeParse(schemas);
            if (!parseResult.success) {
                errorToast.handle(ResponseCodesRecord.Server.BadPayload);
                return;
            }

            setSchemas(parseResult.data.schemas);
        },
        { immediate: true },
    );

    return {
        state,
        dispatch: {
            setSchemas,
            setSelectedSchema,
        },
    };
}
