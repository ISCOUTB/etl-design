<script setup lang="ts">
    import Ajv from "ajv";

    const { uploadedFile, columns, isTabular, parsedFileContent } = useProjectTabsSharedState();

    const ajv = shallowRef(new Ajv({ strict: true, allErrors: true, validateSchema: true }));

    const schema = computedAsync(async () => {
        if (isTabular.value || !uploadedFile.value) {
            return;
        }

        const payload = JSON.parse(await uploadedFile.value.blob.text());
        const declaredDraft7 =
            typeof payload === "object" &&
            payload !== null &&
            !Array.isArray(payload) &&
            (payload.$schema === "http://json-schema.org/draft-07/schema#" ||
                payload.$schema === "https://json-schema.org/draft-07/schema#");

        return {
            valid: declaredDraft7 && ajv.value.validateSchema(payload),
            payload,
            errors: ajv.value.errors,
        };
    });
</script>

<template>
    <DataTable
        v-if="isTabular"
        :index="NuxtKeys.Projects.Schemas.RowId"
        :data="parsedFileContent"
        :columns="columns"
    >
        <TableCaption> {{ uploadedFile?.name }} </TableCaption>
        <DataTableHeader />
        <TableBody>
            <DataTableVirtualList :row-height="37">
                <DataTableContent />
            </DataTableVirtualList>
        </TableBody>
    </DataTable>
    <CodeBlock v-else :content="schema?.payload" :file="uploadedFile?.name" />
</template>
