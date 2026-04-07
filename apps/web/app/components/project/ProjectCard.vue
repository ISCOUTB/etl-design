<script setup lang="ts">
    import type { z } from "zod";
    import { Check, Database, ExternalLink } from "lucide-vue-next";
    import { cn } from "~/lib/utils";

    interface Props {
        project: MaybeRefOrGetter<z.infer<typeof ResponseProjectSchema>>;
        makeInfo: (
            project: z.infer<typeof ResponseProjectSchema>,
        ) => Schemas.Project.ProjectInformation[];
    }

    const props = defineProps<Props>();
    const project = computed(() => toValue(props.project));
</script>

<template>
    <Card
        class="group relative overflow-hidden transition-colors hover:border-foreground/20"
        @dblclick="
            () => $router.push($localeRoute({ name: 'projects-id', params: { id: project.id } }))
        "
    >
        <CardHeader>
            <Field orientation="horizontal">
                <Database class="size-8" stroke-width="2" />
                <FieldContent>
                    <CardTitle>
                        {{ project.name }}
                    </CardTitle>
                    <CardDescription
                        :class="
                            cn(
                                'line-clamp-2',
                                !project.description && 'text-muted-foreground italic',
                            )
                        "
                    >
                        {{
                            ifEmpty(project.description, $t("projects.view.content.no_description"))
                        }}
                    </CardDescription>
                </FieldContent>
                <Button variant="ghost" size="icon" as-child>
                    <NuxtLink
                        :to="$localeRoute({ name: 'projects-id', params: { id: project.id } })"
                    >
                        <ExternalLink />
                    </NuxtLink>
                </Button>
            </Field>
        </CardHeader>
        <CardContent class="cursor-default select-none">
            <div class="grid grid-cols-1 gap-px overflow-hidden rounded-lg border bg-border">
                <div
                    v-for="info in makeInfo(project)"
                    :key="info.label"
                    class="flex justify-between items-center bg-card px-3 py-2.5 h-14"
                >
                    <template v-if="!info.value?.toString().length">
                        <div class="flex flex-col">
                            <span
                                class="text-[10px] uppercase tracking-wider text-muted-foreground"
                            >
                                {{ info.label }}
                            </span>
                            <span class="mt-0.5 truncate font-mono text-xs text-foreground">
                                {{ info.fallbackValue }}
                            </span>
                        </div>
                        <template v-if="info.tooltip && info.tooltip.length > 0">
                            <Tooltip :delay-duration="800">
                                <TooltipTrigger as-child>
                                    <component
                                        :is="info.icon"
                                        v-if="info.warning"
                                        class="size-4 text-yellow-700 dark:text-orange-500"
                                    />
                                </TooltipTrigger>
                                <TooltipContent align="end" side="bottom">
                                    <span v-html="info.tooltip.replace(/\n/g, '<br />')" />
                                </TooltipContent>
                            </Tooltip>
                        </template>
                        <template v-else>
                            <component
                                :is="info.icon"
                                v-if="info.warning"
                                class="size-4 text-yellow-500"
                            />
                        </template>
                    </template>
                    <template v-else>
                        <div class="flex flex-col">
                            <span
                                class="text-[10px] uppercase tracking-wider text-muted-foreground"
                            >
                                {{ info.label }}
                            </span>
                            <span class="mt-0.5 truncate font-mono text-xs text-foreground">
                                <SensitiveInfoInline :value="info.value" />
                            </span>
                        </div>

                        <Check class="text-green-500 size-4" />
                    </template>
                </div>
            </div>

            <div class="mt-3.5 flex items-center justify-between">
                <Badge
                    :class="
                        cn(
                            'text-xs bg-yellow-500 text-gray-100 font-bold',
                            project.provider?.length && 'bg-green-500',
                        )
                    "
                >
                    {{ ifEmpty(project.provider, $t("projects.view.content.no_provider")) }}
                </Badge>

                <span class="text-[10px] text-muted-foreground">
                    {{
                        new Date(project.created_at).toLocaleDateString($i18n.locale, {
                            month: "long",
                            day: "numeric",
                            year: "numeric",
                        })
                    }}
                </span>
            </div>
        </CardContent>
    </Card>
</template>
