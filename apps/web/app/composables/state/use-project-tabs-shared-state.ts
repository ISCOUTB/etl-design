export default function () {
    const { t } = useI18n();

    const route = useRoute();
    const projectId = useRouteParams("id");

    const schema = useProjectSchemaSharedState(NuxtKeys.Projects.Schemas.SchemaState(route.path));
    const tables = useProjectTables(() => projectId.value?.toString());

    const Section = computed<Tabs.Project.ProjectSections>(() => ({
        General: t("projects.id.sections.general_information.tab"),
        Schema: t("projects.id.sections.schema.tab"),
        Tables: t("projects.id.sections.tables.tab"),
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
        tab,
        Section,
        schema,
        tables,
    };
}
