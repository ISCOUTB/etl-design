export const [useProvideProjectState, _useProjectState] = createInjectionState(
    (initialId: string | undefined) => {
        const { t } = useI18n();

        const project = useState<ResponseProject>(NuxtKeys.Projects.SharedState(initialId));

        const VIEWS = computed(() => ({
            Overview: {
                key: "Overview",
                value: t("projects.id.sections.overview.tab"),
            },
            UploadFile: {
                key: "UploadFile",
                value: t("projects.id.sections.upload_schema.tab"),
            },
            Tables: {
                key: "Tables",
                value: t("projects.id.sections.tables.tab"),
            },
            Settings: {
                key: "Settings",
                value: t("projects.id.sections.settings.tab"),
            },
            File: {
                key: "File",
                value: t("projects.id.sections.file.tab"),
            },
            QueryBuilder: {
                key: "QueryBuilder",
                value: t("projects.id.sections.query_builder.tab"),
            },
        }));

        const cookie = useCookie(NuxtKeys.Projects.CookieTab(initialId), {
            default: () => VIEWS.value.Overview.key,
        });

        const view = useRouteQuery<string>("tab", VIEWS.value.Overview.value, {
            mode: "replace",
        });

        syncRef(cookie, view, {
            direction: "both",
            transform: {
                ltr(left) {
                    const sections = Object.values(VIEWS.value);
                    const found = sections.find((section) => section.key === left);
                    if (found) {
                        return found.value;
                    }

                    return VIEWS.value.Overview.value;
                },
                rtl(right) {
                    const sections = Object.values(VIEWS.value);
                    const found = sections.find((section) => section.value === right);
                    if (found) {
                        return found.key;
                    }

                    return VIEWS.value.Overview.key;
                },
            },
        });

        const tables = useProvideProjectTablesState(initialId);
        const uploadSchema = useProvideProjectUploadSchemaState(initialId);
        const queryBuilder = useProvideProjectQueryBuilder(project.value, undefined);

        return {
            project,
            view,
            VIEWS,
            tables,
            uploadSchema,
            queryBuilder,
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
