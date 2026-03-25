<script setup lang="ts">
    import type { z } from "zod";
    import { Edit, Eye, Table2, Trash2 } from "lucide-vue-next";

    const { $localeRoute } = useNuxtApp();
    const route = useRoute();

    const { tables, Section, projectId } = useProjectTabsSharedState();

    const events = useAppEvents();
    const modal = useModal();

    const dropdownItems = computed<
        Components.GenericDropdown.Item<z.infer<typeof MongoRawSchema>>[][]
    >(() => [
        [
            {
                label: "projects.id.sections.tables.card.dropdown.view_schema",
                icon: Eye,
                action: (context) => {
                    if (!context) {
                        return;
                    }

                    tables.dispatch.setSelectedSchema(context);
                    events.emit("event:projects:table:change-view", { value: "view" });
                },
            },
            {
                label: "projects.id.sections.tables.card.dropdown.edit",
                icon: Edit,
                to: (context) => {
                    if (!context) {
                        return;
                    }

                    return $localeRoute({
                        name: "projects-id-tables-tableName-edit",
                        params: {
                            id: projectId.value,
                            tableName: TableUtils.getTableName(context.import_name),
                        },
                        query: { callbackUrl: route.fullPath },
                    });
                },
            },
        ],
        [
            {
                label: "projects.id.sections.tables.card.dropdown.delete",
                icon: Trash2,
                action: (context) => {
                    if (!context) {
                        return;
                    }

                    modal.dispatch.loadComponent({
                        loader: () =>
                            import("@/components/project/tables/ProjectTablesDeleteConfirmationModal.vue"),
                        key: ModalKeys.Projects.Tables.Delete,
                        props: {
                            table: context,
                        },
                    });
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
                <ProjectTablesCard :table="$item" :dropdown-items="dropdownItems" />
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
