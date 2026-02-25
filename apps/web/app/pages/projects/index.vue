<script setup lang="ts">
    import { ResponseCodesRecord } from "#shared/utils/response-codes";
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

    const config = useAppConfig();
    const errorToast = useServerErrorToast();
    const Response = PaginatedResponse(ResponseProjectSchema);

    const currentPage = useRouteQuery("page", 1, {
        transform: Number,
        mode: "replace",
    });
    const { data: _data } = useApiFetch("/projects/search", {
        query: {
            skip: (currentPage.value - 1) * config.pagination.defaultPageSize,
            limit: config.pagination.defaultPageSize,
        },
    });
    const data = computed(() => {
        const parsed = Response.safeParse(_data.value);
        console.warn(parsed.data);
        if (!parsed.success) {
            errorToast.handle(ResponseCodesRecord.Server.BadPayload);
            return;
        }

        return parsed.data;
    });

    const auth = useAuth();
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

        <PaginationRoot
            :items="data?.items"
            index="id"
            :page="currentPage"
            :page-size="data?.limit ?? config.pagination.defaultPageSize"
            :total-pages="data?.total_pages ?? 1"
        >
            <div>
                Lorem ipsum dolor sit amet consectetur adipisicing elit. Ea, fuga a iusto
                necessitatibus voluptas, repellat architecto, amet consequatur delectus dicta
                dignissimos doloribus optio aperiam voluptate? Repellat cumque voluptatum doloremque
                ipsa!
            </div>
        </PaginationRoot>

        <pre>
            {{ auth.data.value?.accessToken }}
        </pre>
    </div>
</template>
