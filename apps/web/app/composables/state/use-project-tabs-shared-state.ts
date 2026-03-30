export default function () {
    const { t } = useI18n();

    const projectId = useRouteParams("id", "-1", { transform: (value) => value.toString() });

    const KEY = NuxtKeys.Projects.SharedState(projectId.value?.toString());
    const project = useState<ResponseProject>(KEY);

    const schema = useProjectSchemaSharedState(() => projectId.value);
    const tables = useProjectTables(() => projectId.value);

    const Section = computed<Tabs.Project.ProjectSections>(() => ({
        Overview: t("projects.id.sections.overview.tab"),
        UploadFile: t("projects.id.sections.upload_schema.tab"),
        Tables: t("projects.id.sections.tables.tab"),
        Settings: t("projects.id.sections.settings.tab"),
        File: t("projects.id.sections.file.tab"),
    }));

    const tab = useRouteQuery<string>("tab", Section.value.Overview, {
        mode: "replace",
        transform: (value) => {
            const sections = Object.values(Section.value);
            const found = sections.find((section) => section === value);
            if (found) {
                return found;
            }

            return Section.value.Overview;
        },
    });

    return {
        tab,
        projectId,
        project,
        Section,
        schema,
        tables,
    };
}
