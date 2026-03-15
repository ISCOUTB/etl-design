import type {
    ColumnConfig,
    ColumnDtype,
    CreateTableFromJson,
    Dtype,
} from "#shared/utils/schemas/types";
import { ColumnDtypesSchema } from "#shared/utils/schemas/api";

export const SchemaUtils = {
    File: {
        normalizeMime(mime: string | undefined): string {
            return (mime ?? "").toLowerCase().trim();
        },

        getFileExtension(name: string): string {
            const ext = name.split(".").pop()?.toLowerCase();
            return ext ?? "";
        },
    },

    isBlankCell(value: unknown): boolean {
        if (value === null || value === undefined) {
            return true;
        }
        if (typeof value === "string") {
            return value.trim() === "";
        }
        return false;
    },

    withRowId(rowId: string, rows: Record<string, unknown>[]): Record<string, unknown>[] {
        return rows.map((row, index) => ({
            ...row,
            [rowId]: crypto.randomUUID() ?? `row-${index}`,
        }));
    },

    declaredDraft(
        payload: unknown,
        drafts: string[] = [
            "http://json-schema.org/draft-07/schema#",
            "https://json-schema.org/draft-07/schema#",
        ],
    ) {
        return (
            typeof payload === "object" &&
            payload !== null &&
            !Array.isArray(payload) &&
            "$schema" in payload &&
            drafts.includes(String(payload.$schema))
        );
    },

    normalizeColumnConfig(config: ColumnConfig, previous?: Partial<ColumnConfig>): ColumnConfig {
        const base: Omit<ColumnConfig, "dtype" | "constraints"> = {
            unique: config.unique ?? false,
            optional: config.optional ?? true,
            primary_key: config.primary_key ?? false,
        };

        switch (config.dtype) {
            case "integer":
                return {
                    dtype: config.dtype,
                    ...base,
                    constraints: previous?.dtype === "integer" ? previous.constraints : undefined,
                };

            case "float":
                return {
                    dtype: config.dtype,
                    ...base,
                    constraints: previous?.dtype === "float" ? previous.constraints : undefined,
                };

            case "double":
                return {
                    dtype: config.dtype,
                    ...base,
                    constraints: previous?.dtype === "double" ? previous.constraints : undefined,
                };

            case "boolean":
                return {
                    dtype: config.dtype,
                    ...base,
                    constraints: undefined,
                };

            case "string":
            default:
                return {
                    dtype: "string",
                    ...base,
                    constraints: previous?.dtype === "string" ? previous.constraints : undefined,
                };
        }
    },

    getColumnConfig(dtype: Dtype = "string", previous?: Partial<ColumnConfig>) {
        return SchemaUtils.normalizeColumnConfig(
            { optional: false, unique: false, primary_key: false, constraints: undefined, dtype },
            previous,
        );
    },

    Builder: {
        buildColumnsPayload(columnsConfig: ColumnDtype) {
            const raw = Object.fromEntries(
                Object.entries(columnsConfig).map(([column, config]) => {
                    return [column, SchemaUtils.normalizeColumnConfig(config, {})];
                }),
            );

            return ColumnDtypesSchema.safeParse(raw);
        },

        buildDtypesBySheet(sheetNames: string[], columnsConfig: ColumnDtype) {
            const sheets = sheetNames.length ? sheetNames : ["Sheet1"];
            return Object.fromEntries(sheets.map((sheet) => [sheet, columnsConfig]));
        },

        buildJsonSchema(
            tableName: string,
            projectId: string,
            schema: Schemas.Schema.JsonSchema,
            primaryKeys: string[],
        ): CreateTableFromJson {
            return {
                table_name: tableName,
                project_id: projectId,
                jsonschema: schema.payload,
                primary_keys: primaryKeys,
            };
        },
    },
};
