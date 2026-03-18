<script setup lang="ts">
    import type { z } from "zod";
    import { Eye, Search, Table2 } from "lucide-vue-next";

    const events = useAppEvents();
    const { tables, Section } = useProjectTabsSharedState();
    const modal = useModal();

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

                    modal.dispatch.loadComponent({
                        loader: () => import("@/components/project/ProjectTableSchemaView.vue"),
                        key: ModalKeys.Projects.Tables.ViewSchema,
                        kind: "dialog",
                        props: {
                            schema: context,
                        },
                    });

                    if (
                        modal.state.value.currentModalKey === ModalKeys.Projects.Tables.ViewSchema
                    ) {
                        modal.dispatch.setOpen(true);
                    }
                },
            },
        ],
    ]);
</script>

<template>
    <div class="flex flex-col w-full grow gap-8">
        <div class="flex flex-col gap-4">
            <div class="space-y-0.5">
                <h2 class="text-lg font-medium text-foreground">
                    {{ $t("projects.id.sections.tables.header.title") }}
                </h2>
                <p class="text-sm text-muted-foreground">
                    {{
                        $t("projects.id.sections.tables.header.description", {
                            length: tables.state.tableSchemas.value.schemas.length,
                        })
                    }}
                </p>
            </div>
            <div>
                <InputGroup class="max-w-md">
                    <InputGroupInput placeholder="Search Tables..." />
                    <InputGroupAddon align="inline-start">
                        <Search class="size-4 text-muted-foreground" />
                    </InputGroupAddon>
                </InputGroup>
            </div>
        </div>

        <template v-if="tables.state.tableSchemas.value.schemas.length > 0">
            <PaginationRoot
                :items="tables.state.tableSchemas.value.schemas"
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
                            @click="
                                events.emit('event:projects:change-tab', { value: Section.Schema })
                            "
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
    </div>
</template>
