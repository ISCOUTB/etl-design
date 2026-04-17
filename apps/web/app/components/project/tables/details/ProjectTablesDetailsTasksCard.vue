<script setup lang="ts">
    import type { ProjectTask } from "#shared/utils/schemas/types";
    import type { HTMLAttributes, HtmlHTMLAttributes } from "vue";
    import type { BadgeVariants } from "~/components/ui/badge";
    import { AlertCircle, CheckCircle2, Send } from "lucide-vue-next";
    import { cn } from "@/lib/utils";

    interface Props {
        task: ProjectTask;
    }

    interface Properties {
        icon: {
            component: Components.LucideIconComponent;
            class: HTMLAttributes["class"];
        };
        header: {
            class: HtmlHTMLAttributes["class"];
        };
        badge: {
            variant: BadgeVariants["variant"];
            class: HTMLAttributes["class"];
            label: string;
        };
    }

    const props = defineProps<Props>();

    function hasError(task: ProjectTask) {
        return !!task.data.error;
    }

    const properties = computed<Properties>(() => {
        if (hasError(props.task)) {
            return {
                icon: {
                    component: AlertCircle,
                    class: "text-destructive",
                },
                header: {
                    class: "bg-destructive/5 border-destructive/50",
                },
                badge: {
                    variant: "destructive",
                    class: "",
                    label: "projects.id.sections.tables.details.tasks.status.failed",
                },
            };
        }

        if (props.task.status === "published") {
            return {
                icon: {
                    component: Send,
                    class: "text-amber-600",
                },
                header: {
                    class: "bg-amber-500/5 border-amber-500/50",
                },
                badge: {
                    variant: "secondary",
                    class: "border-amber-500/30 bg-amber-500 text-slate-50",
                    label: "projects.id.sections.tables.details.tasks.status.published",
                },
            };
        }

        return {
            icon: {
                component: CheckCircle2,
                class: "text-emerald-600",
            },
            header: {
                class: "bg-emerald-500/5 border-emerald-500/50",
            },
            badge: {
                variant: "secondary",
                class: "border-emerald-500/30 bg-emerald-500 text-slate-50",
                label: "projects.id.sections.tables.details.tasks.status.completed",
            },
        };
    });
</script>

<template>
    <div :class="cn('rounded-lg pb-4 border', properties.header.class)">
        <Item>
            <ItemMedia>
                <component :is="properties.icon.component" :class="properties.icon.class" />
            </ItemMedia>
            <ItemContent>
                <ItemTitle>
                    {{ $t("projects.id.sections.tables.details.tasks.item") }}
                </ItemTitle>
                <ItemDescription class="text-xs">
                    {{
                        new Date(task.data.upload_date).toLocaleDateString($i18n.locale, {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                            timeZone: "UTC",
                        })
                    }}
                    <template v-if="task.data.upload_date !== task.data.update_date">
                        {{
                            $t("projects.id.sections.tables.details.tasks.updated", {
                                when: new Date(task.data.update_date).toLocaleDateString(
                                    $i18n.locale,
                                    {
                                        month: "short",
                                        day: "numeric",
                                        year: "numeric",
                                        hour: "2-digit",
                                        minute: "2-digit",
                                        timeZone: "UTC",
                                    },
                                ),
                            })
                        }}
                    </template>
                </ItemDescription>
            </ItemContent>
            <ItemActions>
                <Badge :variant="properties.badge.variant" :class="properties.badge.class">
                    {{ $t(properties.badge.label) }}
                </Badge>
            </ItemActions>
        </Item>
        <Accordion type="multiple" class="px-4">
            <AccordionItem v-if="task.data.error?.length" value="errors">
                <AccordionTrigger
                    class="hover:no-underline focus-visible:ring-0 px-4 bg-destructive/5 cursor-pointer"
                >
                    {{ $t("projects.id.sections.tables.details.tasks.fields.errors") }}
                </AccordionTrigger>
                <AccordionContent class="mt-4">
                    {{ task.data.error }}
                </AccordionContent>
            </AccordionItem>

            <AccordionItem v-if="task.status === 'published'" value="logs">
                <AccordionTrigger
                    class="hover:no-underline focus-visible:ring-0 px-4 bg-amber-500/10 cursor-pointer"
                >
                    {{ $t("projects.id.sections.tables.details.tasks.fields.logs") }}
                </AccordionTrigger>
                <AccordionContent class="mt-4">
                    <CodeBlock class="border-amber-500/50" :content="task.data.results" />
                </AccordionContent>
            </AccordionItem>
        </Accordion>
    </div>
</template>
