<script setup lang="ts">
    definePageMeta({
        title: "projects.create.header.title",
        layout: "sidebar",
        middleware: ["sidebase-auth"],
        i18n: {
            paths: {
                en: "/projects/create",
                es: "/proyectos/crear",
            },
        },
        breadcrumb: {
            options: {
                parent: {
                    kind: "link",
                },
            },
        },
    });

    const { locale } = useI18n();
    const {
        public: { homePageURL },
    } = useRuntimeConfig();

    useSeoMeta({
        description: () => $t("projects.create.header.description"),

        ogImage: () => `${homePageURL}/icon.jpeg`,
        twitterImage: () => `${homePageURL}/icon.jpeg`,

        ogType: "website",
        ogTitle: () => $t("projects.create.header.title"),
        ogDescription: () => $t("projects.create.header.description"),
        ogLocale: () => locale.value.replace("-", "_"),
        ogSiteName: () => $t("layouts.title"),

        twitterCard: "summary_large_image",
        twitterTitle: () => $t("projects.create.header.title"),
        twitterDescription: () => $t("projects.create.header.description"),

        robots: "noindex, nofollow",
    });
</script>

<template>
    <div>
        <ProjectCreateForm class="mx-auto w-full max-w-5xl" />
        <div class="my-6" />
    </div>
</template>
