import { z } from "zod";

export default function () {
    const { t } = useI18n();
    const config = useAppConfig();

    const SignUpSchema = computed(() =>
        z
            .object({
                name: z.string().min(5, { error: t("auth.validation.name_min", { length: 5 }) }),
                email: z.email({ error: t("auth.validation.email_invalid") }),
                password: z
                    .string()
                    .min(config.auth.validation.minPasswordLength, {
                        error: t("auth.validation.password_min", {
                            length: config.auth.validation.minPasswordLength,
                        }),
                    })
                    .max(config.auth.validation.maxPasswordLength, {
                        error: t("common.validation.max_length", {
                            max: config.auth.validation.maxPasswordLength,
                        }),
                    }),
                confirm: z.string().min(1, { error: t("common.validation.required") }),
            })
            .refine((data) => data.password === data.confirm, {
                error: t("auth.validation.passwords_mismatch"),
                path: ["confirm"],
            }),
    );

    return { SignUpSchema };
}
