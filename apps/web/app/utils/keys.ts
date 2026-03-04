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
    },
};

export const ModalKeys = {
    Projects: {
        Delete: {
            ConfirmationModal: "projects:delete:confirmation-modal",
        },
    },
};
