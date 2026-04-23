<script setup lang="ts">
    import { Grid2x2Check, Grid2x2X, Plus, X } from "lucide-vue-next";

    const qb = useQueryBuilder();

    const { $gsap } = useNuxtApp();

    function onRowEnter(element: Element, done: () => void) {
        if (!(element instanceof HTMLElement)) {
            return;
        }

        $gsap.killTweensOf(element);
        element.style.overflow = "hidden";
        $gsap.from(element, {
            opacity: 0,
            y: -6,
            height: 0,
            paddingTop: 0,
            paddingBottom: 0,
            duration: 0.25,
            ease: "power2.out",
            clearProps: "height,paddingTop,paddingBottom,overflow",
            onComplete: done,
        });
    }

    function onRowLeave(element: Element, done: () => void) {
        if (!(element instanceof HTMLElement)) {
            return;
        }

        $gsap.killTweensOf(element);
        element.style.overflow = "hidden";
        $gsap.to(element, {
            opacity: 0,
            x: -10,
            height: 0,
            paddingTop: 0,
            paddingBottom: 0,
            duration: 0.2,
            ease: "power2.in",
            onComplete: done,
        });
    }
</script>

<template>
    <Card>
        <CardHeader>
            <div class="flex items-center justify-between">
                <div class="space-y-1.5">
                    <CardTitle>
                        {{ $t("projects.id.sections.query_builder.cards.columns.title") }}
                    </CardTitle>
                    <CardDescription>
                        {{ $t("projects.id.sections.query_builder.cards.columns.description") }}
                    </CardDescription>
                </div>

                <div v-if="qb.state.selectedCols.value.length" class="space-x-2">
                    <Button
                        variant="outline"
                        size="sm"
                        class="cursor-pointer"
                        @click="qb.dispatch.addColumn"
                    >
                        <Plus />
                        {{ $t("projects.id.sections.query_builder.actions.add_column") }}
                    </Button>
                    <Button
                        variant="default"
                        size="sm"
                        class="cursor-pointer"
                        @click="qb.dispatch.selectAllColumns()"
                    >
                        <Grid2x2Check />
                        {{ $t("projects.id.sections.query_builder.actions.select_all") }}
                    </Button>
                </div>
            </div>
        </CardHeader>
        <CardContent>
            <TransitionGroup tag="div" :css="false" @enter="onRowEnter" @leave="onRowLeave">
                <div
                    v-for="(sc, i) in qb.state.selectedCols.value"
                    :key="sc.id"
                    class="flex items-center gap-3 px-6 py-2.5 border-b border-border/50 last:border-b-0 group"
                >
                    <span
                        class="text-xs text-muted-foreground w-4 shrink-0 select-none tabular-nums"
                    >
                        {{ i + 1 }}
                    </span>

                    <div class="flex items-center flex-1 min-w-0">
                        <Select
                            :model-value="sc.col"
                            @update:model-value="
                                qb.dispatch.updateColumn(sc.id, $event?.toString())
                            "
                        >
                            <SelectTrigger
                                class="h-8 w-56 font-mono text-xs rounded-r-none border-r-0"
                            >
                                <SelectValue
                                    :placeholder="
                                        $t(
                                            'projects.id.sections.query_builder.placeholders.select_column',
                                        )
                                    "
                                />
                            </SelectTrigger>
                            <SelectContent :body-lock="false">
                                <SelectItem
                                    v-for="col in qb.state.columnNames.value"
                                    :key="col"
                                    :value="col"
                                >
                                    {{ col }}
                                </SelectItem>
                            </SelectContent>
                        </Select>

                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger as-child>
                                    <div
                                        class="h-9 px-2.5 flex items-center border border-border rounded-r-md bg-muted/50 cursor-default shrink-0"
                                    >
                                        <span class="font-mono text-xs text-muted-foreground">
                                            {{
                                                qb.state.columns.value.find(
                                                    (c) => c.name === sc.col,
                                                )?.pgType ?? "?"
                                            }}
                                        </span>
                                    </div>
                                </TooltipTrigger>
                                <TooltipContent>
                                    <p class="text-xs">
                                        {{ $t("projects.id.sections.query_builder.labels.dtype") }}:
                                        {{
                                            qb.state.columns.value.find((c) => c.name === sc.col)
                                                ?.dtype
                                        }}
                                    </p>
                                </TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    </div>

                    <Button
                        variant="ghost"
                        size="icon"
                        class="size-7 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 hover:text-slate-50 hover:bg-rose-500 transition-opacity cursor-pointer"
                        @click="qb.dispatch.removeColumn(sc.id)"
                    >
                        <X class="size-3.5" />
                    </Button>
                </div>

                <Empty v-if="!qb.state.selectedCols.value.length" key="empty">
                    <EmptyHeader>
                        <EmptyMedia variant="icon">
                            <Grid2x2X />
                        </EmptyMedia>
                        <EmptyTitle>
                            {{ $t("projects.id.sections.query_builder.empty.header.title") }}
                        </EmptyTitle>
                        <EmptyDescription>
                            {{ $t("projects.id.sections.query_builder.empty.header.description") }}
                        </EmptyDescription>
                    </EmptyHeader>
                    <EmptyContent>
                        <div>
                            <Button
                                variant="outline"
                                size="sm"
                                class="cursor-pointer"
                                @click="qb.dispatch.addColumn"
                            >
                                <Plus />
                                {{ $t("projects.id.sections.query_builder.actions.add_column") }}
                            </Button>
                        </div>
                    </EmptyContent>
                </Empty>
            </TransitionGroup>
        </CardContent>
    </Card>
</template>
