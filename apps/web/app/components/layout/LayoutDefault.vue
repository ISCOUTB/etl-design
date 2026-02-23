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
</script>

<template>
    <div>
        <Html :lang="head.htmlAttrs.lang" :dir="head.htmlAttrs.dir">
            <Head>
                <Title>{{ title }}</Title>
                <template v-for="link in head.link" :key="link.key">
                    <Link
                        :id="link.key"
                        :rel="link.rel"
                        :href="link.href"
                        :hreflang="link.hreflang"
                    />
                </template>
                <template v-for="meta in head.meta" :key="meta.key">
                    <Meta :id="meta.key" :property="meta.property" :content="meta.content" />
                </template>
            </Head>
            <Body>
                <slot />
            </Body>
        </Html>
    </div>
</template>
