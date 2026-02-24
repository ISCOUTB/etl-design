<script setup lang="ts">
    import type { ResponseProjectSchema } from "#shared/utils/schemas/api";
    import type { z } from "zod";
    import { Edit, ExternalLink, MoreHorizontal, Trash } from "lucide-vue-next";

    interface Props {
        project: z.infer<typeof ResponseProjectSchema>;
    }

    defineProps<Props>();

    const { $localeRoute } = useNuxtApp();
    const items = computed<Components.GenericDropdown.Item[][]>(() => [
        [
            {
                label: "projects.view.dropdown.view.label",
                icon: ExternalLink,
                to: () => $localeRoute({ name: "index" }),
            },
            {
                label: "projects.view.dropdown.edit.label",
                icon: Edit,
                to: () => $localeRoute({ name: "index" }),
            },
        ],
        [
            {
                label: "projects.view.dropdown.delete.label",
                icon: Trash,
                to: () => $localeRoute({ name: "index" }),
            },
        ],
    ]);
</script>

<template>
    <DropdownMenuRoot :items="items" :content-props="{ align: 'end' }">
        <template #trigger>
            <Button variant="ghost" class="size-8 p-0">
                <MoreHorizontal class="size-4" />
            </Button>
        </template>
    </DropdownMenuRoot>
</template>
