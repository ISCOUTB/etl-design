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

    function withRowId(rows: Record<string, unknown>[]): Record<string, unknown>[] {
        return rows.map((row, index) => ({
            ...row,
            [NuxtKeys.Projects.Schemas.RowId]: crypto.randomUUID() ?? `row-${index}`,
        }));
    }

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

    return {
        uploadedFile,
        columns,
        isTabular,
        parsedFileContent,
        Section,
        tab,
    };
}
