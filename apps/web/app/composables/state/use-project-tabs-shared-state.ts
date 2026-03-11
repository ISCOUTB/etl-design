import type { Column } from "~/components/common/data-table/utils";
import { read, utils } from "xlsx";

interface UploadedFile {
    name: string;
    size: string;
    type: string;
    blob: Blob;
}

export default function () {
    const { t } = useI18n();

    const route = useRoute();
    const uploadedFile = useState<UploadedFile | undefined>(
        NuxtKeys.Projects.Schemas.UploadFile(route.path),
        () => undefined,
    );
    const isTabular = computed(() => uploadedFile.value?.type !== "json");
    const parsedFileContent = computedAsync<Record<string, unknown>[]>(async () => {
        if (!isTabular.value) {
            return [];
        }

        const buffer = await uploadedFile.value?.blob.arrayBuffer();

        if (uploadedFile.value?.type === "csv") {
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
            return withRowId(utils.sheet_to_json(sheet, { defval: "", raw: true }));
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
        return withRowId(utils.sheet_to_json(sheet, { defval: "", raw: true }));
    });
    const columns = computed(() => {
        const firstRow = parsedFileContent.value?.[0];

        if (!firstRow) {
            return [];
        }

        return Object.keys(firstRow)
            .filter((key) => key !== NuxtKeys.Projects.Schemas.RowId)
            .map<Column<Record<string, unknown>>>((key) => ({
                key,
                label: key,
            }));
    });

    const sampleValueByColumn = computed<Record<string, unknown>>(() => {
        const rows = parsedFileContent.value;
        if (!rows?.length) {
            return {};
        }

        const keys = new Set<string>();
        for (const row of rows) {
            for (const key of Object.keys(row)) {
                if (key !== NuxtKeys.Projects.Schemas.RowId) {
                    keys.add(key);
                }
            }
        }

        const result: Record<string, unknown> = {};
        for (const key of keys) {
            const firstValid = rows.map((row) => row[key]).find((value) => !isBlankCell(value));

            result[key] = firstValid ?? "";
        }

        return result;
    });

    const selectedDataTypes = useState<Record<string, Schemas.Schema.DataType>>(
        NuxtKeys.Projects.Schemas.SelectedDataType(route.path),
        () => ({}),
    );

    const Section = computed<Tabs.Project.ProjectSections>(() => ({
        General: t("projects.id.sections.general_information.tab"),
        Schema: t("projects.id.sections.schema.tab"),
        Settings: t("projects.id.sections.settings.tab"),
        File: t("projects.id.sections.file.tab"),
    }));

    const tab = useRouteQuery<string>("tab", Section.value.General, {
        mode: "replace",
        transform: (value) => {
            const sections = Object.values(Section.value);
            const found = sections.find((section) => section === value);
            if (found) {
                return found;
            }

            return Section.value.General;
        },
    });

    function withRowId(rows: Record<string, unknown>[]): Record<string, unknown>[] {
        return rows.map((row, index) => ({
            ...row,
            [NuxtKeys.Projects.Schemas.RowId]: crypto.randomUUID() ?? `row-${index}`,
        }));
    }

    function setColumnDataType(columnKey: string, value: Schemas.Schema.DataType) {
        selectedDataTypes.value = {
            ...selectedDataTypes.value,
            [columnKey]: value,
        };
    }

    function isBlankCell(value: unknown): boolean {
        if (value === null || value === undefined) {
            return true;
        }

        if (typeof value === "string") {
            return value.trim() === "";
        }

        return false;
    }

    function getColumnDataTypeModel(columnKey: string) {
        return computed<Schemas.Schema.DataType>({
            get: () => selectedDataTypes.value[columnKey] ?? "text",
            set: (value) => setColumnDataType(columnKey, value),
        });
    }

    watch(
        columns,
        (nextColumns) => {
            selectedDataTypes.value = Object.fromEntries(
                nextColumns.map((column) => {
                    const key = String(column.key);

                    return [key, selectedDataTypes.value[key] ?? "text"];
                }),
            );
        },
        { immediate: true },
    );

    return {
        uploadedFile,
        columns,
        sampleValueByColumn,
        isTabular,
        parsedFileContent,
        Section,
        tab,
        selectedDataTypes,
        setColumnDataType,
        getColumnDataTypeModel,
    };
}
