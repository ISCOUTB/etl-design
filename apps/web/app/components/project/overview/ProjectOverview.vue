<script setup lang="ts">
    import { buildPgConnectionString } from "#shared/utils/pg-connection-string";
    import {
        Calendar,
        Cloud,
        Copy,
        Database,
        ExternalLink,
        Globe,
        Hash,
        Info,
        Plug,
        Server,
        User,
    } from "lucide-vue-next";
    import { toast } from "vue-sonner";

    const { project } = useProject();

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
    const config = useAppConfig();

    onMounted(() => {
        whenever(clipboard.copied, () => toast.success($t("common.clipboard.copied")), {
            immediate: true,
        });
    });
</script>

<template>
    <div class="flex flex-col gap-8">
        <section class="space-y-5">
            <div class="space-y-1">
                <h3 class="text-sm font-medium text-foreground">
                    {{ $t("projects.id.sections.overview.header.title") }}
                </h3>
                <p class="text-sm text-muted-foreground">
                    {{ $t("projects.id.sections.overview.header.description") }}
                </p>
            </div>

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

        <section class="space-y-5">
            <div class="flex items-center justify-between">
                <div class="space-y-1">
                    <h3 class="text-sm font-medium text-foreground">
                        {{ $t("projects.id.sections.overview.connection_details.title") }}
                    </h3>
                    <p class="text-sm text-muted-foreground">
                        {{ $t("projects.id.sections.overview.connection_details.description") }}
                    </p>
                </div>

                <div v-if="!project.db_host || !project.db_port">
                    <HoverCard>
                        <HoverCardTrigger as-child>
                            <div class="border border-border rounded-lg p-2">
                                <Info class="size-4.5 text-amber-500 dark:text-orange-400" />
                            </div>
                        </HoverCardTrigger>
                        <HoverCardContent align="end" class="w-96">
                            <Item class="p-0">
                                <ItemContent>
                                    <ItemTitle>
                                        {{
                                            $t(
                                                "projects.id.sections.overview.connection_details.warning.title",
                                            )
                                        }}
                                    </ItemTitle>
                                    <ItemDescription class="line-clamp-none">
                                        {{
                                            $t(
                                                "projects.id.sections.overview.connection_details.warning.description",
                                            )
                                        }}
                                    </ItemDescription>
                                </ItemContent>
                                <ItemActions>
                                    <Button variant="outline" as-child class="break-all">
                                        <NuxtLink
                                            :to="
                                                $localeRoute({
                                                    name: 'projects-id-edit',
                                                    params: { id: project.id },
                                                    query: {
                                                        [config.constants.CALLBACK_KEY]:
                                                            $route.fullPath,
                                                    },
                                                })
                                            "
                                        >
                                            <ExternalLink />
                                            {{
                                                $t(
                                                    "projects.id.sections.overview.connection_details.warning.action",
                                                )
                                            }}
                                        </NuxtLink>
                                    </Button>
                                </ItemActions>
                            </Item>
                        </HoverCardContent>
                    </HoverCard>
                </div>
            </div>

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

        <section class="space-y-5">
            <div class="space-y-1">
                <h3 class="text-sm font-medium text-foreground">
                    {{ $t("projects.id.sections.overview.connection_string.title") }}
                </h3>
                <p class="text-sm text-muted-foreground">
                    {{ $t("projects.id.sections.overview.connection_string.description") }}
                </p>
            </div>

            <div
                class="flex items-center justify-between gap-3 rounded-lg border bg-muted/50 px-4 py-3"
            >
                <template v-if="validConnectionString">
                    <SensitiveInfoInline :value="connectionString" class="text-foreground" />
                </template>
                <template v-else>
                    <code class="font-mono text-sm italic text-muted-foreground">
                        {{ connectionString }}
                    </code>
                </template>
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
