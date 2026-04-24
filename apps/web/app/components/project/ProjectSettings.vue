<script setup lang="ts">
    import { ExternalLink, Pencil, Trash2, TriangleAlert } from "lucide-vue-next";

    const { project } = useProject();

    const modal = useModal();
    const config = useAppConfig();

    function deleteProject() {
        modal.dispatch.loadComponent({
            loader: () => import("@/components/project/ProjectDeleteConfirmationModal.vue"),
            key: ModalKeys.Projects.Delete.ConfirmationModal,
            kind: "alert-dialog",
            props: {
                project,
            },
        });
    }
</script>

<template>
    <div class="flex flex-col gap-8">
        <section class="space-y-5">
            <div class="space-y-1">
                <h3 class="text-sm font-medium text-foreground">
                    {{ $t("projects.id.sections.settings.overview.title") }}
                </h3>
                <p class="text-sm text-muted-foreground">
                    {{ $t("projects.id.sections.settings.overview.description") }}
                </p>
            </div>

            <Item v-if="project" variant="outline" class="p-5 rounded-lg">
                <ItemContent>
                    <ItemTitle>
                        {{ $t("projects.id.sections.settings.edit.title") }}
                    </ItemTitle>
                    <ItemDescription>
                        {{ $t("projects.id.sections.settings.edit.description") }}
                    </ItemDescription>
                </ItemContent>
                <ItemActions>
                    <Button variant="outline" as-child>
                        <NuxtLink
                            :to="
                                $localeRoute({
                                    name: 'projects-id-edit',
                                    params: { id: project.id },
                                    query: {
                                        [config.constants.CALLBACK_KEY]: $route.fullPath,
                                    },
                                })
                            "
                        >
                            <Pencil class-name="size-4" />
                            <span>{{ $t("projects.id.sections.settings.edit.label") }}</span>
                        </NuxtLink>
                    </Button>
                </ItemActions>
            </Item>
        </section>

        <section class="space-y-5">
            <div class="space-y-1">
                <h3 class="text-sm font-medium text-foreground">
                    {{ $t("projects.id.sections.settings.ownership.title") }}
                </h3>
                <p class="text-sm text-muted-foreground">
                    {{ $t("projects.id.sections.settings.ownership.description") }}
                </p>
            </div>

            <Item variant="outline" class="p-5 rounded-lg">
                <ItemContent>
                    <ItemTitle>
                        {{ $t("projects.id.sections.settings.ownership.transfer.title") }}
                    </ItemTitle>
                    <ItemDescription>
                        {{ $t("projects.id.sections.settings.ownership.transfer.description") }}
                    </ItemDescription>
                </ItemContent>
                <ItemActions>
                    <NuxtLink as-child class="cursor-not-allowed">
                        <Button disabled variant="outline">
                            <ExternalLink class="size-4" />
                            <span>
                                {{ $t("projects.id.sections.settings.ownership.transfer.label") }}
                            </span>
                        </Button>
                    </NuxtLink>
                </ItemActions>
            </Item>
        </section>

        <Separator />

        <section class="space-y-5">
            <div class="flex items-center space-x-2">
                <TriangleAlert class="size-4 text-destructive" />
                <h3 class="text-sm font-medium text-destructive">
                    {{ $t("projects.id.sections.settings.danger_zone.title") }}
                </h3>
            </div>

            <Item variant="outline" class="p-5 rounded-lg border-destructive/30">
                <ItemContent>
                    <ItemTitle>
                        {{ $t("projects.id.sections.settings.delete.title") }}
                    </ItemTitle>
                    <ItemDescription>
                        {{ $t("projects.id.sections.settings.delete.description") }}
                    </ItemDescription>
                </ItemContent>
                <ItemActions>
                    <Button variant="destructive" @click="deleteProject">
                        <Trash2 class="size-4" />
                        <span>
                            {{ $t("projects.id.sections.settings.delete.label") }}
                        </span>
                    </Button>
                </ItemActions>
            </Item>
        </section>
    </div>
</template>
