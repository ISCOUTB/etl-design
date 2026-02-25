import type { ColumnDef } from "@tanstack/vue-table";
import type { z } from "zod";
import CellEmpty from "@/components/common/data-table/DataTableCellEmpty.vue";
import HeaderSorted from "@/components/common/data-table/DataTableHeaderSorted.vue";
import ActionsDropdown from "@/components/projects/ProjectsActionsDropdown.vue";

export default function () {
    const { t } = useI18n();

    const columns = computed<ColumnDef<z.infer<typeof ResponseProjectSchema>>[]>(() => [
        {
            accessorKey: "name",
            header: ({ column }) =>
                h(HeaderSorted<z.infer<typeof ResponseProjectSchema>, unknown>, {
                    column,
                    title: t("projects.create.fields.name.label"),
                }),
        },
        {
            accessorKey: "provider",
            header: ({ column }) =>
                h(HeaderSorted<z.infer<typeof ResponseProjectSchema>, unknown>, {
                    column,
                    title: t("projects.create.fields.provider.label"),
                }),
            cell: ({ row }) => {
                const value = row.getValue("provider");
                if (value) {
                    return value;
                }

                return h(CellEmpty);
            },
        },
        {
            accessorKey: "db_host",
            header: ({ column }) =>
                h(HeaderSorted<z.infer<typeof ResponseProjectSchema>, unknown>, {
                    column,
                    title: t("projects.create.fields.db_host.label"),
                }),
            cell: ({ row }) => {
                const value = row.getValue("provider");
                if (value) {
                    return value;
                }

                return h(CellEmpty);
            },
        },
        {
            accessorKey: "db_name",
            header: ({ column }) =>
                h(HeaderSorted<z.infer<typeof ResponseProjectSchema>, unknown>, {
                    column,
                    title: t("projects.create.fields.db_name.label"),
                }),
            cell: ({ row }) => {
                const value = row.getValue("provider");
                if (value) {
                    return value;
                }

                return h(CellEmpty);
            },
        },
        {
            id: t("projects.view.table.actions.label"),
            cell: ({ row }) => h(ActionsDropdown, { project: row.original }),
        },
    ]);

    return { columns };
}
