<script setup lang="ts">
    definePageMeta({
        title: "projects.create.header.title",
        layout: "sidebar",
        i18n: {
            paths: {
                en: "/projects/create",
            },
        },
    });

    const { locale } = useI18n();

    useSeoMeta({
        ogType: "website",
        description: () => $t("projects.create.header.description"),
        ogTitle: () => $t("projects.create.header.title"),
        ogDescription: () => $t("projects.create.header.description"),
        ogLocale: () => locale.value.replace("-", "_"),
        robots: "noindex, nofollow",
    });
</script>

<template>
    <div>
        <ProjectCreateForm class="mx-auto w-full max-w-5xl" />
        <div class="my-6" />
    </div>
</template>
