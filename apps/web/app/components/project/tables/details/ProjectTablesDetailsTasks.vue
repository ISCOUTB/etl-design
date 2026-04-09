<script setup lang="ts">
    import type { ProjectTask } from "#shared/utils/schemas/types";
    import { ProjectTaskResponse } from "#shared/utils/schemas/api";
    import { ListMinus, ListTodo } from "lucide-vue-next";
    import { toast } from "vue-sonner";
    import { cn } from "@/lib/utils";

    const {
        state: { project },
        tables,
    } = useProject();
    const { t } = useI18n();

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
                    console.warn(_parseResult.error);
                    toast.error(t("projects.id.sections.tables.details.tasks.events.bad_payload"));
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
                        <Item
                            variant="outline"
                            :class="
                                cn(
                                    task.data.error?.length &&
                                        'border-destructive/50 bg-destructive/10',
                                )
                            "
                        >
                            <ItemMedia>
                                <ListTodo />
                            </ItemMedia>
                            <ItemContent>
                                <ItemTitle>
                                    {{ $t("projects.id.sections.tables.details.tasks.item") }}
                                </ItemTitle>
                                <ItemDescription class="text-xs">
                                    {{ task.data.task_id }}
                                </ItemDescription>
                            </ItemContent>
                            <ItemActions class="w-full">
                                <Accordion type="multiple" class="w-full">
                                    <AccordionItem
                                        v-if="task.data.error?.length"
                                        v-slot="{ open }"
                                        value="errors"
                                    >
                                        <AccordionTrigger
                                            :class="
                                                cn(
                                                    'px-4 cursor-pointer border-b-destructive/10 bg-destructive/15 hover:no-underline',
                                                    open && 'border-b rounded-b-none',
                                                )
                                            "
                                        >
                                            {{
                                                $t(
                                                    "projects.id.sections.tables.details.tasks.errors",
                                                )
                                            }}
                                        </AccordionTrigger>
                                        <AccordionContent
                                            class="p-4 rounded-b-lg border border-destructive/10"
                                        >
                                            {{ task.data.error }}
                                        </AccordionContent>
                                    </AccordionItem>
                                </Accordion>
                            </ItemActions>
                        </Item>
                    </template>
                </div>
            </template>
        </CardContent>
    </Card>
</template>
