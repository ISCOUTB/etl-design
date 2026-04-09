import { z } from "zod";

export const ApiErrorSchema = z.looseObject({
    error: z.string(),
    message: z.string(),
});

const _PaginatedResponseObject = z.object({
    total: z.coerce.number().int(),
    page: z.coerce.number().int(),
    limit: z.coerce.number().int(),
    total_pages: z.coerce.number().int(),
    has_prev: z.boolean(),
    has_next: z.boolean(),
});

export function PaginatedResponse<T extends z.ZodType>(object: T) {
    return _PaginatedResponseObject.extend({ items: z.array(object) });
}

const _ApiResponseObject = z.object({
    status: z.string(),
    code: z.coerce.number().int(),
    message: z.string(),
});

export function ApiResponse(): z.ZodObject<
    Prettify<typeof _ApiResponseObject.shape & { data: z.ZodRecord<z.ZodString, z.ZodString> }>
>;
export function ApiResponse<T extends z.ZodType>(
    object: T,
): z.ZodObject<Prettify<typeof _ApiResponseObject.shape & { data: T }>>;
export function ApiResponse<T extends z.ZodType>(object?: T) {
    const schema = object ?? z.record(z.string(), z.string());
    return _ApiResponseObject.extend({ data: schema });
}

export const BaseProjectSchema = z.object({
    name: z.string().min(1),
    description: z.string().nullable().default(null),
    provider: z.string().nullable().default(null),
    db_host: z.string().nullable().default(null),
    db_port: z.number().int().nullable().default(null),
    db_user: z.string().nullable().default(null),
    db_password: z.string().nullable().default(null),
    db_name: z.string().nullable().default(null),
    db_params: z.string().nullable().default(null),
});

export const ResponseProjectSchema = z
    .object({
        id: z.string(),
        created_at: z.iso.datetime({ offset: true }),
        updated_at: z.iso.datetime({ offset: true }),
    })
    .extend(BaseProjectSchema.shape);

export const DtypesEnum = z.enum(["string", "integer", "float", "double", "boolean"]);

export const BaseNumberConstraints = z
    .object({
        minimum: z.number().optional(),
        maximum: z.number().optional(),
        exclusive_minimum: z.boolean().default(false),
        exclusive_maximum: z.boolean().default(false),
        multiple_of: z.number().optional(),
    })
    .superRefine((value, ctx) => {
        if (
            value.minimum !== undefined &&
            value.maximum !== undefined &&
            value.minimum > value.maximum
        ) {
            ctx.addIssue({
                code: "custom",
                message: "minimum cannot be higher than maximum",
                path: ["minimum"],
            });
        }

        if (value.multiple_of !== undefined && value.multiple_of <= 0) {
            ctx.addIssue({
                code: "custom",
                message: "multipleof must be higher than 0",
                path: ["multiple_of"],
            });
        }
    });

export const NumberConstraints = BaseNumberConstraints;

export const IntegerConstraints = BaseNumberConstraints.safeExtend({
    minimum: z.number().int().optional(),
    maximum: z.number().int().optional(),
    multiple_of: z.number().int().optional(),
});

export const FloatConstraints = BaseNumberConstraints;

export const StringConstraints = z
    .object({
        min_length: z.number().int().nonnegative().optional(),
        max_length: z.number().int().nonnegative().optional(),
        pattern: z.string().optional(),
    })
    .superRefine((value, ctx) => {
        if (
            value.min_length !== undefined &&
            value.max_length !== undefined &&
            value.min_length > value.max_length
        ) {
            ctx.addIssue({
                code: "custom",
                message: "min_length cannot be higher than max_length",
                path: ["min_length"],
            });
        }
    });

const SpreadSheetCommon = z.object({
    unique: z.boolean().default(false),
    optional: z.boolean().default(false),
    primary_key: z.boolean().default(false),
});

export const SpreadsheetDtypesSchema = z.discriminatedUnion("dtype", [
    SpreadSheetCommon.extend({
        dtype: z.literal("integer"),
        constraints: IntegerConstraints.optional(),
    }),
    SpreadSheetCommon.extend({
        dtype: z.literal("float"),
        constraints: FloatConstraints.optional(),
    }),
    SpreadSheetCommon.extend({
        dtype: z.literal("double"),
        constraints: FloatConstraints.optional(),
    }),
    SpreadSheetCommon.extend({
        dtype: z.literal("string"),
        constraints: StringConstraints.optional(),
    }),
    SpreadSheetCommon.extend({
        dtype: z.literal("boolean"),
        constraints: z.undefined().optional(),
    }),
]);

export const ColumnDtypesSchema = z.record(z.string(), SpreadsheetDtypesSchema);

export const JsonSchemaPropertyConstraints = z.object({
    unique: z.coerce.boolean().optional(),
    optional: z.coerce.boolean().optional(),
    primary_key: z.coerce.boolean().optional(),
});

export const JsonSchema = z.preprocess(
    (data) => {
        if (typeof data === "object" && data !== null) {
            const object = data as any;

            if (object.schema && !object.$schema) {
                object.$schema = object.schema;
            }

            return object;
        }

        return data;
    },
    z.object({
        $schema: z.string(),
        type: z.literal("object"),
        required: z.array(z.string()),
        properties: z.record(
            z.string(),
            z
                .object({
                    type: DtypesEnum,
                })
                .extend(JsonSchemaPropertyConstraints.shape)
                .catchall(z.unknown()),
        ),
    }),
);

export const CreateTableFromJsonSchema = z.object({
    table_name: z.string(),
    project_id: z.string(),
    jsonschema: JsonSchema,
    primary_keys: z.array(z.string()),
});

export const MongoRawSchema = z.object({
    id: z.string(),
    import_name: z.string(),
    created_at: z.iso.datetime({ offset: true }),
    active_schema: JsonSchema,
    schemas_releases: z.array(
        z.object({
            created_at: z.iso.datetime({ offset: true }),
            schema: JsonSchema,
        }),
    ),
});

export const MongoGetSchemasResponse = z.object({ schemas: z.array(MongoRawSchema) });

export const API_CONSTANTS = {
    TASK: {
        VALIDATION_TASK: "validation",
        INSERTION_TASK: "insertion",
    },
} as const;

export const ProjectTask = ApiResponse(
    z
        .object({
            task_id: z.string(),
            project_id: z.string(),
            import_name: z.string(),
            error: z.string().optional(),
            upload_date: z.string(),
            update_date: z.string(),
        })
        .catchall(z.unknown()),
);

export const ProjectTaskResponse = z.array(ProjectTask);
