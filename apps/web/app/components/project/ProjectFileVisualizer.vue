<script setup lang="ts">
    const { schema } = useProjectTabsSharedState();
</script>

<template>
    <div class="rounded-lg">
        <DataTable
            v-if="schema.computed.isTabular.value"
            :index="NuxtKeys.Projects.Schemas.RowId"
            :data="schema.computed.parsedFileContent"
            :columns="schema.computed.columns"
        >
            <DataTableHeader />
            <TableBody>
                <DataTableVirtualList :row-height="37">
                    <DataTableContent />
                </DataTableVirtualList>
            </TableBody>
        </DataTable>
        <CodeBlock
            v-else
            :content="() => schema.computed.jsonSchema.value?.payload"
            :file="() => schema.state.value.uploadedFile?.name"
        />
    </div>
    <section class="py-12" />
</template>
