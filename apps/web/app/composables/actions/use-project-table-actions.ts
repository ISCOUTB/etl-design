import type { JsonSchema } from "~~/shared/utils/schemas/types";

export default function () {
    const { $api } = useNuxtApp();
    const [loading] = useToggle(false);

    async function handleSchemaTransition(
        projectId: ResponseProject["id"],
        import_name: MongoRaw["import_name"],
    ) {
        loading.value = true;

        try {
            const response = await $api(`/schemas/${projectId}`, {
                method: "DELETE",
                query: {
                    table_name: TableUtils.getTableName(import_name),
                },
            });

            return response;
        } finally {
            loading.value = false;
        }
    }

    async function uploadFile(
        file: File,
        project: ResponseProject,
        tableName: string,
        dtypes: Record<string, Record<string, ColumnConfig>>,
    ) {
        loading.value = true;

        try {
            const response = await $api("/uploads/table-excel", {
                method: "POST",
                body: new FormBuilder()
                    .append("spreadsheet", file, file.name)
                    .append("project_id", project.id)
                    .append("table_name", tableName)
                    .append("dtypes_str", JSON.stringify(dtypes))
                    .build(),
                query: {
                    execute_sql: Boolean(project.db_host && project.db_port),
                },
            });

            return response;
        } finally {
            loading.value = false;
        }
    }

    async function uploadSchema(project: ResponseProject, tableName: string, schema: JsonSchema) {
        loading.value = true;

        try {
            const response = await $api("/uploads/table-json", {
                method: "POST",
                body: SchemaUtils.Builder.buildJsonSchema(tableName, project.id, schema, []),
                query: {
                    execute_sql: Boolean(project.db_host && project.db_port),
                },
            });

            return response;
        } finally {
            loading.value = false;
        }
    }

    return {
        state: {
            loading,
        },
        handleSchemaTransition,
        uploadFile,
        uploadSchema,
    };
}
