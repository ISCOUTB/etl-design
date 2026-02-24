<script setup lang="ts">
    const modal = useModal();
</script>

<template>
    <LayoutDefault>
        <SidebarProvider>
            <LayoutAppSidebar collapsible="icon" />

            <SidebarInset>
                <header
                    class="sticky top-0 z-10 flex h-16 shrink-0 items-center backdrop-blur-sm bg-background/80 border-b border-border/10 rounded-t-xl"
                >
                    <div class="flex justify-between grow px-4">
                        <div class="flex space-x-2 items-center">
                            <SidebarTrigger class="-ml-1" />
                            <Separator
                                orientation="vertical"
                                class="mr-2 data-[orientation=vertical]:h-4"
                            />
                        </div>
                        <div class="flex space-x-2 items-center pointer-events-auto">
                            <SettingsLocale :content-props="{ side: 'bottom', align: 'end' }" />
                            <SettingsColorMode :content-props="{ side: 'bottom', align: 'end' }" />
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
    </LayoutDefault>
</template>
