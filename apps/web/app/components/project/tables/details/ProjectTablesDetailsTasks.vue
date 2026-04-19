<script setup lang="ts">
    import type { ProjectTask } from "#shared/utils/schemas/types";
    import { ProjectTaskResponse } from "#shared/utils/schemas/api";
    import { ListMinus } from "lucide-vue-next";
    import { toast } from "vue-sonner";

    const { project, tables } = useProject();
    const { t } = useI18n();
    const { $logger } = useNuxtApp();

    const { data: tasks, refresh } = useApiFetch<ProjectTask[]>(
        `/tasks/project/${project.value.id}`,
        {
            method: "GET",
            query: {
                table_name: TableUtils.getTableName(tables.state.value.selectedSchema?.import_name),
            },
            transform: (payload) => {
                const _parseResult = ProjectTaskResponse.safeParse(payload);
                if (!_parseResult.success) {
                    toast.error(t("projects.id.sections.tables.details.tasks.events.bad_payload"));
                    $logger.info(_parseResult.error);
                    return [];
                }

                return _parseResult.data;
            },
            key: () =>
                NuxtKeys.Projects.Tables.Tasks(
                    project.value.id,
                    TableUtils.getTableName(tables.state.value.selectedSchema?.import_name),
                ),
        },
    );
    useIntervalFn(() => refresh(), 10000);
</script>

<template>
    <Card>
        <CardHeader>
            <CardTitle>{{ $t("projects.id.sections.tables.details.tasks.title") }}</CardTitle>
            <CardDescription>
                {{ $t("projects.id.sections.tables.details.tasks.description") }}
            </CardDescription>
        </CardHeader>
        <CardContent>
            <template v-if="!tasks?.length">
                <Empty>
                    <EmptyHeader>
                        <EmptyMedia variant="icon">
                            <ListMinus />
                        </EmptyMedia>
                        <EmptyTitle>
                            {{ $t("projects.id.sections.tables.details.tasks.empty.title") }}
                        </EmptyTitle>
                        <EmptyDescription>
                            {{ $t("projects.id.sections.tables.details.tasks.empty.description") }}
                        </EmptyDescription>
                    </EmptyHeader>
                </Empty>
            </template>
            <template v-else>
                <div class="space-y-4">
                    <template v-for="task in tasks" :key="task.data.task_id">
                        <ProjectTablesDetailsTasksCard :task="task" />
                    </template>
                </div>
            </template>
        </CardContent>
    </Card>
</template>
