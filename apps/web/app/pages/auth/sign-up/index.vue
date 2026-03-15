<script setup lang="ts">
    definePageMeta({
        title: "auth.sign_up.title",
        auth: { unauthenticatedOnly: true, navigateAuthenticatedTo: "/" },
        i18n: {
            paths: {
                en: "/auth/sign-up",
            },
        },
    });

    useSeoMeta({
        title: $t("auth.sing_up.title"),
        description: $t("auth.sign_up.subtitle"),
        ogType: "website",
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
                    <AuthSignUpForm />
                </CardContent>
            </Card>
            <div class="flex justify-end space-x-2">
                <SettingsLocale />
                <SettingsColorMode :content-props="{ side: 'bottom', align: 'end' }" />
            </div>
        </div>
    </div>
</template>
