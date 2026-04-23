export const [useProvideProjectQueryBuilder, useProjectQueryBuilderState] = createInjectionState(
    (project: ResponseProject, _schema: MongoRaw | undefined) => {
        const schema = useState<MongoRaw | undefined>(
            NuxtKeys.Projects.QueryBuilder.SelectedSchema(project.id),
            () => _schema,
        );

        const rows = useState<Record<string, unknown>[]>(
            NuxtKeys.Projects.QueryBuilder.Rows(project.id),
            () => [],
        );

        return { state: { schema, rows } };
    },
);
