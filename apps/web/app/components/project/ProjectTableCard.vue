<script setup lang="ts">
    import type { z } from "zod";
    import { ChevronsUpDown, MoreVertical, Table2 } from "lucide-vue-next";
    import { cn } from "~/lib/utils";

    interface Props {
        table: MaybeRefOrGetter<z.infer<typeof MongoRawSchema>>;
    }

    const props = defineProps<Props>();
    const table = computed(() => toValue(props.table));
    const open = useState<boolean>(
        NuxtKeys.Projects.Tables.CollapsibleState(table.value),
        () => false,
    );
    const animations = useCollapsibleAnimations();

    const tableName = computed(() => TableUtils.getTableName(table.value.import_name));
    const properties = computed(() => Object.entries(table.value.active_schema.properties));
    const requiredFiels = computed(() => table.value.active_schema.required);

    const columns = computed(() =>
        properties.value.map(([name, prop]) => ({
            name,
            prop,
            required: requiredFiels.value.includes(name),
            icon: TableUtils.getIcon(prop.type),
            color: TableUtils.getColor(prop.type),
        })),
    );
</script>

<template>
    <Collapsible v-model:open="open">
        <Card class="shadow-sm">
            <CardHeader>
                <Item class="p-0">
                    <ItemMedia>
                        <Table2 class="size-6 text-primary" />
                    </ItemMedia>
                    <ItemContent>
                        <ItemTitle>
                            <span>
                                {{ tableName }}
                            </span>
                            <Badge variant="secondary">
                                {{
                                    $t("projects.id.sections.tables.card.n_columns", {
                                        length: properties.length,
                                    })
                                }}
                            </Badge>
                        </ItemTitle>
                        <ItemDescription>
                            {{
                                new Date(table.created_at).toLocaleDateString($i18n.locale, {
                                    month: "long",
                                    day: "numeric",
                                    year: "numeric",
                                })
                            }}
                        </ItemDescription>
                    </ItemContent>
                    <ItemActions>
                        <CollapsibleTrigger as-child>
                            <Button variant="ghost" size="icon">
                                <ChevronsUpDown class="size-4" />
                            </Button>
                        </CollapsibleTrigger>
                        <Button variant="ghost" size="icon">
                            <MoreVertical class="size-4" />
                        </Button>
                    </ItemActions>
                </Item>
            </CardHeader>
            <Transition :css="false" @enter="animations.onEnter" @leave="animations.onLeave">
                <CollapsibleContent v-if="open" force-mount>
                    <CardContent>
                        <template v-for="column in columns" :key="column.name">
                            <div
                                class="flex items-center justify-between rounded-md px-2 py-1.5 hover:bg-muted/50 transition-colors"
                            >
                                <div class="flex items-center gap-2.5">
                                    <div
                                        :class="
                                            cn(
                                                'flex size-6 items-center justify-center rounded',
                                                column.color,
                                            )
                                        "
                                    >
                                        <component :is="column.icon" class="size-3.5" />
                                    </div>
                                    <span class="font-mono text-sm text-foreground">
                                        {{ column.name }}
                                    </span>
                                    <template v-if="column.required">
                                        <Badge
                                            variant="outline"
                                            class="text-[10px]font-normal text-muted-foreground"
                                        >
                                            {{
                                                $t(
                                                    "projects.id.sections.tables.card.required_column",
                                                )
                                            }}
                                        </Badge>
                                    </template>
                                </div>
                                <span :class="cn('text-xs  px-2 py-1.5 rounded-lg', column.color)">
                                    {{ column.prop.type }}
                                </span>
                            </div>
                        </template>
                    </CardContent>
                </CollapsibleContent>
            </Transition>
        </Card>
    </Collapsible>
</template>
