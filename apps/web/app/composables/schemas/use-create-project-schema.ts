import { z } from "zod";

export default function () {
    const { t } = useI18n();

    const CreateProjectSchema = computed(() =>
        z.object({
            name: z.string().min(1, {
                error: t("projects.create.validation.name_empty"),
            }),
            description: z.string().optional(),
            provider: z.string().optional(),
            dbHost: z.string().optional(),
            dbPort: z.coerce
                .number()
                .transform((value) => value.toString())
                .optional(),
            dbUser: z.string().optional(),
            dbPassword: z.string().optional(),
            dbName: z.string().optional(),
            dbParams: z.string().optional(),
        }),
    );

    return { CreateProjectSchema };
}
