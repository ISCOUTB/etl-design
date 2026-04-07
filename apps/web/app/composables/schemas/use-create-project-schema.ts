import { z } from "zod";

export default function () {
    const { t } = useI18n();

    const CreateProjectSchema = computed(() =>
        z.object({
            name: z.string().min(1, {
                error: t("projects.create.validation.name_empty"),
            }),
            description: z.string().nullable(),
            provider: z.string().nullable(),
            dbHost: z.string().nullable(),
            dbPort: z
                .string()
                .nullable()
                .transform((value) => {
                    if (value === null || value?.trim() === "") {
                        return null;
                    }

                    return value;
                })
                .refine((value) => value === null || /^\d+$/.test(value), {
                    error: t("projects.create.validation.port_number"),
                }),
            dbUser: z.string().nullable(),
            dbPassword: z.string().nullable(),
            dbName: z.string().nullable(),
            dbParams: z.string().nullable(),
        }),
    );

    return { CreateProjectSchema };
}
