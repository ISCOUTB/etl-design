import type { z } from "zod";
import type { Column } from "@/components/common/data-table/utils";
import { read, utils } from "xlsx";

type ColumnConfig = z.infer<typeof SpreadsheetDtypesSchema>;
type Dtype = z.infer<typeof DtypesEnum>;

interface State {
    tableName: string | undefined;
    uploadedFile: Schemas.Schema.UploadedFile | undefined;
    sheetNames: string[];
    columnsConfig: Record<string, ColumnConfig>;
}

const ROW_ID = NuxtKeys.Projects.Schemas.RowId;

function createColumnConfig(
    dtype: Dtype = "string",
    previous?: Partial<ColumnConfig>,
): ColumnConfig {
    const base = {
        unique: previous?.unique ?? false,
        optional: previous?.optional ?? true,
        primary_key: previous?.primary_key ?? false,
    };

    switch (dtype) {
        case "integer":
            return {
                dtype,
                ...base,
                constraints: previous?.dtype === "integer" ? previous.constraints : undefined,
            };

        case "float":
            return {
                dtype,
                ...base,
                constraints: previous?.dtype === "float" ? previous.constraints : undefined,
            };

        case "double":
            return {
                dtype,
                ...base,
                constraints: previous?.dtype === "double" ? previous.constraints : undefined,
            };

        case "boolean":
            return {
                dtype,
                ...base,
                constraints: undefined,
            };

        case "string":
        default:
            return {
                dtype: "string",
                ...base,
                constraints: previous?.dtype === "string" ? previous.constraints : undefined,
            };
    }
}

export default function (stateKey: string) {
    const state = useState<State>(stateKey, () => ({
        tableName: undefined,
        uploadedFile: undefined,
        sheetNames: [],
        columnsConfig: {},
    }));

    const isTabular = computed(() => state.value.uploadedFile?.type !== "json");

    const parsedFileContent = computedAsync<Record<string, unknown>[]>(async () => {
        if (!isTabular.value) {
            return [];
        }

        const { uploadedFile } = state.value;
        const buffer = await uploadedFile?.blob.arrayBuffer();

        if (uploadedFile?.type === "csv") {
            const text = new TextDecoder().decode(buffer);
            const wb = read(text, { type: "string", cellDates: true, raw: true });
            const firstSheet = wb.SheetNames[0];
            if (!firstSheet) {
                return [];
            }
            const sheet = wb.Sheets[firstSheet];
            if (!sheet) {
                return [];
            }
            state.value.sheetNames = wb.SheetNames;
            return withRowId(ROW_ID, utils.sheet_to_json(sheet, { defval: "", raw: true }));
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
        return withRowId(ROW_ID, utils.sheet_to_json(sheet, { defval: "", raw: true }));
    });

    const columns = computed<Column<Record<string, unknown>>[]>(() => {
        const firstRow = parsedFileContent.value?.[0];
        if (!firstRow) {
            return [];
        }
        return Object.keys(firstRow)
            .filter((key) => key !== ROW_ID)
            .map((key) => ({ key, label: key }));
    });

    const sampleValueByColumn = computed<Record<string, unknown>>(() => {
        const rows = parsedFileContent.value;
        if (!rows?.length) {
            return {};
        }
        const keys = new Set(rows.flatMap((row) => Object.keys(row)).filter((k) => k !== ROW_ID));
        return Object.fromEntries(
            [...keys].map((key) => [
                key,
                rows.map((row) => row[key]).find((v) => !isBlankCell(v)) ?? "",
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

                    return [columnKey, previous ?? createColumnConfig()];
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
        state.value = { ...state.value, uploadedFile: file };
    }

    function setTableName(tableName: string) {
        state.value = {
            ...state.value,
            tableName,
        };
    }

    function setColumnConfig(columnKey: string, config: ColumnConfig) {
        state.value.columnsConfig = {
            ...state.value.columnsConfig,
            [columnKey]: config,
        };
    }

    function patchColumnConfig(columnKey: string, patch: Partial<ColumnConfig>) {
        const current = state.value.columnsConfig[columnKey] ?? createColumnConfig();

        setColumnConfig(columnKey, { ...current, ...patch } as ColumnConfig);
    }

    function setColumnDataType(columnKey: string, dtype: z.infer<typeof DtypesEnum>) {
        const current = state.value.columnsConfig[columnKey];
        setColumnConfig(columnKey, createColumnConfig(dtype, current));
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
            get: () => state.value.columnsConfig[columnKey] ?? createColumnConfig(),
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
