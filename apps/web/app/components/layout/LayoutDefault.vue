<script setup>
    const { t, te } = useI18n();
    const route = useRoute();
    const head = useLocaleHead();
    const title = computed(() => {
        if (te(route.meta.title)) {
            return t(route.meta.title);
        }

        return t("layouts.title");
    });

    useHead(() => ({
        htmlAttrs: head.value.htmlAttrs,
        link: head.value.link,
        meta: head.value.meta,
        title: title.value,
    }));
</script>

<template>
    <div>
        <Html :lang="head.htmlAttrs.lang" :dir="head.htmlAttrs.dir">
            <Body>
                <slot />
            </Body>
        </Html>
    </div>
</template>
