import type {
    JsonSchema as _JsonSchema,
    JsonSchemaPropertyConstraints as _JsonSchemaPropertyConstraints,
    ColumnDtypesSchema,
    CreateTableFromJsonSchema,
    DtypesEnum,
    MongoRawSchema,
    ResponseProjectSchema,
    SpreadsheetDtypesSchema,
} from "#shared/utils/schemas/api";
import type { z } from "zod";

export type ColumnConfig = z.infer<typeof SpreadsheetDtypesSchema>;
export type Dtype = z.infer<typeof DtypesEnum>;
export type ResponseProject = z.infer<typeof ResponseProjectSchema>;
export type ColumnDtype = z.infer<typeof ColumnDtypesSchema>;
export type CreateTableFromJson = z.infer<typeof CreateTableFromJsonSchema>;
export type MongoRaw = z.infer<typeof MongoRawSchema>;
export type JsonSchema = z.infer<typeof _JsonSchema>;
export type JsonSchemaPropertyConstraints = z.infer<typeof _JsonSchemaPropertyConstraints>;
