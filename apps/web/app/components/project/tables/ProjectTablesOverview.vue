<script setup lang="ts">
    import type { z } from "zod";
    import { Eye, Table2 } from "lucide-vue-next";

    const { tables, Section } = useProjectTabsSharedState();

    const events = useAppEvents();

    const dropdownItems = computed<
        Components.GenericDropdown.Item<z.infer<typeof MongoRawSchema>>[][]
    >(() => [
        [
            {
                label: "projects.id.sections.tables.card.actions.view_schema",
                icon: Eye,
                action: (context) => {
                    if (!context) {
                        return;
                    }

                    tables.dispatch.setSelectedSchema(context);
                    events.emit("event:projects:table:change-view", { value: "view" });
                },
            },
        ],
    ]);
</script>

<template>
    <template v-if="tables.state.value.tableSchemas.length > 0">
        <PaginationRoot
            :items="tables.state.value.tableSchemas"
            index="id"
            :page="1"
            :page-size="10"
            :total-pages="1"
            class="flex flex-col space-y-4"
        >
            <template #item="{ $item }">
                <ProjectTableCard :table="$item" :dropdown-items="dropdownItems" />
            </template>
        </PaginationRoot>
    </template>
    <template v-else>
        <Empty class="flex flex-col items-center justify-between">
            <EmptyHeader>
                <EmptyMedia>
                    <Table2 class="size-6 text-muted-foreground" />
                </EmptyMedia>
                <EmptyTitle>
                    {{ $t("projects.id.sections.tables.empty.header.title") }}
                </EmptyTitle>
            </EmptyHeader>
            <EmptyContent>
                <div class="flex space-x-2">
                    <Button
                        class="cursor-pointer"
                        @click="events.emit('event:projects:change-tab', { value: Section.Schema })"
                    >
                        {{ $t("projects.id.sections.tables.empty.events.create_new") }}
                    </Button>
                    <Button variant="outline" @click="$router.back()">
                        {{ $t("common.actions.go_back") }}
                    </Button>
                </div>
            </EmptyContent>
        </Empty>
    </template>
</template>
