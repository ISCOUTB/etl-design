import type { ColumnConfig, ResponseProject } from "#shared/utils/schemas/types";
import type { z } from "zod";
import type { Column } from "@/components/common/data-table/utils";
import { JsonSchema } from "#shared/utils/schemas/api";
import { read, utils } from "xlsx";

interface State {
    tableName: string | undefined;
    uploadedFile: Schemas.Schema.UploadedFile | undefined;
    sheetNames: string[];
    columnsConfig: Record<string, ColumnConfig>;
    warnings: { key: string; message: string }[];
}

const ROW_ID = NuxtKeys.Projects.Schemas.RowId;

export default function (projectId: MaybeRefOrGetter<ResponseProject["id"] | undefined>) {
    const config = useAppConfig();
    const { t } = useI18n();

    const id = computed(() => toValue(projectId));

    const state = useState<State>(NuxtKeys.Projects.Schemas.SchemaState(id.value), () => ({
        tableName: undefined,
        uploadedFile: undefined,
        sheetNames: [],
        columnsConfig: {},
        warnings: [],
    }));

    const isTabular = computed(() => state.value.uploadedFile?.type !== "json");

    const parsedFileContent = computedAsync<Record<string, unknown>[] | undefined>(async () => {
        try {
            if (!isTabular.value || !state.value.uploadedFile) {
                return [];
            }

            const { uploadedFile } = state.value;
            const buffer = await uploadedFile?.blob.arrayBuffer();

            if (uploadedFile?.type === "csv") {
                const text = new TextDecoder().decode(buffer);

                const wb = read(text, {
                    type: "string",
                    cellDates: true,
                    raw: true,
                });

                const firstSheet = wb.SheetNames[0];
                if (!firstSheet) {
                    return [];
                }
                const sheet = wb.Sheets[firstSheet];
                if (!sheet) {
                    return [];
                }

                const firstLine = text.split("\n")[0] ?? "";
                if (config.files.delimiter && firstLine.split(config.files.delimiter).length) {
                    setWarnings([
                        ...state.value.warnings,
                        {
                            key: "warning:invalid-delimiter",
                            message: t("projects.id.sections.schema.validation.delimiter", {
                                delimiter: t("projects.id.sections.schema.validation.comma"),
                            }),
                        },
                    ]);
                }

                state.value.sheetNames = wb.SheetNames;
                return SchemaUtils.withRowId(
                    ROW_ID,
                    utils.sheet_to_json(sheet, { defval: "", raw: true }),
                );
            }

            const wb = read(buffer, { type: "array", cellDates: true, raw: true });
            const firstSheet = wb.SheetNames[0];
            if (!firstSheet) {
                return [];
            }
            const sheet = wb.Sheets[firstSheet];
            if (!sheet) {
                return [];
            }
            state.value.sheetNames = wb.SheetNames;
            return SchemaUtils.withRowId(
                ROW_ID,
                utils.sheet_to_json(sheet, { defval: "", raw: true }),
            );
        } catch {}
    });

    const jsonSchema = computedAsync<z.infer<typeof JsonSchema> | undefined>(async () => {
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
        const keys = new Set(rows.flatMap((row) => Object.keys(row)).filter((k) => k !== ROW_ID));
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
        state.value = { ...state.value, uploadedFile: file, tableName: file?.nameWithoutExt };
    }

    function setTableName(tableName: string) {
        state.value = {
            ...state.value,
            tableName,
        };
    }

    function setWarnings(warnings: State["warnings"]) {
        const unique = Array.from(
            new Map(warnings.map((warning) => [warning.key, warning])).values(),
        );

        state.value = {
            ...state.value,
            warnings: unique,
        };
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

    function setColumnDataType(columnKey: string, dtype: z.infer<typeof DtypesEnum>) {
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
        return computed<z.infer<typeof DtypesEnum>>({
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
        },
    };
}
