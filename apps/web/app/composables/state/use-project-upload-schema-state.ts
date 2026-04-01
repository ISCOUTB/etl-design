import type { Dtype, JsonSchema } from "#shared/utils/schemas/types";
import type { Column } from "@/components/common/data-table/utils";

interface State {
    tableName: string | undefined;
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
                            message: t("projects.id.sections.schema.validation.delimiter", {
                                delimiter: t("projects.id.sections.schema.validation.comma"),
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
                console.warn("Invalid JSON schema format");
                return;
            }

            return parseResult.data;
        });

        const columns = computed<Column<Record<string, unknown>>[]>(() => {
            if (!parsedFileContent.value) {
                return [];
            }

            const firstRow = parsedFileContent.value?.[0];
            if (!firstRow) {
                return [];
            }
            return Object.keys(firstRow)
                .filter((key) => key !== ROW_ID)
                .map((key) => ({ key, label: key }));
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
            state.value = { ...state.value, uploadedFile: file, tableName: file?.nameWithoutExt };
        }

        function setTableName(tableName: string) {
            state.value = {
                ...state.value,
                tableName,
            };
        }

        function addSchemaError(error: SchemaError) {
            const already = errors.value.some((e) => e.key === error.key);
            if (already) {
                return;
            }
            errors.value = [...errors.value, error];
        }

        function removeSchemaError(key: SchemaError["key"]) {
            errors.value = errors.value.filter((error) => error.key !== key);
        }

        function clearSchemaErrors() {
            errors.value = [];
        }

        function setColumnConfig(columnKey: string, config: ColumnConfig) {
            state.value.columnsConfig = {
                ...state.value.columnsConfig,
                [columnKey]: config,
            };
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
            },
        };
    });
