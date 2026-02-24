<script setup lang="ts">
    import type { ClassValue } from "class-variance-authority/types";
    import type { DropdownMenuContentProps } from "reka-ui";
    import type { HTMLAttributes } from "vue";
    import { cn } from "@/lib/utils";

    interface Props {
        items: MaybeRefOrGetter<Components.GenericDropdown.Item[][]>;
        contentProps?: DropdownMenuContentProps & { class?: HTMLAttributes["class"] };
    }

    const props = withDefaults(defineProps<Props>(), {
        contentProps: undefined,
    });

    function filterDropdownItems(
        items: Components.GenericDropdown.Item[][],
    ): Components.GenericDropdown.Item[][] {
        return items
            .map((group) =>
                group.filter((item) => {
                    if (toValue(item.hidden)) {
                        return false;
                    }

                    if (item.sub) {
                        item.sub = filterDropdownItems(item.sub);
                    }

                    return true;
                }),
            )
            .filter((group) => group.length > 0);
    }

    const items = computed(() => toValue(props.items));
    const dropdownItems = computed(() => filterDropdownItems(items.value));
</script>

<template>
    <DropdownMenu>
        <SidebarMenuItem>
            <DropdownMenuTrigger as-child>
                <slot name="trigger" />
            </DropdownMenuTrigger>
            <DropdownMenuContent
                :class="cn('w-56', props.contentProps?.class as ClassValue)"
                v-bind="contentProps"
            >
                <slot name="dropdown-header" />
                <template v-for="(group, index) in dropdownItems" :key="group.length.toString(32)">
                    <DropdownMenuGroupItem :group="group" />
                    <DropdownMenuSeparator v-if="index < dropdownItems.length - 1" />
                </template>
            </DropdownMenuContent>
        </SidebarMenuItem>
    </DropdownMenu>
</template>
