<script setup lang="ts" generic="TContext">
    interface Props<T> {
        group: Components.GenericDropdown.Item<T>[];
        context?: MaybeRefOrGetter<T>;
    }

    const props = defineProps<Props<TContext>>();
    const context = computed(() => toValue(props.context));

    function resolveDisabled(item: Components.GenericDropdown.Item<TContext>) {
        if (item.disabled) {
            if (typeof item.disabled === "function") {
                return item.disabled(context.value);
            }

            return toValue(item.disabled);
        }
    }

    function handleAction(item: Components.GenericDropdown.Item<TContext>) {
        if (item.action) {
            item.action(context.value);
        }
    }
</script>

<template>
    <DropdownMenuGroup>
        <template v-for="item in group" :key="item.label">
            <template v-if="item.sub">
                <DropdownMenuSub>
                    <DropdownMenuSubTrigger :disabled="resolveDisabled(item)">
                        <DropdownMenuItemContent :context="context" :item="item" />
                    </DropdownMenuSubTrigger>
                    <DropdownMenuPortal>
                        <DropdownMenuSubContent class="w-48">
                            <template v-for="(_group, index) in item.sub" :key="_group">
                                <DropdownMenuGroupItem :group="_group" />
                                <DropdownMenuSeparator v-if="index < item.sub.length - 1" />
                            </template>
                        </DropdownMenuSubContent>
                    </DropdownMenuPortal>
                </DropdownMenuSub>
            </template>
            <template v-else>
                <DropdownMenuItem
                    :disabled="resolveDisabled(item)"
                    :as-child="!!item.to"
                    @click="handleAction(item)"
                >
                    <DropdownMenuItemContent :context="context" :item="item" />
                </DropdownMenuItem>
            </template>
        </template>
    </DropdownMenuGroup>
</template>
