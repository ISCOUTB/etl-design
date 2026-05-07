<script setup lang="ts">
    import { Table2 } from "lucide-vue-next";

    const { VIEWS, tables } = useProject();

    const events = useAppEvents();
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
                <ProjectTablesCard :table="$item" />
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
                            events.emit('event:projects:change-tab', {
                                value: VIEWS.UploadFile.value,
                            })
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
</template>
