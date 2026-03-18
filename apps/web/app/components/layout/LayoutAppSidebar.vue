<script setup lang="ts">
    import type { DropdownMenuContentProps } from "reka-ui";
    import type { SidebarProps } from "@/components/ui/sidebar";
    import { MoreHorizontal } from "lucide-vue-next";
    import { useSidebar } from "@/components/ui/sidebar";

    const props = withDefaults(defineProps<SidebarProps>(), {
        variant: "floating",
    });

    const { $localeRoute } = useNuxtApp();

    const { isMobile } = useSidebar();
    const dropdownSide = computed<DropdownMenuContentProps["side"]>(() => {
        if (isMobile.value) {
            return "bottom";
        }

        return "right";
    });
    const dropdownAlign = computed<DropdownMenuContentProps["align"]>(() => {
        if (isMobile.value) {
            return "end";
        }

        return "start";
    });

    function filterSidebarGroups(groups: Components.Sidebar.Group[]): Components.Sidebar.Group[] {
        return groups.map((group) => ({
            ...group,
            items: group.items.filter((item) => !toValue(item.hidden)),
        }));
    }

    const { sidebarContent } = useSidebarConfig();
    const filteredGroups = computed(() => filterSidebarGroups(sidebarContent.value));
</script>

<template>
    <Sidebar v-bind="props">
        <SidebarHeader>
            <SidebarMenu>
                <SidebarMenuItem>
                    <SidebarMenuButton size="lg" as-child>
                        <NuxtLink :to="$localeRoute({ name: 'index' })">
                            <div
                                class="aspect-square size-8 p-1 rounded-lg bg-muted dark:bg-gray-300"
                            >
                                <NuxtImg src="/icon.jpeg" />
                            </div>
                            <div class="grid flex-1 text-left text-sm leading-tight">
                                <span class="truncate font-medium">{{ $t("layouts.title") }}</span>
                                <span class="truncate text-xs">Framework</span>
                            </div>
                        </NuxtLink>
                    </SidebarMenuButton>
                </SidebarMenuItem>
            </SidebarMenu>
        </SidebarHeader>

        <SidebarContent as-child>
            <ScrollArea class="h-full">
                <template
                    v-for="(group, groupIndex) in filteredGroups"
                    :key="`group-${groupIndex}-${group.items.length}`"
                >
                    <SidebarGroup>
                        <SidebarGroupLabel v-if="group.title">
                            {{ $t(group.title) }}
                        </SidebarGroupLabel>

                        <SidebarMenu>
                            <template
                                v-for="(groupItem, groupItemIndex) in group.items"
                                :key="`${group.title}-${groupItem.kind}-${groupItemIndex}`"
                            >
                                <template v-if="groupItem.kind === 'collapsible'">
                                    <CollapsibleSidebarRoot :item="groupItem" />
                                </template>

                                <template v-if="groupItem.kind === 'action-button'">
                                    <DropdownSidebarMenuRoot
                                        :items="groupItem.dropdownItems"
                                        :content-props="{
                                            side: dropdownSide,
                                            align: dropdownAlign,
                                            class: 'min-w-56 rounded-lg',
                                        }"
                                    >
                                        <template #trigger>
                                            <SidebarMenuButton
                                                class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                                            >
                                                <component
                                                    :is="groupItem.icon"
                                                    v-if="groupItem.icon"
                                                />
                                                <span>{{ groupItem.label }}</span>
                                                <MoreHorizontal class="ml-auto" />
                                            </SidebarMenuButton>
                                        </template>
                                    </DropdownSidebarMenuRoot>
                                </template>

                                <template v-if="groupItem.kind === 'item'">
                                    <SidebarMenuItem class="cursor-pointer">
                                        <template v-if="groupItem.actionKind === 'navigation'">
                                            <SidebarMenuButton as-child>
                                                <NuxtLink :to="groupItem.to()">
                                                    <component
                                                        :is="groupItem.icon"
                                                        v-if="groupItem.icon"
                                                    />
                                                    <span>{{ $t(groupItem.label) }}</span>
                                                </NuxtLink>
                                            </SidebarMenuButton>
                                        </template>

                                        <template v-if="groupItem.actionKind === 'function'">
                                            <SidebarMenuButton @click="groupItem.action">
                                                <component
                                                    :is="groupItem.icon"
                                                    v-if="groupItem.icon"
                                                />
                                                <span>{{ $t(groupItem.label) }}</span>
                                            </SidebarMenuButton>
                                        </template>
                                    </SidebarMenuItem>
                                </template>
                            </template>
                        </SidebarMenu>
                    </SidebarGroup>
                </template>
            </ScrollArea>
        </SidebarContent>

        <SidebarFooter>
            <LayoutAppSidebarUser />
        </SidebarFooter>

        <SidebarRail />
    </Sidebar>
</template>
