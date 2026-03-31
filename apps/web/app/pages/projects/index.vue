<script setup lang="ts">
    import type { z } from "zod";
    import { PaginatedResponse, ResponseProjectSchema } from "#shared/utils/schemas/api";
    import {
        AlignLeft,
        ChevronsLeft,
        ChevronsRight,
        Edit,
        ExternalLink,
        Plug,
        Plus,
        Search,
        Server,
        Trash,
    } from "lucide-vue-next";

    definePageMeta({
        title: "projects.view.title",
        layout: "sidebar",
        i18n: {
            paths: {
                en: "/projects",
            },
        },
    });

    const { locale } = useI18n();

    useSeoMeta({
        ogType: "website",
        description: () => $t("projects.view.header.description"),
        ogTitle: () => $t("projects.view.title"),
        ogDescription: () => $t("projects.view.header.description"),
        ogLocale: () => locale.value.replace("-", "_"),
        robots: "index, follow",
    });

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
    const calculatedSkip = computed(
        () => (currentPage.value - 1) * config.pagination.defaultPageSize,
    );

    const { data: _data, status } = useApiFetch("/projects/search", {
        query: {
            name: debouncedSearchContent,
            skip: calculatedSkip,
            limit: config.pagination.defaultPageSize,
        },
        key: NuxtKeys.Projects.Search,
    });
    const data = computed(() => {
        if (!_data.value) {
            return;
        }

        const parsed = Response.safeParse(_data.value);
        if (!parsed.success) {
            errorToast.handle(ResponseCodesRecord.Server.BadPayload);
            return;
        }

        return parsed.data;
    });

    const modal = useModal();
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
                to: (context) => {
                    if (!context) {
                        return;
                    }

                    return $localeRoute({ name: "projects-id-edit", params: { id: context.id } });
                },
            },
        ],
        [
            {
                label: "projects.view.dropdown.delete.label",
                icon: Trash,
                action: (context) => {
                    if (!context) {
                        return;
                    }

                    modal.dispatch.loadComponent({
                        loader: () =>
                            import("@/components/project/ProjectDeleteConfirmationModal.vue"),
                        key: ModalKeys.Projects.Delete.ConfirmationModal,
                        props: {
                            project: context,
                        },
                    });
                },
            },
        ],
    ]);

    function makeInfo(
        project: z.infer<typeof ResponseProjectSchema>,
    ): Schemas.Project.ProjectInformation[] {
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

    function handlePageChange(page: number) {
        currentPage.value = page;
    }
</script>

<template>
    <div class="mx-auto w-full max-w-5xl flex flex-col grow">
        <TooltipProvider>
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
                :loading="status === 'pending'"
                :page-size="data?.limit ?? config.pagination.defaultPageSize"
                :total-pages="data?.total_pages ?? 1"
                class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3"
                @change-page="handlePageChange"
            >
                <template #controls-previous>
                    <ChevronsLeft />
                </template>
                <template #controls-next>
                    <ChevronsRight />
                </template>

                <template #empty>
                    <LazyProjectEmpty />
                </template>

                <template #loading>
                    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                        <template v-for="i in config.pagination.defaultPageSize" :key="i">
                            <Skeleton class="w-full h-82.5" />
                        </template>
                    </div>
                </template>

                <template #item="{ $item }">
                    <ProjectCard
                        :project="$item"
                        :dropdown-items="dropdownItems"
                        :make-info="makeInfo"
                    />
                </template>
            </PaginationRoot>
        </TooltipProvider>
    </div>
</template>
