import z from "zod";

export default function () {
    const { t } = useI18n();

    const EditTableSchema = computed(() =>
        z.object({
            tableName: z
                .string()
                .min(1, t("common.validation.required"))
                .regex(
                    /^[a-z_][a-z0-9_]*$/,
                    t("projects.id.tables.edit.validation.table_name_format"),
                ),
            columns: z
                .array(
                    z.object({
                        name: z
                            .string()
                            .min(1, t("common.validation.required"))
                            .regex(
                                /^[a-z_][a-z0-9_]*$/,
                                t("projects.id.tables.edit.validation.column_name_format"),
                            ),
                        type: z.enum(DtypesEnum.enum, {
                            error: "projects.id.tables.edit.validation.invalid_type",
                        }),
                        extra: z.record(z.string(), z.unknown()),
                    }),
                )
                .min(1, t("projects.id.tables.edit.validation.min_columns", { min: 1 })),
        }),
    );

    return { EditTableSchema };
}
