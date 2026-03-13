import type { z } from "zod";
import type { Column } from "@/components/common/data-table/utils";
import { read, utils } from "xlsx";

interface State {
    uploadedFile: Schemas.Schema.UploadedFile | undefined;
    sheetNames: string[];
    selectedDataTypes: Record<string, z.infer<typeof DtypesEnum>>;
}

const ROW_ID = NuxtKeys.Projects.Schemas.RowId;

export default function (stateKey: string) {
    const state = useState<State>(stateKey, () => ({
        uploadedFile: undefined,
        sheetNames: [],
        selectedDataTypes: {},
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
            state.value.selectedDataTypes = Object.fromEntries(
                nextColumns.map(({ key }) => [
                    String(key),
                    state.value.selectedDataTypes[String(key)] ?? "string",
                ]),
            );
        },
        { immediate: true },
    );

    function setUploadedFile(file: Schemas.Schema.UploadedFile | undefined) {
        state.value = { ...state.value, uploadedFile: file };
    }

    function setColumnDataType(columnKey: string, value: z.infer<typeof DtypesEnum>) {
        state.value.selectedDataTypes = {
            ...state.value.selectedDataTypes,
            [columnKey]: value,
        };
    }

    function getColumnDataTypeModel(columnKey: string) {
        return computed<z.infer<typeof DtypesEnum>>({
            get: () => state.value.selectedDataTypes[columnKey] ?? "string",
            set: (value) => setColumnDataType(columnKey, value),
        });
    }

    return {
        state,
        computed: {
            isTabular,
            parsedFileContent,
            columns,
            sampleValueByColumn,
        },
        dispatch: {
            setUploadedFile,
            setColumnDataType,
            getColumnDataTypeModel,
        },
    };
}
