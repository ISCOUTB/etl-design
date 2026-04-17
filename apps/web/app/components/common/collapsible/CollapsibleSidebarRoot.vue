<script setup lang="ts">
    import type { CollapsibleContentProps } from "reka-ui";
    import type { HTMLAttributes } from "vue";
    import { ChevronRight } from "lucide-vue-next";

    interface Props {
        item: MaybeRefOrGetter<Components.Sidebar.GroupCollapsibleKind>;
        contentProps?: CollapsibleContentProps & { class?: HTMLAttributes["class"] };
    }

    const props = withDefaults(defineProps<Props>(), {
        contentProps: undefined,
    });

    function filterCollapsibleItems(items: Components.Sidebar.GroupCollapsibleKindItem[]) {
        return items.filter((item) => !toValue(item.hidden));
    }

    const collapsible = computed(() => toValue(props.item));
    const collapsibleItems = computed(() =>
        filterCollapsibleItems(collapsible.value.collapsibleItems),
    );

    const open = useState(
        NuxtKeys.Sidebar.OpenCollapsible(collapsible.value),
        () => collapsible.value.defaultActive,
    );
    const animations = useCollapsibleAnimations();
</script>

<template>
    <Collapsible v-model:open="open" as-child class="group/collapsible">
        <SidebarMenuItem>
            <SidebarMenuButton
                class="cursor-pointer"
                :tooltip="$t(collapsible.label)"
                @click="collapsible.menuAction"
            >
                <component :is="collapsible.icon" v-if="collapsible.icon" />
                <span>{{ $t(collapsible.label) }}</span>
            </SidebarMenuButton>

            <template v-if="collapsible.collapsibleItems.length">
                <CollapsibleTrigger as-child>
                    <SidebarMenuAction class="data-[state=open]:rotate-90">
                        <ChevronRight />
                        <span class="sr-only">Toggle</span>
                    </SidebarMenuAction>
                </CollapsibleTrigger>

                <Transition :css="false" @enter="animations.onEnter" @leave="animations.onLeave">
                    <CollapsibleContent v-if="open" force-mount>
                        <SidebarMenuSub>
                            <SidebarMenuSubItem
                                v-for="subItem in collapsibleItems"
                                :key="`${collapsible.collapsibleItems.length.toString(32)}-${
                                    subItem.label
                                }`"
                            >
                                <SidebarMenuSubButton
                                    :as-child="!!subItem.to"
                                    class="cursor-pointer select-none"
                                    @click="subItem.action"
                                >
                                    <template v-if="subItem.to">
                                        <NuxtLink :to="subItem.to()">
                                            <component :is="subItem.icon" class="mr-2 h-4 w-4" />
                                            <span>{{ $t(subItem.label) }}</span>
                                        </NuxtLink>
                                    </template>
                                    <template v-else>
                                        <component :is="subItem.icon" class="mr-2 h-4 w-4" />
                                        <span>{{ $t(subItem.label) }}</span>
                                    </template>
                                </SidebarMenuSubButton>
                            </SidebarMenuSubItem>
                        </SidebarMenuSub>
                    </CollapsibleContent>
                </Transition>
            </template>
        </SidebarMenuItem>
    </Collapsible>
</template>
