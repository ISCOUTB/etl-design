<script setup lang="ts">
    import type { Column } from "@/components/common/data-table/utils";
    import Ajv from "ajv";
    import { read, utils } from "xlsx";

    interface Props {
        name: string;
        size: string;
        blob: Blob;
        format: "json" | "csv" | "xlsx" | "xls";
    }

    const props = defineProps<Props>();
    const ajv = shallowRef(new Ajv({ strict: true, allErrors: true, validateSchema: true }));

    function withRowId(rows: Record<string, unknown>[]): Record<string, unknown>[] {
        return rows.map((row, index) => ({
            ...row,
            [NuxtKeys.Projects.Schemas.RowId]: crypto.randomUUID() ?? `row-${index}`,
        }));
    }

    const isTabular = computed(() => props.format !== "json");

    const parsed = computedAsync<Record<string, unknown>[]>(async () => {
        if (!isTabular.value) {
            return [];
        }

        const buffer = await props.blob.arrayBuffer();

        if (props.format === "csv") {
            const text = new TextDecoder().decode(buffer);
            const wb = read(text, { type: "string", cellDates: true, raw: true });

            const firstSheet = wb.SheetNames[0];
            if (!firstSheet) {
                return [];
            }

            const sheet = wb.Sheets[firstSheet];
            if (!sheet) {
                return [];
            }
            return withRowId(utils.sheet_to_json(sheet, { defval: "", raw: true }));
        }

        const wb = read(buffer, { type: "array", cellDates: true, raw: true });
        const firstSheet = wb.SheetNames[0];
        if (!firstSheet) {
            return [];
        }
        const sheet = wb.Sheets[firstSheet];
        if (!sheet) {
            return [];
        }
        return withRowId(utils.sheet_to_json(sheet, { defval: "", raw: true }));
    });
    const columns = computed(() => {
        const firstRow = parsed.value?.[0];

        if (!firstRow) {
            return [];
        }

        return Object.keys(firstRow)
            .filter((key) => key !== NuxtKeys.Projects.Schemas.RowId)
            .map<Column<Record<string, unknown>>>((key) => ({
                key,
                label: key,
            }));
    });

    const schema = computedAsync(async () => {
        if (isTabular.value) {
            return;
        }

        const payload = JSON.parse(await props.blob.text());
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
        :data="parsed"
        :columns="columns"
    >
        <TableCaption> {{ `${name} - (${size})` }} </TableCaption>
        <DataTableHeader />
        <TableBody>
            <DataTableVirtualList>
                <DataTableContent />
            </DataTableVirtualList>
        </TableBody>
    </DataTable>
    <CodeBlock v-else :content="schema?.payload" :file="props.name" />
</template>
