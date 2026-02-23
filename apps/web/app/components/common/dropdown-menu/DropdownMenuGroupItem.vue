<script setup lang="ts">
    interface Props {
        group: Components.GenericDropdown.Item[];
    }

    defineProps<Props>();
</script>

<template>
    <DropdownMenuGroup>
        <template v-for="item in group" :key="item.label">
            <template v-if="item.sub">
                <DropdownMenuSub>
                    <DropdownMenuSubTrigger :disabled="toValue(item.disabled)">
                        <DropdownMenuItemContent :item="item" />
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
                    :disabled="toValue(item.disabled)"
                    :as-child="!!item.to"
                    @click="item.action"
                >
                    <DropdownMenuItemContent :item="item" />
                </DropdownMenuItem>
            </template>
        </template>
    </DropdownMenuGroup>
</template>
