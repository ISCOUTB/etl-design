<!-- eslint-disable antfu/consistent-list-newline -->
<script setup lang="ts">
    import type { z } from "zod";
    import type { Column } from "~/components/common/data-table/utils";

    definePageMeta({
        title: "Test Page",
        layout: "default",
        middleware: ["development-only"],
    });

    useSeoMeta({
        robots: "noindex, nofollow",
    });

    const columns: Column<z.infer<typeof ResponseProjectSchema>>[] = [
        { key: "id", label: "ID" },
        { key: "name", label: "Name" },
        { key: "provider", label: "Provider" },
    ];
    const data = useState("mock-data", () =>
        Array.from({ length: 10000 }).map((_, index) => mockResponseProjectSchema(index)),
    );
</script>

<template>
    <DataTable :data="data" index="id" :columns="columns" :page-size="10" class="h-screen">
        <TableCaption>Mock Data</TableCaption>
        <DataTableHeader />
        <TableBody>
            <DataTableVirtualList :row-height="37">
                <DataTableContent />
            </DataTableVirtualList>
        </TableBody>
    </DataTable>
</template>
