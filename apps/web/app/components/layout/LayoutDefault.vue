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
    const modal = useModal();
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
                <SidebarProvider>
                    <LayoutAppSidebar collapsible="icon" />

                    <SidebarInset>
                        <header class="flex h-16 shrink-0 items-center">
                            <div class="flex justify-between grow px-4">
                                <div class="flex space-x-2 items-center">
                                    <SidebarTrigger class="-ml-1" />
                                    <Separator
                                        orientation="vertical"
                                        class="mr-2 data-[orientation=vertical]:h-4"
                                    />
                                </div>
                                <div class="flex space-x-2 items-center pointer-events-auto">
                                    <SettingsLocale
                                        :content-props="{ side: 'bottom', align: 'end' }"
                                    />
                                    <SettingsColorMode
                                        :content-props="{ side: 'bottom', align: 'end' }"
                                    />
                                </div>
                            </div>
                        </header>

                        <LayoutPageContainer>
                            <Sheet
                                v-if="modal.currentComponent && modal.open.value"
                                v-model:open="modal.open.value"
                            >
                                <component
                                    :is="modal.currentComponent.value"
                                    v-if="modal.currentComponent.value"
                                    v-bind="modal.componentProps.value"
                                />
                            </Sheet>

                            <slot />
                        </LayoutPageContainer>
                    </SidebarInset>
                </SidebarProvider>
            </Body>
        </Html>
    </div>
</template>
