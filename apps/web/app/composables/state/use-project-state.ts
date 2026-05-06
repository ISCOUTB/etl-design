const VIEWS = {
    Overview: "overview",
    UploadFile: "upload-file",
    Tables: "tables",
    Settings: "settings",
    File: "file",
    QueryBuilder: "query-builder",
} as const;

export const [useProvideProjectState, _useProjectState] = createInjectionState(
    (initialId: string | undefined) => {
        const project = useState<ResponseProject>(NuxtKeys.Projects.SharedState(initialId));

        const view = useRouteQuery<string>("tab", VIEWS.Overview, {
            mode: "replace",
            transform: (value) => {
                const sections = Object.values(VIEWS);
                const found = sections.find((section) => section === value);
                if (found) {
                    return found;
                }

                return VIEWS.Overview;
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
