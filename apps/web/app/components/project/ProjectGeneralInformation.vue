<script setup lang="ts">
    import type { ResponseProjectSchema } from "#shared/utils/schemas/api";
    import type { z } from "zod";
    import {
        Calendar,
        Cloud,
        Copy,
        Database,
        Globe,
        Hash,
        Plug,
        Server,
        TriangleAlert,
        User,
    } from "lucide-vue-next";
    import { cn } from "@/lib/utils";

    interface Props {
        project: MaybeRefOrGetter<z.infer<typeof ResponseProjectSchema> | undefined>;
    }

    const props = defineProps<Props>();
    const project = computed(() => toValue(props.project));

    const validConnectionString = computed(
        () =>
            project.value &&
            project.value.db_user &&
            project.value.db_password &&
            project.value.db_host &&
            project.value.db_port &&
            project.value.db_name,
    );
    const connectionString = computed(() => {
        if (!project.value) {
            return;
        }

        return `postgresql://${project.value.db_user}:${project.value.db_password}@${project.value.db_host}:${project.value.db_port}/${project.value.db_name}?${project.value.db_params}`;
    });

    const clipboard = useClipboard();
</script>

<template>
    <div v-if="project" class="flex flex-col gap-8">
        <section>
            <h3 class="mb-1 text-sm font-medium text-foreground">
                {{ $t("projects.id.sections.general_information.overview.title") }}
            </h3>
            <p class="mb-5 text-sm text-muted-foreground">
                {{ $t("projects.id.sections.general_information.overview.description") }}
            </p>

            <div class="rounded-lg border">
                <div class="divide-y px-5">
                    <div class="flex items-center justify-between py-3">
                        <div class="flex items-center space-x-3 text-muted-foreground">
                            <Hash class="size-4 shrink-0" />
                            <span class="text-sm">
                                {{ $t("projects.id.sections.general_information.fields.id") }}
                            </span>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span class="font-mono text-sm text-foreground">
                                {{ project.id }}
                            </span>
                            <Button
                                variant="ghost"
                                size="icon"
                                class="size-8"
                                @click="clipboard.copy(project.id)"
                            >
                                <Copy />
                                <span class="sr-only">Copy ID</span>
                            </Button>
                        </div>
                    </div>

                    <div class="flex items-center justify-between py-3">
                        <div class="flex items-center gap-3 text-muted-foreground">
                            <Cloud class="size-4 shrink-0" />
                            <span class="text-sm">
                                {{ $t("projects.create.fields.provider.label") }}
                            </span>
                        </div>

                        <Badge
                            v-if="project.provider?.length"
                            variant="outline"
                            class="space-x-1.5 font-normal"
                        >
                            {{ project.provider }}
                        </Badge>
                        <TriangleAlert class="size-6 text-yellow-500/50 dark:text-orange-500/60" />
                    </div>

                    <ProjectGeneralInformationRow
                        :icon="Calendar"
                        label="projects.id.sections.general_information.fields.created_at"
                        :value="
                            new Date(project.created_at).toLocaleDateString($i18n.locale, {
                                month: 'long',
                                day: 'numeric',
                                year: 'numeric',
                            })
                        "
                    />
                </div>
            </div>
        </section>

        <section>
            <h3 class="mb-1 text-sm font-medium text-foreground">
                {{ $t("projects.id.sections.general_information.connection_details.title") }}
            </h3>
            <p class="mb-5 text-sm text-muted-foreground">
                {{ $t("projects.id.sections.general_information.connection_details.description") }}
            </p>

            <div class="rounded-lg border">
                <div class="divide-y px-5">
                    <ProjectGeneralInformationRow
                        copyable
                        :icon="Server"
                        label="projects.create.fields.db_host.label"
                        :value="project.db_host"
                    />

                    <ProjectGeneralInformationRow
                        :icon="Plug"
                        label="projects.create.fields.db_port.label"
                        :value="project.db_port?.toString()"
                    />

                    <ProjectGeneralInformationRow
                        copyable
                        :icon="User"
                        label="projects.create.fields.db_user.label"
                        :value="project.db_user"
                    />

                    <ProjectGeneralInformationRow
                        copyable
                        :icon="Database"
                        label="projects.create.fields.db_name.label"
                        :value="project.db_name"
                    />

                    <ProjectGeneralInformationRow
                        :icon="Globe"
                        label="projects.create.fields.db_params.label"
                        :value="project.db_params"
                        class="font-mono"
                    />
                </div>
            </div>
        </section>

        <section>
            <h3 class="mb-1 text-sm font-medium text-foreground">
                {{ $t("projects.id.sections.general_information.connection_string.title") }}
            </h3>
            <p class="mb-5 text-sm text-muted-foreground">
                {{ $t("projects.id.sections.general_information.connection_string.description") }}
            </p>

            <div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-3">
                <code
                    :class="
                        cn(
                            'flex-1 truncate font-mono text-sm text-foreground',
                            !validConnectionString && 'line-through text-muted-foreground italic',
                        )
                    "
                >
                    {{ connectionString }}
                </code>
                <Button
                    v-if="connectionString"
                    variant="outline"
                    size="sm"
                    class="shrink-0"
                    @click="
                        () => {
                            if (connectionString) {
                                clipboard.copy(connectionString);
                            }
                        }
                    "
                >
                    <Copy class="size-3.5" />
                </Button>
            </div>
        </section>
    </div>
</template>
