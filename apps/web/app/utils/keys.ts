import type { z } from "zod";

export const NuxtKeys = {
    Projects: {
        Id: "projects:id",
        Search: "projects:search",
        Delete: {
            Validation: (project: z.infer<typeof ResponseProjectSchema> | undefined) => {
                if (!project) {
                    return "project:delete";
                }

                return `project:${project.id}:delete`;
            },
        },
        SharedState: (candidateId: z.infer<typeof ResponseProjectSchema>["id"] | undefined) => {
            if (!candidateId) {
                return "project:state";
            }

            return `project:${candidateId}:state`;
        },
        Schemas: {
            SchemaState: (route: string) => `project:${route}:shared-state`,
            ExampleFormat: "project:schema:example-format",
            RowId: "__rowId",
        },
        Tables: {
            TablesState: (projectId: z.infer<typeof ResponseProjectSchema>["id"] | undefined) => {
                if (!projectId) {
                    return "project:tables";
                }

                return `project:${projectId}:tables`;
            },
            CollapsibleState: (table: z.infer<typeof MongoRawSchema>) =>
                `project:table:${table.id}:collapsible:open`,
            RawSchemas: (projectId: z.infer<typeof ResponseProjectSchema>["id"] | undefined) => {
                if (!projectId) {
                    return "project:raw-schemas";
                }

                return `project:${projectId}:raw-schemas`;
            },
            View: (route: string) => `project:tables:${route}:view`,
            TabsManager: (route: string) => `project:tables:${route}:tabs-manager`,
        },
    },
    Components: {
        DataTable: {
            Sorting: (route: string) => `data-table:sorting-state:${route}`,
        },
    },
    Sidebar: {
        OpenCollapsible: (group: Components.Sidebar.GroupCollapsibleKind) =>
            `sidebar:${group.kind}:${group.label}`,
    },
};

export const ModalKeys = {
    Projects: {
        Delete: {
            ConfirmationModal: "projects:delete:confirmation-modal",
        },
        Schema: {
            UploadFile: "projects:schema:upload-file",
        },
        Tables: {
            ViewSchema: "projects:tables:view-schema",
        },
    },
};
