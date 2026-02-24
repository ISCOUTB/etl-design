<script setup lang="ts">
    import type { z } from "zod";
    import { PaginatedResponse, ResponseProjectSchema } from "#shared/utils/schemas/api";
    import { Plus } from "lucide-vue-next";

    definePageMeta({
        title: "projects.view.title",
        layout: "sidebar",
        i18n: {
            paths: {
                en: "/projects",
            },
        },
    });

    const Response = PaginatedResponse(ResponseProjectSchema);
    const { data } = useApiFetch<z.infer<typeof Response>>("/projects/search", {
        onResponse({ response }) {
            const parsedResponse = Response.safeParse(response.body);
            if (!parsedResponse.success) {
                return;
            }

            response._data = parsedResponse.data;
        },
    });

    /**
     * data.value.items is of type Record<string, unknown>
     * Typescript does not infers that it is in fact a ResponseProjectSchema[]
     */
    const { columns } = useProjectsTableColumns();
</script>

<template>
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

        <template v-if="data">
            <DataTable state-key="projects" :columns="columns" :data="data.items">
                <template #control-previous>
                    {{ $t("projects.view.table.pagination.previous") }}
                </template>
                <template #control-next>
                    {{ $t("projects.view.table.pagination.next") }}
                </template>
            </DataTable>
        </template>
    </div>
</template>
