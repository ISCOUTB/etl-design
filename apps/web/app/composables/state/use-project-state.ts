export const [useProvideProjectState, _useProjectState] = createInjectionState(
    (initialId: string | undefined) => {
        const { t } = useI18n();

        const project = useState<ResponseProject>(NuxtKeys.Projects.SharedState(initialId));

        const VIEWS = computed(() => ({
            Overview: t("projects.id.sections.overview.tab"),
            UploadFile: t("projects.id.sections.upload_schema.tab"),
            Tables: t("projects.id.sections.tables.tab"),
            Settings: t("projects.id.sections.settings.tab"),
            File: t("projects.id.sections.file.tab"),
            QueryBuilder: t("projects.id.sections.query_builder.tab"),
        }));

        const view = useRouteQuery<string>("tab", VIEWS.value.Overview, {
            mode: "replace",
            transform: (value) => {
                const sections = Object.values(VIEWS.value);
                const found = sections.find((section) => section === value);
                if (found) {
                    return found;
                }

                return VIEWS.value.Overview;
            },
        });

        const tables = useProvideProjectTablesState(initialId);
        const uploadSchema = useProvideProjectUploadSchemaState(initialId);

        return {
            state: {
                project,
                view,
                VIEWS,
            },
            tables,
            uploadSchema,
        };
    },
);

export function useProject() {
    const state = _useProjectState();
    if (!state) {
        throw createError({
            status: 500,
            statusText:
                "Project state not injected. Ensure useProvideProjectState is called in a parent component.",
            fatal: true,
        });
    }
    return state;
}
