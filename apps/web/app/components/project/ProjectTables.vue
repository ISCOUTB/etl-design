<script setup lang="ts">
    import { Search, Table2 } from "lucide-vue-next";

    const { tables } = useProjectTabsSharedState();
</script>

<template>
    <div class="flex flex-col w-full grow gap-8">
        <div class="flex flex-col gap-4">
            <div class="space-y-0.5">
                <h2 class="text-lg font-medium text-foreground">Tables</h2>
                <p class="text-sm text-muted-foreground">
                    {{ tables.state.tableSchemas.value.schemas.length }} Table(s) in this project
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
            <div class="flex flex-col space-y-4">Table Card goes brrrr...</div>
        </template>
        <template v-else>
            <Empty class="flex flex-col items-center justify-between">
                <EmptyHeader>
                    <EmptyMedia>
                        <Table2 class="size-6 text-muted-foreground" />
                    </EmptyMedia>
                    <EmptyTitle> No Tables Found </EmptyTitle>
                </EmptyHeader>
                <EmptyContent>
                    <div class="flex space-x-2">
                        <Button class="cursor-pointer"> Create a new one </Button>
                        <Button variant="outline" @click="$router.back()">
                            {{ $t("common.actions.go_back") }}
                        </Button>
                    </div>
                </EmptyContent>
            </Empty>
        </template>
    </div>
</template>
