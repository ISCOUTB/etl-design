<script setup lang="ts">
    import { toast } from "vue-sonner";

    const email = useRouteQuery<string>("email", "");
    const { SignInSchema } = useSignInSchema();
    const { handleSubmit } = useForm({
        validationSchema: toTypedSchema(SignInSchema.value),
        initialValues: {
            email: email.value,
            password: "",
        },
    });

    const errorToast = useErrorToast();
    const router = useRouter();
    const auth = useAuth();
    const runtimeConfig = useRuntimeConfig();
    const { $localeRoute } = useNuxtApp();
    const callbackUrl = useRouteQuery("callbackUrl", runtimeConfig.public.homePageURL, {
        transform: (value) => {
            try {
                const parsed = new URL(value, runtimeConfig.public.homePageURL);
                return parsed.pathname + parsed.search + parsed.hash;
            } catch {
                if (value.startsWith("/")) {
                    return value;
                }

                return $localeRoute({ name: "index" });
            }
        },
    });
    const [loading] = useToggle(false);
    const onSubmit = handleSubmit((values) => {
        loading.value = true;

        auth.signIn("credentials", {
            email: values.email,
            password: values.password,
            redirect: false,
        })
            .then((response) => {
                if (response.error) {
                    errorToast.handle(response.error);
                    return;
                }

                if (response.ok) {
                    toast.success($t("auth.events.user_logged.title"), {
                        description: $t("auth.events.user_logged.description", {
                            email: values.email,
                        }),
                    });

                    router.push(callbackUrl.value);
                }
            })
            .finally(() => (loading.value = false));
    });
</script>

<template>
    <form @submit="onSubmit">
        <FieldGroup>
            <VeeField v-slot="{ field, errors }" name="email">
                <Field :data-invalid="!!errors.length">
                    <FieldLabel for="email">
                        {{ $t("auth.fields.email.label") }}
                    </FieldLabel>
                    <Input
                        id="email"
                        v-bind="field"
                        v-model="email"
                        type="email"
                        :placeholder="$t('auth.fields.email.placeholder')"
                        autocomplete="email"
                        :aria-invalid="!!errors.length"
                    />
                    <FieldError v-if="errors.length" :errors="errors" />
                </Field>
            </VeeField>

            <VeeField v-slot="{ field, errors }" name="password">
                <Field :data-invalid="!!errors.length">
                    <FieldLabel for="password">
                        {{ $t("auth.fields.password.label") }}
                    </FieldLabel>
                    <Input
                        id="password"
                        v-bind="field"
                        type="password"
                        :placeholder="$t('auth.fields.password.placeholder')"
                        autocomplete="current-password"
                        :aria-invalid="!!errors.length"
                    />
                    <FieldError v-if="errors.length" :errors="errors" />
                </Field>
            </VeeField>

            <Field>
                <Button :disabled="loading" type="submit">
                    <Spinner v-if="loading" />
                    {{ $t("auth.sign_in.submit") }}
                </Button>
            </Field>

            <FieldDescription>
                {{ $t("auth.sign_in.create_account") }}
                <NuxtLinkLocale
                    :to="{ name: 'auth-sign-up' }"
                    class="font-medium text-foreground underline underline-offset-4 transition-colors hover:text-foreground/80"
                >
                    {{ $t("auth.sign_in.sign_up_link") }}
                </NuxtLinkLocale>
            </FieldDescription>
        </FieldGroup>
    </form>
</template>
