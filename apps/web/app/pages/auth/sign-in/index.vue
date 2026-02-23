<script setup lang="ts">
    import { toast } from "vue-sonner";

    definePageMeta({
        title: "auth.sign_in.title",
        auth: { unauthenticatedOnly: true, navigateAuthenticatedTo: "/" },
    });

    const { SignInSchema } = useSignInSchema();
    const { handleSubmit } = useForm({
        validationSchema: toTypedSchema(SignInSchema.value),
        initialValues: {
            email: "",
            password: "",
        },
    });

    const errorToast = useServerErrorToast();
    const router = useRouter();
    const auth = useAuth();
    const runtimeConfig = useRuntimeConfig();
    const { $localeRoute } = useNuxtApp();
    const email = useRouteQuery<string>("email", "");
    const callbackUrl = useRouteQuery("callbackUrl", runtimeConfig.public.homePageURL, {
        transform: (value) => {
            try {
                const parsed = new URL(value, runtimeConfig.public.homePageURL);
                return parsed.pathname + parsed.search + parsed.hash;
            } catch {
                if (value.startsWith("/")) {
                    return value;
                }

                return $localeRoute({ path: "/" });
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
                            {{ $t("auth.sign_in.title") }}
                        </h2>
                        <p class="mt-2 text-sm text-muted-foreground">
                            {{ $t("auth.sign_in.subtitle") }}
                        </p>
                    </CardDescription>
                </CardHeader>
                <CardContent>
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
                                <NuxtLink
                                    :to="$localePath({ path: '/auth/sign-up' })"
                                    class="font-medium text-foreground underline underline-offset-4 transition-colors hover:text-foreground/80"
                                >
                                    {{ $t("auth.sign_in.sign_up_link") }}
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
