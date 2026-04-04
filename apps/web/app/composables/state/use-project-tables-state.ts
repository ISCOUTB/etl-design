import z from "zod";

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
            },
            { immediate: true },
        );

        const _TasksResponse = z.array(ApiResponse());
        const { data: tasks, refresh } = useAsyncData(
            () =>
                NuxtKeys.Projects.Tables.Tasks(
                    initialId,
                    TableUtils.getTableName(state.value.selectedSchema?.import_name),
                ),
            async (nuxtApp, { signal }) => {
                if (!state.value.selectedSchema) {
                    return [];
                }

                try {
                    const response = await Promise.all([
                        nuxtApp.$api(`/tasks/project/${initialId}`, {
                            method: "GET",
                            query: {
                                table_name: TableUtils.getTableName(
                                    state.value.selectedSchema.import_name,
                                ),
                                task: API_CONSTANTS.TASK.VALIDATION_TASK,
                            },
                            signal,
                        }),
                        nuxtApp.$api(`/tasks/project/${initialId}`, {
                            method: "GET",
                            query: {
                                table_name: TableUtils.getTableName(
                                    state.value.selectedSchema.import_name,
                                ),
                                task: API_CONSTANTS.TASK.INSERTION_TASK,
                            },
                            signal,
                        }),
                    ]);

                    return response;
                } catch (error) {
                    errorToast.handleServer(error);
                }
            },
            {
                transform: (response) => {
                    if (!response) {
                        return [];
                    }

                    const [_validation, _insertion] = response;
                    const validation = _TasksResponse.safeParse(_validation);
                    const insertion = _TasksResponse.safeParse(_insertion);

                    if (!validation.success || !insertion.success) {
                        errorToast.handle(ResponseCodesRecord.Server.BadPayload);
                        return [];
                    }

                    return [validation.data, insertion.data];
                },
                immediate: false,
            },
        );

        watch(
            () => state.value.selectedSchema,
            (schema) => {
                if (!schema) {
                    return;
                }

                refresh();
            },
        );

        return {
            state,
            tasks,
            dispatch: {
                setSchemas,
                setUploadedFile,
                setSelectedSchema,
            },
        };
    },
);
