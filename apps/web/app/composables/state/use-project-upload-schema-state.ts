import type { Dtype, JsonSchema } from "#shared/utils/schemas/types";
import type { Column } from "@/components/common/data-table/utils";

interface State {
    tableName: string | undefined;
    insertData: boolean;
    uploadedFile: Schemas.Schema.UploadedFile | undefined;
    sheetNames: string[];
    columnsConfig: Record<string, ColumnConfig>;
}

interface SchemaError {
    key: "error:invalid-delimiter";
    message: string;
}

const ROW_ID = NuxtKeys.Projects.Schemas.RowId;

export const [useProvideProjectUploadSchemaState, useProjectUploadSchemaState] =
    createInjectionState((initialId: string | undefined) => {
        const { t } = useI18n();
        const config = useAppConfig();

        const state = useState<State>(NuxtKeys.Projects.Schemas.SchemaState(initialId), () => ({
            tableName: undefined,
            insertData: true,
            uploadedFile: undefined,
            sheetNames: [],
            columnsConfig: {},
            warnings: [],
        }));
        const errors = useState<SchemaError[]>(
            NuxtKeys.Projects.Schemas.Errors(initialId),
            () => [],
        );

        const isTabular = computed(() => state.value.uploadedFile?.type !== "json");

        const parsedFileContent = computedAsync<Record<string, unknown>[]>(async () => {
            if (!isTabular.value || !state.value.uploadedFile) {
                return [];
            }

            const { uploadedFile } = state.value;
            if (!uploadedFile) {
                return [];
            }

            const { sheetNames, parsed } = await SchemaUtils.Parser.parseContent(
                uploadedFile.blob,
                {
                    ROW_ID,
                    delimiter: config.files.delimiter,
                    type: uploadedFile.type,
                    onDelimiterError() {
                        addSchemaError({
                            key: "error:invalid-delimiter",
                            message: t("projects.id.sections.upload_schema.validation.delimiter", {
                                delimiter: t("projects.id.sections.upload_schema.validation.comma"),
                            }),
                        });
                    },
                },
            );

            state.value.sheetNames = sheetNames;
            return parsed;
        });

        const jsonSchema = computedAsync<JsonSchema | undefined>(async () => {
            if (isTabular.value || !state.value.uploadedFile) {
                return;
            }

            const fileContent = await state.value.uploadedFile.blob.text();
            const parseResult = JsonSchema.safeParse(JSON.parse(fileContent));
            if (!parseResult.success) {
                return;
            }

            return parseResult.data;
        });

        const columns = computed<Column<Record<string, unknown>>[]>(() => {
            if (!parsedFileContent.value) {
                return [];
            }

            return toColumns(parsedFileContent.value, ROW_ID);
        });

        const sampleValueByColumn = computed<Record<string, unknown>>(() => {
            if (!parsedFileContent.value) {
                return {};
            }

            const rows = parsedFileContent.value;
            if (!rows?.length) {
                return {};
            }
            const keys = new Set(
                rows.flatMap((row) => Object.keys(row)).filter((k) => k !== ROW_ID),
            );
            return Object.fromEntries(
                [...keys].map((key) => [
                    key,
                    rows.map((row) => row[key]).find((v) => !SchemaUtils.isBlankCell(v)) ?? "",
                ]),
            );
        });

        watch(
            columns,
            (nextColumns) => {
                if (!nextColumns.length) {
                    return;
                }

                state.value.columnsConfig = Object.fromEntries(
                    nextColumns.map(({ key }) => {
                        const columnKey = String(key);
                        const previous = state.value.columnsConfig[columnKey];

                        return [columnKey, previous ?? SchemaUtils.getColumnConfig()];
                    }),
                );
            },
            { immediate: true },
        );

        const selectedDataTypes = computed(() =>
            Object.fromEntries(
                Object.entries(state.value.columnsConfig).map(([columnKey, config]) => [
                    columnKey,
                    config.dtype,
                ]),
            ),
        );

        function setUploadedFile(file: Schemas.Schema.UploadedFile | undefined) {
            if (!file) {
                clearSchemaErrors();
            }
            state.value.uploadedFile = file;
            state.value.tableName = file?.nameWithoutExt;
        }

        function setTableName(tableName: string) {
            state.value.tableName = tableName;
        }

        function setInsertData(value: boolean) {
            state.value.insertData = value;
        }

        function addSchemaError(error: SchemaError) {
            if (!errors.value.some((e) => e.key === error.key)) {
                errors.value.push(error);
            }
        }

        function removeSchemaError(key: SchemaError["key"]) {
            errors.value = errors.value.filter((error) => error.key !== key);
        }

        function clearSchemaErrors() {
            errors.value.length = 0;
        }

        function setColumnConfig(columnKey: string, config: ColumnConfig) {
            state.value.columnsConfig[columnKey] = config;
        }

        function patchColumnConfig(columnKey: string, patch: Partial<ColumnConfig>) {
            const current = state.value.columnsConfig[columnKey] ?? SchemaUtils.getColumnConfig();
            setColumnConfig(columnKey, { ...current, ...patch } as ColumnConfig);
        }

        function setColumnDataType(columnKey: string, dtype: Dtype) {
            const current = state.value.columnsConfig[columnKey];
            setColumnConfig(columnKey, SchemaUtils.getColumnConfig(dtype, current));
        }

        function setColumnOptional(columnKey: string, optional: boolean) {
            patchColumnConfig(columnKey, { optional });
        }

        function setColumnUnique(columnKey: string, unique: boolean) {
            patchColumnConfig(columnKey, { unique });
        }

        function setColumnPrimaryKey(columnKey: string, primary_key: boolean) {
            patchColumnConfig(columnKey, { primary_key });
        }

        function getColumnDataTypeModel(columnKey: string) {
            return computed<Dtype>({
                get: () => state.value.columnsConfig[columnKey]?.dtype ?? "string",
                set: (value) => setColumnDataType(columnKey, value),
            });
        }

        function getColumnConfigModel(columnKey: string) {
            return computed<ColumnConfig>({
                get: () => state.value.columnsConfig[columnKey] ?? SchemaUtils.getColumnConfig(),
                set: (value) => setColumnConfig(columnKey, value),
            });
        }

        function toColumns(
            data: Record<string, unknown>[] | undefined,
            rowId: string,
        ): Column<Record<string, unknown>>[] {
            const row = data?.[0];
            if (!row) {
                return [];
            }

            return Object.keys(row)
                .filter((key) => key !== rowId)
                .map((key) => ({ key, label: key }));
        }

        return {
            state,
            errors,
            computed: {
                isTabular,
                parsedFileContent,
                columns,
                sampleValueByColumn,
                selectedDataTypes,
                jsonSchema,
            },
            dispatch: {
                setUploadedFile,
                setColumnDataType,
                setTableName,
                setInsertData,
                setColumnConfig,
                setColumnUnique,
                setColumnOptional,
                setColumnPrimaryKey,
                patchColumnConfig,
                getColumnDataTypeModel,
                getColumnConfigModel,
                addSchemaError,
                removeSchemaError,
                clearSchemaErrors,
                toColumns,
            },
        };
    });
