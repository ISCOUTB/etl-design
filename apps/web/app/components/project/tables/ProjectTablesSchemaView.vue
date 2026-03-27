<script setup lang="ts">
    import type { HTMLAttributes } from "vue";
    import { ArrowLeft, Clock, Fingerprint, Key, Pencil, Table2 } from "lucide-vue-next";
    import { cn } from "~/lib/utils";

    interface Props {
        schema: MaybeRefOrGetter<MongoRaw | undefined>;
        project: MaybeRefOrGetter<ResponseProject | undefined>;
    }

    interface ColumnBadge {
        icon?: Components.LucideIconComponent;
        label: string;
        class: HTMLAttributes["class"];
    }

    const props = defineProps<Props>();

    const schema = computed(() => toValue(props.schema));
    const project = computed(() => toValue(props.project));

    const tableName = computed(() => {
        if (!schema.value) {
            return;
        }

        return TableUtils.getTableName(schema.value.import_name);
    });

    const properties = computed(() => {
        if (!schema.value) {
            return;
        }

        return Object.entries(schema.value.active_schema.properties);
    });

    const events = useAppEvents();
    function handleBack(_event: Event) {
        events.emit("event:projects:table:change-view", { value: "overview" });
    }

    function makeBadges(
        config: Pick<ColumnConfig, "primary_key" | "unique" | "optional">,
    ): ColumnBadge[] {
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
    <div class="flex flex-col space-y-6">
        <div class="flex items-center gap-4">
            <Button variant="ghost" size="icon" class="shrink-0" @click="handleBack">
                <ArrowLeft class="size-4" />
                <span class="sr-only">Back to tables</span>
            </Button>
            <div class="min-w-0 flex-1">
                <div class="flex items-center gap-3">
                    <div
                        class="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10"
                    >
                        <Table2 class="size-5 text-primary" />
                    </div>
                    <div>
                        <h2 class="text-lg font-medium text-foreground">
                            {{ tableName }}
                        </h2>
                        <p class="text-xs text-muted-foreground font-mono">
                            {{ schema?.id }}
                        </p>
                    </div>
                </div>
            </div>
            <Button v-if="project" variant="outline" as-child>
                <NuxtLink
                    :to="
                        $localePath({
                            name: 'projects-id-tables-tableName-edit',
                            params: { id: project.id, tableName },
                            query: {
                                callbackUrl: $route.fullPath,
                            },
                        })
                    "
                >
                    <Pencil class="size-4" />
                    Edit Schema
                </NuxtLink>
            </Button>
        </div>

        <Card v-if="schema" class="overflow-hidden">
            <CardHeader>
                <CardTitle class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <Badge variant="default"> Active </Badge>
                        <span> {{ properties?.length }} columns </span>
                    </div>
                    <div class="flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock class="size-3.5" />
                        {{
                            new Date(schema?.created_at).toLocaleDateString($i18n.locale, {
                                month: "short",
                                day: "numeric",
                                year: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                                timeZone: "UTC",
                            })
                        }}
                    </div>
                </CardTitle>
            </CardHeader>

            <Separator />

            <CardContent class="space-y-4">
                <div class="flex items-center space-x-2 text-xs text-muted-foreground">
                    <span class="font-medium">Schema:</span>
                    <code class="rounded bg-muted px-1.5 py-0.5">
                        {{ schema.active_schema.$schema }}
                    </code>
                </div>

                <div class="rounded-lg border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableCell class="px-4 py-2">Column </TableCell>
                                <TableCell>Type </TableCell>
                                <TableCell>Constraints </TableCell>
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
                                            <component
                                                :is="TableUtils.getIcon(config.type)"
                                                class="size-3.5"
                                            />
                                        </div>
                                        <span class="text-sm text-muted-foreground">
                                            {{ config.type }}
                                        </span>
                                    </TableCell>
                                    <TableCell>
                                        <Badge
                                            v-for="badge in makeBadges({
                                                primary_key: config.primary_key || false,
                                                unique: config.unique || false,
                                                optional: config.optional || false,
                                            })"
                                            :key="badge.label"
                                        >
                                            Puta
                                        </Badge>
                                    </TableCell>
                                </TableRow>
                            </template>
                        </TableBody>
                    </Table>
                </div>
            </CardContent>
        </Card>
    </div>
</template>
