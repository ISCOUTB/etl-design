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
            State: (route: string) => `project:${route}:shared-state`,
            UploadFile: (route: string) => `project:${route}:upload-file`,
            SheetNames: (route: string) => `project:${route}:sheet-names`,
            Columns: (route: string) => `project:${route}:columns-definition`,
            SelectedDataType: (route: string) => `projects:${route}:selected-data-type`,
            ExampleFormat: "project:schema:example-format",
            RowId: "__rowId",
        },
    },
    Components: {
        DataTable: {
            Sorting: (route: string) => `data-table:sorting-state:${route}`,
        },
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
    },
};
