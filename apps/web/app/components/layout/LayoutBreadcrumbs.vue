<script setup lang="ts">
    const { t, te } = useI18n();
    const { $localeRoute } = useNuxtApp();

    const router = useRouter();

    const { BREADCRUMB_OVERRIDES } = useGlobalState();
    const _breadcrumbs = useBreadcrumbItems();
    const breadcrumbs = computed(() => {
        const items = _breadcrumbs.value;

        const rawMetas = items.map((item) => {
            const record = resolveRoute(item.to);
            return record?.meta.breadcrumb as Breadcrumb.PageMeta | undefined;
        });

        const resolvedMetas = [...rawMetas];
        for (let i = items.length - 1; i >= 0; i--) {
            const meta = resolvedMetas[i];
            if (!meta?.options?.parent) {
                continue;
            }

            const parentIndex = i - 1;
            if (parentIndex < 0) {
                continue;
            }

            resolvedMetas[parentIndex] = {
                ...resolvedMetas[parentIndex],
                ...meta.options.parent,
                overrides: {
                    ...resolvedMetas[parentIndex]?.overrides,
                    ...meta.options.parent?.overrides,
                },
            };
        }

        return items.map((item, index) => {
            const resolved = resolvedMetas[index];
            return {
                ...item,
                label: resolveOverride(
                    resolved?.overrides?.label?.keypath,
                    resolved?.label || item.label,
                ),
                kind: resolveOverride(resolved?.overrides?.kind?.keypath, resolved?.kind || "page"),
            };
        });
    });

    const config = useAppConfig();
    const slicedBreadcrumbs = computed(() => {
        if (breadcrumbs.value.length <= config.composables.useBreadcrumbItems.maxItems) {
            return breadcrumbs.value;
        }

        return [
            breadcrumbs.value[0],
            undefined,
            ...breadcrumbs.value.slice(-(config.composables.useBreadcrumbItems.maxItems - 1)),
        ];
    });

    const dropdownItems = computed<Components.GenericDropdown.Item[]>(() => {
        if (breadcrumbs.value.length <= config.composables.useBreadcrumbItems.maxItems) {
            return [];
        }

        return breadcrumbs.value
            .slice(
                1,
                breadcrumbs.value.length - (config.composables.useBreadcrumbItems.maxItems - 1),
            )
            .map<Components.GenericDropdown.Item>((breadcrumb) => ({
                label: breadcrumb.label,
                to: () => breadcrumb.to || $localeRoute({ name: "index" }),
            }));
    });

    function resolveOverride(keypath: string | undefined, _default: string) {
        if (!keypath) {
            return _default;
        }

        const overrided = BREADCRUMB_OVERRIDES.value[keypath];
        if (overrided) {
            return overrided;
        }
        return _default;
    }

    function resolveRoute(to: string | undefined) {
        if (to) {
            return router.resolve(to).matched.at(-1);
        }
    }

    function resolveText(keypath: string) {
        if (te(keypath)) {
            return t(keypath);
        }

        return keypath;
    }

    const route = useRoute();
    function useOverrides() {
        return route.matched.some((record) => {
            const breadcrumb = record.meta.breadcrumb;
            return Boolean(breadcrumb?.overrides);
        });
    }
    watch(
        () => route.fullPath,
        () => {
            if (!useOverrides()) {
                BREADCRUMB_OVERRIDES.value = {};
            }
        },
        { immediate: true },
    );
</script>

<template>
    <Breadcrumb>
        <BreadcrumbList>
            <template v-for="(item, index) in slicedBreadcrumbs" :key="index">
                <BreadcrumbItem>
                    <template v-if="!item">
                        <DropdownMenuRoot
                            :items="[dropdownItems]"
                            :root-props="{ modal: false }"
                            :content-props="{ align: 'start' }"
                        >
                            <template #trigger>
                                <Button size="icon-sm" variant="ghost" class="cursor-pointer">
                                    <BreadcrumbEllipsis />
                                </Button>
                            </template>
                        </DropdownMenuRoot>
                    </template>

                    <template v-else>
                        <template v-if="item.kind === 'page'">
                            <BreadcrumbPage class="cursor-default">
                                {{ resolveText(item.label) }}
                            </BreadcrumbPage>
                        </template>
                        <template v-if="item.kind === 'link'">
                            <BreadcrumbLink as-child>
                                <NuxtLink :to="item.to">
                                    {{ resolveText(item.label) }}
                                </NuxtLink>
                            </BreadcrumbLink>
                        </template>
                    </template>
                </BreadcrumbItem>
                <BreadcrumbSeparator v-if="index < slicedBreadcrumbs.length - 1" />
            </template>
        </BreadcrumbList>
    </Breadcrumb>
</template>
