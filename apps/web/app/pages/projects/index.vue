<script setup lang="ts">
    import type { z } from "zod";
    import { PaginatedResponse, ResponseProjectSchema } from "#shared/utils/schemas/api";
    import {
        AlignLeft,
        Check,
        Database,
        Edit,
        ExternalLink,
        MoreVertical,
        Plug,
        Plus,
        Search,
        Server,
        Trash,
    } from "lucide-vue-next";
    import { cn } from "@/lib/utils";

    definePageMeta({
        title: "projects.view.title",
        layout: "sidebar",
        i18n: {
            paths: {
                en: "/projects",
            },
        },
    });

    interface ProjectInformation {
        label: string;
        value: string | undefined | null;
        fallbackValue: string;
        icon?: Components.LucideIconComponent;
        warning?: boolean;
        tooltip?: string;
    }

    const { $localeRoute } = useNuxtApp();
    const errorToast = useErrorToast();
    const config = useAppConfig();
    const Response = PaginatedResponse(ResponseProjectSchema);

    const currentPage = useRouteQuery("page", 1, {
        transform: Number,
        mode: "replace",
    });
    const searchContent = useState("search-content", () => "");
    const debouncedSearchContent = useDebounce(searchContent, 1000);

    const { data: _data } = useApiFetch("/projects/search", {
        query: {
            name: debouncedSearchContent,
            skip: (currentPage.value - 1) * config.pagination.defaultPageSize,
            limit: config.pagination.defaultPageSize,
        },
        key: `${currentPage.value}-projects-search`,
    });
    const data = computed(() => {
        const parsed = Response.safeParse(_data.value);
        if (!parsed.success) {
            errorToast.handle(ResponseCodesRecord.Server.BadPayload);
            return;
        }

        return parsed.data;
    });

    const dropdownItems = computed<
        Components.GenericDropdown.Item<z.infer<typeof ResponseProjectSchema>>[][]
    >(() => [
        [
            {
                label: "projects.view.dropdown.view.label",
                icon: ExternalLink,
                to: (context) => {
                    if (context) {
                        return $localeRoute({ name: "projects-id", params: { id: context.id } });
                    }

                    return $localeRoute({ name: "index" });
                },
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

    function makeInfo(project: z.infer<typeof ResponseProjectSchema>): ProjectInformation[] {
        return [
            {
                label: $t("projects.create.fields.db_host.label"),
                value: project.db_host,
                fallbackValue: $t("projects.create.fields.db_host.label"),
                icon: Server,
                warning: !project.db_host,
                tooltip: $t("projects.view.content.no_field", {
                    field: $t("projects.create.fields.db_host.label"),
                }),
            },
            {
                label: $t("projects.create.fields.db_port.label"),
                value: project.db_port?.toString(),
                fallbackValue: $t("projects.create.fields.db_port.label"),
                icon: Plug,
                warning: !project.db_port,
                tooltip: $t("projects.view.content.no_field", {
                    field: $t("projects.create.fields.db_port.label"),
                }),
            },
            {
                label: $t("projects.create.fields.db_name.label"),
                value: project.db_name,
                fallbackValue: $t("projects.create.fields.db_name.label"),
                icon: AlignLeft,
                warning: !project.db_name,
                tooltip: $t("projects.view.content.no_field", {
                    field: $t("projects.create.fields.db_name.label"),
                }),
            },
        ];
    }
</script>

<template>
    <TooltipProvider>
        <div class="mx-auto w-full max-w-5xl">
            <div class="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                    <h1 class="text-2xl font-semibold tracking-tight text-foreground text-balance">
                        {{ $t("projects.view.header.title") }}
                    </h1>
                    <p class="mt-1.5 text-sm text-muted-foreground">
                        {{ $t("projects.view.header.description") }}
                    </p>
                </div>
                <NuxtLink as-child :to="$localeRoute({ name: 'projects-create' })">
                    <Button>
                        <Plus class="size-4" />
                        <span>{{ $t("projects.create.header.title") }}</span>
                    </Button>
                </NuxtLink>
            </div>

            <div class="mb-6">
                <InputGroup class="max-w-sm">
                    <InputGroupInput
                        v-model="searchContent"
                        :placeholder="$t('projects.view.search_input.placeholder')"
                    />
                    <InputGroupAddon align="inline-start">
                        <Search />
                    </InputGroupAddon>
                </InputGroup>
            </div>

            <PaginationRoot
                :items="data?.items"
                index="id"
                :page="currentPage"
                :page-size="data?.limit ?? config.pagination.defaultPageSize"
                :total-pages="data?.total_pages ?? 1"
                class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3"
            >
                <template #item="{ $item }">
                    <Card
                        class="group relative overflow-hidden transition-colors hover:border-foreground/20"
                    >
                        <CardHeader>
                            <Field orientation="horizontal">
                                <Database class="size-8" stroke-width="2" />
                                <FieldContent>
                                    <CardTitle>
                                        {{ $item.name }}
                                    </CardTitle>
                                    <CardDescription
                                        :class="
                                            cn(
                                                'line-clamp-2',
                                                !$item.description
                                                    && 'text-yellow-700 dark:text-yellow-400/70 italic font-medium',
                                            )
                                        "
                                    >
                                        {{
                                            ifEmpty(
                                                $item.description,
                                                $t("projects.view.content.no_description"),
                                            )
                                        }}
                                    </CardDescription>
                                </FieldContent>
                                <DropdownMenuRoot :context="$item" :items="dropdownItems">
                                    <template #trigger>
                                        <Button
                                            variant="ghost"
                                            class="size-8 p-0 opacity-0 group-hover:opacity-100"
                                        >
                                            <MoreVertical class="size-4" />
                                        </Button>
                                    </template>
                                </DropdownMenuRoot>
                            </Field>
                        </CardHeader>
                        <CardContent>
                            <div
                                class="grid grid-cols-1 gap-px overflow-hidden rounded-lg border bg-border"
                            >
                                <div
                                    v-for="info in makeInfo($item)"
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
                                            <span
                                                class="mt-0.5 truncate font-mono text-xs text-foreground"
                                            >
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
                                                    <span
                                                        v-html="
                                                            info.tooltip.replace(/\n/g, '<br />')
                                                        "
                                                    />
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
                                            <span
                                                class="mt-0.5 truncate font-mono text-xs text-foreground"
                                            >
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
                                            $item.provider?.length && 'bg-green-500',
                                        )
                                    "
                                >
                                    {{
                                        ifEmpty(
                                            $item.provider,
                                            $t("projects.view.content.no_provider"),
                                        )
                                    }}
                                </Badge>

                                <span class="text-[10px] text-muted-foreground">
                                    {{
                                        new Date($item.created_at).toLocaleDateString(
                                            $i18n.locale,
                                            {
                                                month: "long",
                                                day: "numeric",
                                                year: "numeric",
                                            },
                                        )
                                    }}
                                </span>
                            </div>
                        </CardContent>
                    </Card>
                </template>
            </PaginationRoot>
        </div>
    </TooltipProvider>
</template>
