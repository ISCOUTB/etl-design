<script setup lang="ts">
    definePageMeta({
        title: "Projects ID",
        i18n: {
            paths: {
                en: "/projects/[id]",
            },
        },
    });

    const route = useRoute();
    const setI18nParams = useSetI18nParams();
    setI18nParams({ en: { id: route.params.id } });
</script>

<template>
    <div>
        {{ route.params.id }}
    </div>
</template>
