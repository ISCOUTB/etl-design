<!-- eslint-disable vue/script-indent -->
<script setup lang="ts">
    import type { NuxtError } from "#app";
    import { HelpCircle, Search, ServerCrash, SquareArrowUpLeft } from "lucide-vue-next";

    interface Props {
        error: NuxtError;
    }

    interface Error {
        title: string;
        description: string;
        icon?: Components.LucideIconComponent;
    }

    const props = defineProps<Props>();
    const parsedError = computed(() => mapError(props.error.status));

    function mapError(statusCode: number | undefined): Error {
        switch (statusCode) {
            case 404: {
                return {
                    title: "errors.404.title",
                    description: "errors.404.description",
                    icon: Search,
                };
            }
            case 500: {
                return {
                    title: "errors.500.title",
                    description: "errors.500.description",
                    icon: ServerCrash,
                };
            }
            default: {
                return {
                    title: "errors.unknown.title",
                    description: "errors.unknown.description",
                    icon: HelpCircle,
                };
            }
        }
    }
</script>

<template>
    <NuxtLayout name="sidebar">
        <Empty>
            <EmptyHeader>
                <EmptyMedia v-if="parsedError.icon" variant="icon">
                    <component :is="parsedError.icon" />
                </EmptyMedia>
                <EmptyTitle>
                    {{ $t(parsedError.title) }}
                </EmptyTitle>
                <EmptyDescription>
                    {{ $t(parsedError.description) }}
                </EmptyDescription>
            </EmptyHeader>
            <EmptyContent>
                <Button variant="outline" as-child class="cursor-pointer">
                    <NuxtLink :to="$localeRoute({ name: 'index' })">
                        <SquareArrowUpLeft />
                        {{ $t("common.actions.go_home") }}
                    </NuxtLink>
                </Button>
            </EmptyContent>
        </Empty>
    </NuxtLayout>
</template>
