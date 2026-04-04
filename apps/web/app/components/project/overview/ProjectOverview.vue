<script setup lang="ts">
    import { buildPgConnectionString } from "#shared/utils/pg-connection-string";
    import {
        Calendar,
        Cloud,
        Copy,
        Database,
        Globe,
        Hash,
        Plug,
        Server,
        User,
    } from "lucide-vue-next";
    import { toast } from "vue-sonner";

    const {
        state: { project },
    } = useProject();

    const validConnectionString = computed(
        () => project && project.value.db_host && project.value.db_port,
    );
    const connectionString = computed(() => {
        if (!project || !validConnectionString.value) {
            return $t("projects.id.sections.overview.connection_string.invalid");
        }

        return buildPgConnectionString({
            user: project.value.db_user,
            password: project.value.db_password,
            host: project.value.db_host!,
            port: project.value.db_port!,
            database: project.value.db_name,
            params: project.value.db_params,
        });
    });

    const clipboard = useClipboard();

    onMounted(() => {
        whenever(clipboard.copied, () => toast.success($t("common.clipboard.copied")), {
            immediate: true,
        });
    });
</script>

<template>
    <div class="flex flex-col gap-8">
        <section>
            <h3 class="mb-1 text-sm font-medium text-foreground">
                {{ $t("projects.id.sections.overview.header.title") }}
            </h3>
            <p class="mb-5 text-sm text-muted-foreground">
                {{ $t("projects.id.sections.overview.header.description") }}
            </p>

            <div class="rounded-lg border">
                <div class="divide-y px-5">
                    <div class="flex items-center justify-between py-3">
                        <div class="flex items-center space-x-3 text-muted-foreground">
                            <Hash class="size-4 shrink-0" />
                            <span class="text-sm">
                                {{ $t("projects.id.sections.overview.fields.id") }}
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
                    </div>

                    <ProjectOverviewItem
                        no-sensitive
                        :icon="Calendar"
                        label="projects.id.sections.overview.fields.created_at"
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
                {{ $t("projects.id.sections.overview.connection_details.title") }}
            </h3>
            <p class="mb-5 text-sm text-muted-foreground">
                {{ $t("projects.id.sections.overview.connection_details.description") }}
            </p>

            <div class="rounded-lg border">
                <div class="divide-y px-5">
                    <ProjectOverviewItem
                        copyable
                        :icon="Server"
                        label="projects.create.fields.db_host.label"
                        :value="project.db_host"
                    />

                    <ProjectOverviewItem
                        copyable
                        :icon="Plug"
                        label="projects.create.fields.db_port.label"
                        :value="project.db_port?.toString()"
                    />

                    <ProjectOverviewItem
                        copyable
                        no-warning
                        :icon="User"
                        label="projects.create.fields.db_user.label"
                        :value="project.db_user"
                    />

                    <ProjectOverviewItem
                        copyable
                        no-warning
                        :icon="Database"
                        label="projects.create.fields.db_name.label"
                        :value="project.db_name"
                    />

                    <ProjectOverviewItem
                        copyable
                        no-warning
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
                {{ $t("projects.id.sections.overview.connection_string.title") }}
            </h3>
            <p class="mb-5 text-sm text-muted-foreground">
                {{ $t("projects.id.sections.overview.connection_string.description") }}
            </p>

            <div
                class="flex items-center justify-between gap-3 rounded-lg border bg-muted/50 px-4 py-3"
            >
                <SensitiveInfoInline :value="connectionString" class="text-foreground" />
                <Button
                    v-if="validConnectionString"
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
