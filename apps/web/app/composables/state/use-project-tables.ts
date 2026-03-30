import type { z } from "zod";

interface State {
    tableSchemas: z.infer<typeof MongoRawSchema>[];
    selectedSchema: z.infer<typeof MongoRawSchema> | undefined;
    selectedFiles: Record<MongoRaw["id"], Schemas.Schema.UploadedFile | undefined>;
}

export default function (projectId: MaybeRefOrGetter<ResponseProject["id"] | undefined>) {
    const errorToast = useErrorToast();

    const id = computed(() => toValue(projectId));

    const state = useState<State>(NuxtKeys.Projects.Tables.TableState(id.value), () => ({
        tableSchemas: [],
        selectedSchema: undefined,
        selectedFiles: {},
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

    function setUploadedFile(
        tableId: MongoRaw["id"],
        file: Schemas.Schema.UploadedFile | undefined,
    ) {
        state.value = {
            ...state.value,
            selectedFiles: { ...state.value.selectedFiles, [tableId]: file },
        };
    }

    watch(
        _schemas,
        (schemas) => {
            if (!schemas) {
                return;
            }

            const parseResult = MongoGetSchemasResponse.safeParse(schemas);
            if (!parseResult.success) {
                console.warn(parseResult.error);
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
            setUploadedFile,
        },
    };
}
