interface State {
    tableSchemas: MongoRaw[];
    selectedSchema: MongoRaw | undefined;
    selectedFiles: Record<MongoRaw["id"], Schemas.Schema.UploadedFile | undefined>;
}

export const [useProvideProjectTablesState, useProjectTablesState] = createInjectionState(
    (initialId: string | undefined) => {
        const state = useState<State>(NuxtKeys.Projects.Tables.TableState(initialId), () => ({
            tableSchemas: [],
            selectedSchema: undefined,
            selectedFiles: {},
        }));

        const { data: _schemas } = useApiFetch(() => `/schemas/search/${initialId}`, {
            method: "GET",
            key: NuxtKeys.Projects.Tables.RawSchemas(initialId),
        });

        function setSchemas(schemas: MongoRaw[]) {
            state.value.tableSchemas = schemas;
        }

        function setSelectedSchema(schema: MongoRaw | undefined) {
            state.value.selectedSchema = schema;
        }

        function setUploadedFile(
            tableId: MongoRaw["id"],
            file: Schemas.Schema.UploadedFile | undefined,
        ) {
            state.value.selectedFiles[tableId] = file;
        }

        const errorToast = useErrorToast();
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

                const currentSelectedId = state.value.selectedSchema?.id;
                if (currentSelectedId) {
                    const updatedSelected = parseResult.data.schemas.find(
                        (schema) => schema.id === currentSelectedId,
                    );

                    setSelectedSchema(updatedSelected);
                }
            },
            { immediate: true },
        );

        return {
            state,
            dispatch: {
                setSchemas,
                setUploadedFile,
                setSelectedSchema,
            },
        };
    },
);
