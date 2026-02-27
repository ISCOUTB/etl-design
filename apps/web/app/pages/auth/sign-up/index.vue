<script setup lang="ts">
    import { ResponseCodesRecord } from "#shared/utils/response-codes";
    import { ApiErrorSchema } from "#shared/utils/schemas/api";
    import { UserResponse } from "#shared/utils/schemas/auth";
    import { FetchError } from "ofetch";
    import { toast } from "vue-sonner";

    definePageMeta({
        title: "auth.sign_up.title",
        auth: { unauthenticatedOnly: true, navigateAuthenticatedTo: "/" },
        i18n: {
            paths: {
                en: "/auth/sign-up",
            },
        },
    });

    const { SignUpSchema } = useSignUpSchema();
    const { handleSubmit } = useForm({
        validationSchema: toTypedSchema(SignUpSchema.value),
        initialValues: {
            name: "",
            email: "",
            password: "",
            confirm: "",
        },
    });

    const errorToast = useErrorToast();
    const api = useApi();
    const { $localeRoute } = useNuxtApp();
    const router = useRouter();
    const [loading] = useToggle(false);
    const onSubmit = handleSubmit((values) => {
        const formData = new FormData();
        formData.append("username", values.name);
        formData.append("email", values.email);
        formData.append("password", values.password);

        loading.value = true;
        api("/auth/sign-up", {
            method: "POST",
            body: formData,
        })
            .then((response) => {
                const parsedResponse = UserResponse.safeParse(response);

                if (!parsedResponse.success) {
                    throw createError({});
                }

                toast.success($t("auth.events.user_created.title"), {
                    description: $t("auth.events.user_created.description", {
                        email: parsedResponse.data.email,
                    }),
                });

                router.push(
                    $localeRoute({
                        name: "auth-sign-in",
                        query: { email: parsedResponse.data.email },
                    }),
                );
            })
            .catch((error) => {
                if (error instanceof FetchError) {
                    const parsedError = ApiErrorSchema.safeParse(error.data);
                    if (!parsedError.success) {
                        errorToast.handle(ResponseCodesRecord.Server.UnknownError);

                        return;
                    }

                    errorToast.handle(parsedError.data.error);
                }
            })
            .finally(() => (loading.value = false));
    });
</script>

<template>
    <div class="flex flex-col min-h-svh items-center justify-center px-4 py-12">
        <div class="w-full max-w-md overflow-hidden space-y-2">
            <Card>
                <CardHeader class="items-center px-6 pt-8 pb-4 text-center sm:px-8">
                    <CardTitle
                        class="text-center font-mono text-3xl font-bold tracking-[0.2em] text-foreground sm:text-4xl"
                    >
                        S.L.O.T.H
                    </CardTitle>
                    <CardDescription class="w-full pt-3 text-center">
                        <h2 class="text-xl font-semibold uppercase tracking-wide text-foreground">
                            {{ $t("auth.sign_up.title") }}
                        </h2>
                        <p class="mt-2 text-sm text-muted-foreground">
                            {{ $t("auth.sign_up.subtitle") }}
                        </p>
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form @submit="onSubmit">
                        <FieldGroup>
                            <VeeField v-slot="{ field, errors }" name="name">
                                <Field :data-invalid="!!errors.length">
                                    <FieldLabel for="name">
                                        {{ $t("auth.fields.username.label") }}
                                    </FieldLabel>
                                    <Input
                                        id="name"
                                        v-bind="field"
                                        :placeholder="$t('auth.fields.username.placeholder')"
                                        autocomplete="name"
                                        :aria-invalid="!!errors.length"
                                    />
                                    <FieldError v-if="errors.length" :errors="errors" />
                                </Field>
                            </VeeField>

                            <VeeField v-slot="{ field, errors }" name="email">
                                <Field :data-invalid="!!errors.length">
                                    <FieldLabel for="email">
                                        {{ $t("auth.fields.email.label") }}
                                    </FieldLabel>
                                    <Input
                                        id="email"
                                        type="email"
                                        v-bind="field"
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

                            <VeeField v-slot="{ field, errors }" name="confirm">
                                <Field :data-invalid="!!errors.length">
                                    <FieldLabel for="confirm">
                                        {{ $t("auth.fields.confirm_password.label") }}
                                    </FieldLabel>
                                    <Input
                                        id="confirm"
                                        v-bind="field"
                                        type="password"
                                        :placeholder="
                                            $t('auth.fields.confirm_password.placeholder')
                                        "
                                        autocomplete="current-password"
                                        :aria-invalid="!!errors.length"
                                    />
                                    <FieldError v-if="errors.length" :errors="errors" />
                                </Field>
                            </VeeField>

                            <Field>
                                <Button :disabled="loading" type="submit">
                                    <Spinner v-if="loading" />
                                    {{ $t("auth.sign_up.submit") }}
                                </Button>
                            </Field>

                            <FieldDescription>
                                {{ $t("auth.sign_up.has_account") }}
                                <NuxtLink
                                    :to="$localeRoute({ name: 'auth-sign-in' })"
                                    class="font-medium text-foreground underline underline-offset-4 transition-colors hover:text-foreground/80"
                                >
                                    {{ $t("auth.sign_up.sign_in_link") }}
                                </NuxtLink>
                            </FieldDescription>
                        </FieldGroup>
                    </form>
                </CardContent>
            </Card>
            <div class="flex justify-end space-x-2">
                <SettingsLocale />
                <SettingsColorMode :content-props="{ side: 'bottom', align: 'end' }" />
            </div>
        </div>
    </div>
</template>
