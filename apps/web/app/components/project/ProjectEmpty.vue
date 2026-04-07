<script setup lang="ts">
    import { Folder, Plus } from "lucide-vue-next";
</script>

<template>
    <Empty>
        <EmptyHeader>
            <EmptyMedia>
                <Folder class="size-4" />
            </EmptyMedia>
            <EmptyTitle>
                {{ $t("projects.view.empty.header.title") }}
            </EmptyTitle>
            <EmptyDescription>
                {{ $t("projects.view.empty.header.description") }}
            </EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
            <NuxtLink as-child :to="$localeRoute({ name: 'projects-create' })">
                <Button>
                    <Plus class="size-4" />
                    <span>{{ $t("projects.create.header.title") }}</span>
                </Button>
            </NuxtLink>
        </EmptyContent>
    </Empty>
</template>
