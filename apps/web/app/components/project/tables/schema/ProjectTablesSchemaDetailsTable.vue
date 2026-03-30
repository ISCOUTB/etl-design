<script setup lang="ts">
    import type { Dtype, JsonSchemaPropertyConstraints } from "#shared/utils/schemas/types";
    import type { HTMLAttributes } from "vue";
    import { Fingerprint, Key } from "lucide-vue-next";
    import { cn } from "~/lib/utils";

    interface Props {
        properties: [string, JsonSchemaPropertyConstraints & { type: Dtype }][];
    }

    interface ColumnBadge {
        icon?: Components.LucideIconComponent;
        label: string;
        class: HTMLAttributes["class"];
    }

    defineProps<Props>();

    function makeBadges(config: JsonSchemaPropertyConstraints): ColumnBadge[] {
        const badges: ColumnBadge[] = [];

        if (config.primary_key) {
            badges.push({
                label: "Primary",
                icon: Key,
                class: TableUtils.getPropertiesColor("primary"),
            });
        }

        if (config.unique && !config.primary_key) {
            badges.push({
                label: "Unique",
                icon: Fingerprint,
                class: TableUtils.getPropertiesColor("unique"),
            });
        }

        if (config.optional) {
            badges.push({ label: "Optional", class: TableUtils.getPropertiesColor("optional") });
        }

        return badges;
    }
</script>

<template>
    <div class="rounded-lg border">
        <Table>
            <TableHeader>
                <TableRow>
                    <TableCell class="px-4 py-2">Column </TableCell>
                    <TableCell class="px-4 py-2">Type </TableCell>
                    <TableCell class="px-4 py-2">Constraints </TableCell>
                </TableRow>
            </TableHeader>
            <TableBody>
                <template v-for="[column, config] in properties" :key="column">
                    <TableRow>
                        <TableCell class="px-4 font-mono text-sm text-foreground">
                            {{ column }}
                        </TableCell>
                        <TableCell class="flex items-center space-x-2">
                            <div
                                :class="
                                    cn(
                                        'flex size-6 items-center justify-center rounded',
                                        TableUtils.getColor(config.type),
                                    )
                                "
                            >
                                <component :is="TableUtils.getIcon(config.type)" class="size-3.5" />
                            </div>
                            <span class="text-sm text-muted-foreground">
                                {{ config.type }}
                            </span>
                        </TableCell>
                        <TableCell>
                            <div class="w-full h-full flex flex-wrap items-center gap-1.5">
                                <Badge
                                    v-for="badge in makeBadges({
                                        primary_key: config.primary_key || false,
                                        unique: config.unique || false,
                                        optional: config.optional || false,
                                    })"
                                    :key="badge.label"
                                    variant="outline"
                                    :class="cn(badge.class)"
                                >
                                    <component :is="badge.icon" v-if="badge.icon" />
                                    {{ badge.label }}
                                </Badge>
                            </div>
                        </TableCell>
                    </TableRow>
                </template>
            </TableBody>
        </Table>
    </div>
</template>
