interface State {
    loading: boolean;
    tableSchemas: MongoRaw[];
    selectedSchema: MongoRaw | undefined;
    tasks: {
        validation: unknown[];
    };
    selectedFiles: Record<MongoRaw["id"], Schemas.Schema.UploadedFile | undefined>;
}

export const [useProvideProjectTablesState, useProjectTablesState] = createInjectionState(
    (initialId: string | undefined) => {
        const { $api } = useNuxtApp();

        const state = useState<State>(NuxtKeys.Projects.Tables.TableState(initialId), () => ({
            loading: false,
            tableSchemas: [],
            selectedSchema: undefined,
            tasks: {
                validation: [],
            },
            selectedFiles: {},
        }));

        const { data: _schemas } = useApiFetch(() => `/schemas/search/${initialId}`, {
            method: "GET",
            key: NuxtKeys.Projects.Tables.RawSchemas(initialId),
        });

        function setLoading(value: boolean) {
            state.value.loading = value;
        }

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
            },
            { immediate: true },
        );

        watch(
            () => state.value.selectedSchema,
            (schema) => {
                if (!schema) {
                    return;
                }

                setLoading(true);
                Promise.all([
                    $api(`/tasks/project/${initialId}`, {
                        method: "GET",
                        query: {
                            table_name: TableUtils.getTableName(schema.import_name),
                            task: API_CONSTANTS.TASK.VALIDATION_TASK,
                        },
                    }),
                    $api(`/tasks/project/${initialId}`, {
                        method: "GET",
                        query: {
                            table_name: TableUtils.getTableName(schema.import_name),
                            task: API_CONSTANTS.TASK.INSERTION_TASK,
                        },
                    }),
                ])
                    .then((values) => console.warn(values))
                    .catch((error) => console.error(error))
                    .finally(() => setLoading(false));
            },
            { deep: true },
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
