import type { MongoRaw, ResponseProject } from "#shared/utils/schemas/types";

function $<T>(context: T | undefined, defaultValue: string, value: (value: T) => string) {
    if (!context) {
        return defaultValue;
    }

    return value(context);
}

function $$<A, B>(
    a: A | undefined,
    b: B | undefined,
    defaults: {
        none: string;
        onlyA: (a: A) => string;
        both: (a: A, b: B) => string;
    },
) {
    if (!a) {
        return defaults.none;
    }

    if (!b) {
        return defaults.onlyA(a);
    }

    return defaults.both(a, b);
}

export const NuxtKeys = {
    Projects: {
        Id: "projects:id",
        Search: "projects:search",
        SharedState: (candidateId: ResponseProject["id"] | undefined) =>
            $(candidateId, "project:state", (value) => `project:${value}:state`),
        Schemas: {
            SchemaState: (projectId: ResponseProject["id"] | undefined) =>
                $(projectId, "project:shared-state", (value) => `project:${value}:shared-state`),
            Errors: (projectId: ResponseProject["id"] | undefined) =>
                $(
                    projectId,
                    "project:schemas-errors",
                    (value) => `project:${value}:schemas-errors`,
                ),
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
            SharedState: (
                projectId: ResponseProject["id"] | undefined,
                tableName: MongoRaw["import_name"] | undefined,
            ) =>
                $$(projectId, tableName, {
                    none: "project:tables:shared-state",
                    onlyA: (id) => `project:${id}:tables:shared-state`,
                    both: (id, name) => `project:${id}:tables:${name}:shared-state`,
                }),
            State: (projectId: ResponseProject["id"] | undefined, table: MongoRaw | undefined) =>
                $$(projectId, table, {
                    none: "project:tables:selected:state",
                    onlyA: (id) => `project:${id}:tables:selected:state`,
                    both: (id, table) => `project:${id}:tables:${table.id}:selected:state`,
                }),
        },
        Edit: {
            TableName: (
                projectId: ResponseProject["id"] | undefined,
                tableName: MongoRaw["import_name"] | undefined,
            ) =>
                $$(projectId, tableName, {
                    none: "project:tables:edit:table-name",
                    onlyA: (id) => `project:${id}:tables:edit:table-name`,
                    both: (id, name) => `project:${id}:tables:${name}:edit:table-name`,
                }),
            ColumnState: (
                projectId: ResponseProject["id"] | undefined,
                tableName: MongoRaw["import_name"] | undefined,
            ) =>
                $$(projectId, tableName, {
                    none: "project:tables:edit:columns",
                    onlyA: (id) => `project:${id}:tables:edit:columns`,
                    both: (id, name) => `project:${id}:tables:${name}:edit:columns`,
                }),
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
    Params: {
        NoDefaultValue: "keys:params:default-value",
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
            Delete: "projects:tables:delete-schema",
        },
    },
} as const;
