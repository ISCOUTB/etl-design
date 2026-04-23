<script setup lang="ts">
    import type { z } from "zod";
    import { ChevronRight, Edit, Eye, Pickaxe, RotateCcw, Table2, Trash2 } from "lucide-vue-next";
    import { cn } from "~/lib/utils";

    interface Props {
        table: MaybeRefOrGetter<z.infer<typeof MongoRawSchema>>;
    }

    interface Action {
        label: string;
        icon: Components.LucideIconComponent;
        hidden?: boolean | (() => boolean);
        disabled?: boolean | (() => boolean);
        action: () => void;
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

    const { VIEWS, queryBuilder } = useProject();
    const modal = useModal();

    const { $localeRoute } = useNuxtApp();
    const route = useRoute();
    const config = useAppConfig();
    const events = useAppEvents();
    const { project, tables } = useProject();
    const actions = computed<Action[]>(() =>
        [
            {
                label: "projects.id.sections.tables.card.dropdown.view_schema",
                icon: Eye,
                action() {
                    tables.dispatch.setSelectedSchema(table.value);
                    events.emit("event:projects:table:change-view", { value: "details" });
                },
            },
            {
                label: "projects.id.sections.tables.card.dropdown.query",
                icon: Pickaxe,
                action() {
                    queryBuilder.state.schema.value = table.value;
                    events.emit("event:projects:change-tab", { value: VIEWS.value.QueryBuilder });
                },
            },
            {
                label: "projects.id.sections.tables.card.dropdown.edit",
                icon: Edit,
                async action() {
                    await navigateTo(
                        $localeRoute({
                            name: "projects-id-tables-tableName-edit",
                            params: {
                                id: project.value.id,
                                tableName: TableUtils.getTableName(table.value.import_name),
                            },
                            query: { [config.constants.CALLBACK_KEY]: route.fullPath },
                        }),
                    );
                },
            },
            {
                label: "projects.id.sections.tables.card.dropdown.revert",
                icon: RotateCcw,
                hidden: () => table.value.schemas_releases.length === 0,
                action() {
                    modal.dispatch.loadComponent({
                        loader: () =>
                            import("~/components/project/tables/ProjectTablesDeleteModal.vue"),
                        key: ModalKeys.Projects.Tables.Delete,
                        props: {
                            table: table.value,
                            projectId: project.value.id,
                            kind: "revert",
                        },
                    });
                },
            },
            {
                label: "projects.id.sections.tables.card.dropdown.delete",
                icon: Trash2,
                hidden: () => table.value.schemas_releases.length > 0,
                action() {
                    modal.dispatch.loadComponent({
                        loader: () =>
                            import("~/components/project/tables/ProjectTablesDeleteModal.vue"),
                        key: ModalKeys.Projects.Tables.Delete,
                        props: {
                            table: table.value,
                            projectId: project.value.id,
                            kind: "delete",
                        },
                    });
                },
            },
        ].filter((action) => !toValue(action.hidden)),
    );

    function handleSelect(_event: Event) {
        tables.dispatch.setSelectedSchema(table.value);
        events.emit("event:projects:table:change-view", { value: "details" });
    }
</script>

<template>
    <Collapsible v-model:open="open">
        <Card
            class="shadow-sm"
            @click="
                () => {
                    if (!open) {
                        open = !open;
                    }
                }
            "
            @dblclick="handleSelect"
        >
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
                            <Badge
                                v-if="table.schemas_releases.length > 0"
                                variant="outline"
                                class="bg-emerald-500 border-emerald-400 text-white dark:bg-gray-700"
                            >
                                {{
                                    $t("projects.id.sections.tables.card.n_versions", {
                                        length: table.schemas_releases.length,
                                    })
                                }}
                            </Badge>
                        </ItemTitle>
                        <ItemDescription class="select-none">
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
                        <template v-for="action in actions" :key="action.label">
                            <Tooltip :delay-duration="800">
                                <TooltipProvider>
                                    <TooltipTrigger as-child>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            @click.stop="action.action"
                                        >
                                            <component :is="action.icon" />
                                        </Button>
                                    </TooltipTrigger>
                                    <TooltipContent side="bottom">
                                        {{ $t(action.label) }}
                                    </TooltipContent>
                                </TooltipProvider>
                            </Tooltip>
                        </template>
                        <Button
                            variant="ghost"
                            size="icon"
                            :class="cn(open && 'rotate-90')"
                            @click.stop="() => (open = !open)"
                        >
                            <ChevronRight class="size-4" />
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
