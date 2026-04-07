<script setup lang="ts">
    const auth = useAuth();

    const open = useCookie(NuxtKeys.Sidebar.CookieOpen, {
        default: () => false,
    });
</script>

<template>
    <LayoutDefault>
        <SidebarProvider v-model:open="open">
            <LayoutAppSidebar collapsible="icon" />

            <SidebarInset>
                <header
                    class="sticky top-0 z-10 flex h-16 shrink-0 items-center backdrop-blur-sm bg-background/80 border-b border-border/10 rounded-t-xl"
                >
                    <div class="flex justify-between grow px-4">
                        <div class="flex items-center space-x-3">
                            <SidebarTrigger class="-ml-1" />
                            <Separator
                                orientation="vertical"
                                class="data-[orientation=vertical]:h-4"
                            />
                            <LayoutBreadcrumbs />
                        </div>

                        <div class="flex space-x-2">
                            <template v-if="auth.status.value === 'unauthenticated'">
                                <LayoutAuthButtons />
                            </template>

                            <div class="flex space-x-2 items-center pointer-events-auto">
                                <SettingsLocale :content-props="{ side: 'bottom', align: 'end' }" />
                                <SettingsColorMode
                                    :content-props="{ side: 'bottom', align: 'end' }"
                                />
                            </div>
                        </div>
                    </div>
                </header>

                <LayoutPageContainer>
                    <LayoutModal />
                    <slot />
                </LayoutPageContainer>
            </SidebarInset>
        </SidebarProvider>
    </LayoutDefault>
</template>
