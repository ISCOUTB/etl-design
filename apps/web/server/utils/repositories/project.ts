import type { MongoRaw, ResponseProject } from "#shared/utils/schemas/types";
import type { Session } from "next-auth";
import { TableUtils } from "#shared/utils/project/tables";
import {
    MongoGetSchemasResponse,
    MongoRawSchema,
    ResponseProjectSchema,
} from "#shared/utils/schemas/api";

export const ProjectRepository = {
    async get(session: Session, id: ResponseProject["id"]) {
        const response = await ApiClient.getInstance(session)(`/projects/id/${id}`, {
            method: "GET",
        });

        const parsed = ResponseProjectSchema.safeParse(response);
        if (!parsed.success) {
            throw createError({ status: 400, statusText: ResponseCodesRecord.Server.BadPayload });
        }

        return parsed.data;
    },
    async getTable(session: Session, projectId: ResponseProject["id"], importName: MongoRaw["id"]) {
        const response = await ApiClient.getInstance(session)(`/schemas/${projectId}/raw`, {
            method: "GET",
            query: {
                table_name: TableUtils.getTableName(importName),
            },
        });

        const parsed = MongoRawSchema.safeParse(response);
        if (!parsed.success) {
            throw createError({ status: 400, statusText: ResponseCodesRecord.Server.BadPayload });
        }

        return parsed.data;
    },
    async getTables(session: Session, projectId: ResponseProject["id"]) {
        const response = await ApiClient.getInstance(session)(`/schemas/search/${projectId}`, {
            method: "GET",
        });

        const parsed = MongoGetSchemasResponse.safeParse(response);
        if (!parsed.success) {
            throw createError({ status: 400, statusText: ResponseCodesRecord.Server.BadPayload });
        }

        return parsed.data;
    },
};
