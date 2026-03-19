import type { MongoRaw, ResponseProject } from "#shared/utils/schemas/types";

function $<T>(context: T | undefined, defaultValue: string, value: (value: T) => string) {
    if (!context) {
        return defaultValue;
    }

    return value(context);
}

export const NuxtKeys = {
    Projects: {
        Id: "projects:id",
        Search: "projects:search",
        Delete: {
            Validation: (project: ResponseProject | undefined) =>
                $(project, "project:delete", (value) => `project:${value.id}:delete`),
        },
        SharedState: (candidateId: ResponseProject["id"] | undefined) =>
            $(candidateId, "project:state", (value) => `project:${value}:state`),
        Schemas: {
            SchemaState: (projectId: ResponseProject["id"] | undefined) =>
                $(projectId, "project:shared-state", (value) => `project:${value}:shared-state`),
            ExampleFormat: "project:schema:example-format",
            RowId: "__rowId",
        },
        Tables: {
            TableState: (projectId: ResponseProject["id"] | undefined) =>
                $(projectId, "project:tables", (value) => `project:${value}:tables`),
            CollapsibleState: (table: MongoRaw) => `project:table:${table.id}:collapsible:open`,
            RawSchemas: (projectId: ResponseProject["id"] | undefined) =>
                $(projectId, "project:raw-schemas", (value) => `project:${value}:raw-schemas`),
            View: (projectId: ResponseProject["id"] | undefined) =>
                $(projectId, "project:tables:view", (value) => `project:${value}:tables:view`),
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
} as const;

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
} as const;
