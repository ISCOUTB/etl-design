export const [useProvideProjectQueryBuilder, useProjectQueryBuilderState] = createInjectionState(
    (project: ResponseProject, _schema: MongoRaw | undefined) => {
        const schema = useState<MongoRaw | undefined>(
            NuxtKeys.Projects.QueryBuilder.SelectedSchema(project.id),
            () => _schema,
        );

        return { state: { schema } };
    },
);
