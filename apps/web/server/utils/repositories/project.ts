import type { Session } from "next-auth";
import { MongoGetSchemasResponse } from "#shared/utils/schemas/api";

export const ProjectRepository = {
    async getTables(session: Session, projectId: string) {
        const response = await ApiClient.getInstance()(`/schemas/search/${projectId}`, {
            method: "GET",
            headers: {
                Authorization: `Bearer ${session.accessToken}`,
            },
        });

        const parsed = MongoGetSchemasResponse.safeParse(response);
        if (!parsed.success) {
            throw createError({ status: 400, statusText: ResponseCodesRecord.Server.BadPayload });
        }

        return parsed.data;
    },
};
