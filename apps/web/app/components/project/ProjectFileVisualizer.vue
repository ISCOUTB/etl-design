<script setup lang="ts">
    const { uploadSchema } = useProject();
</script>

<template>
    <div class="rounded-lg">
        <DataTable
            v-if="uploadSchema.computed.isTabular.value"
            :index="NuxtKeys.Projects.Schemas.RowId"
            :data="uploadSchema.computed.parsedFileContent"
            :columns="uploadSchema.computed.columns"
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
            :content="() => uploadSchema.computed.jsonSchema.value"
            :file="() => uploadSchema.state.value.uploadedFile?.name"
        />
    </div>
    <section class="py-12" />
</template>
