import { z } from "zod";

export default function () {
    const { t } = useI18n();

    const EditTableSchema = computed(() =>
        z.object({
            tableName: z.string().min(1, t("common.validation.required")),
            columns: z
                .array(
                    z.object({
                        name: z.string().min(1, t("common.validation.required")),
                        type: z.enum(DtypesEnum.enum, {
                            error: "projects.id.tables.edit.validation.invalid_type",
                        }),
                        optional: z.boolean(),
                        unique: z.boolean(),
                        primary_key: z.boolean(),
                    }),
                )
                .min(1, t("projects.id.tables.edit.validation.min_columns", { min: 1 }))
                .superRefine((columns, context) => {
                    const names = columns.map((column) => column.name.toLowerCase().trim());

                    columns.forEach((column, index) => {
                        const duplicated =
                            names.indexOf(column.name.toLocaleLowerCase().trim()) !== index;

                        if (duplicated && column.name.length > 0) {
                            context.addIssue({
                                code: "custom",
                                message: t("projects.id.tables.edit.validation.duplicated_column"),
                                path: [index, "name"],
                            });
                        }
                    });
                }),
        }),
    );

    return { EditTableSchema };
}
