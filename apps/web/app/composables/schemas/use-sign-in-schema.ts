import { z } from "zod";

export default function () {
    const { t } = useI18n();

    const SignInSchema = computed(() =>
        z.object({
            email: z.email({ error: t("auth.validation.email_invalid") }),
            password: z.string().min(1, {
                error: t("common.validation.required"),
            }),
        }),
    );

    return { SignInSchema };
}
