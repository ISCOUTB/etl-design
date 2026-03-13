<script setup lang="ts">
    import Ajv from "ajv";

    const { schema } = useProjectTabsSharedState();

    const ajv = shallowRef(new Ajv({ strict: true, allErrors: true, validateSchema: true }));

    const jsonSchema = computedAsync(async () => {
        if (schema.computed.isTabular.value || !schema.state.value.uploadedFile) {
            return;
        }

        const payload = JSON.parse(await schema.state.value.uploadedFile.blob.text());
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
    <div class="rounded-lg">
        <DataTable
            v-if="schema.computed.isTabular"
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
            :content="jsonSchema?.payload"
            :file="schema.state.value.uploadedFile?.name"
        />
    </div>
    <section class="py-12" />
</template>
