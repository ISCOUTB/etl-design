<script setup lang="ts">
    definePageMeta({
        title: "layouts.title",
        layout: "sidebar",
        i18n: {
            paths: {
                en: "/",
            },
        },
    });

    const { locale } = useI18n();

    useSeoMeta({
        ogType: "website",
        description: () => $t("layouts.description"),
        ogTitle: () => $t("layouts.title"),
        ogDescription: () => $t("layouts.description"),
        ogLocale: () => locale.value.replace("-", "_"),
        robots: "index, follow",
    });

    const routeError = useRouteError();
    onMounted(() => routeError.onToast());
</script>

<template>
    <div>
        Lorem ipsum dolor sit amet consectetur adipisicing elit. Vitae maxime molestias provident
        esse earum ratione, sint magnam architecto officiis rem aliquid, impedit, nam consequatur
        similique debitis perspiciatis numquam eius laudantium!
    </div>
</template>
