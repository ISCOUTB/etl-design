<script setup lang="ts">
    import { WandSparkles } from "lucide-vue-next";
    import { v7 } from "uuid";
    import { toast } from "vue-sonner";
    import { z } from "zod";

    const { $logger } = useNuxtApp();
    const {
        state: { project },
        tables,
        queryBuilder,
    } = useProject();

    const { locale } = useI18n();
    const focused = useWindowFocus();
    const webNotification = useWebNotification({
        dir: "auto",
        renotify: true,
        lang: locale.value,
    });

    const qb = useQueryBuilder();

    const QueryCompletion = z.object({
        import_name: z.string(),
        tree: GroupNode,
        columns: z.array(ColumnSelection),
    });

    const errorToast = useErrorToast();
    const modal = useModal();
    const [loading] = useToggle(false);

    function handleGenerate() {
        modal.dispatch.loadComponent({
            loader: () =>
                import("@/components/project/query-builder/ProjectQueryBuilderGenerateModal.vue"),
            key: ModalKeys.Projects.QueryBuilder.Generate,
            props: {
                onSubmit(message) {
                    $fetch("/api/schemas/query-builder/generate", {
                        method: "POST",
                        body: {
                            projectId: project.value.id,
                            userMessage: message,
                        },
                        onRequest() {
                            loading.value = true;
                            toast.success(
                                $t(
                                    "projects.id.sections.query_builder.generate.events.request_sent.title",
                                ),
                                {
                                    description: $t(
                                        "projects.id.sections.query_builder.generate.events.request_sent.description",
                                    ),
                                },
                            );
                        },
                    })
                        .then(({ response }) => {
                            const parsedResponse = deepParseJSON(response);

                            if (typeof parsedResponse !== "object") {
                                return;
                            }

                            const completion = QueryCompletion.safeParse(parsedResponse);
                            if (!completion.success) {
                                const options = errorToast.handle(
                                    ResponseCodesRecord.Server.Project.QueryBuilder.GenerateError,
                                );

                                if (!focused.value) {
                                    webNotification.show({
                                        title: options.title,
                                        body: options.description?.toString(),
                                        icon: "/icon.jpeg",
                                        tag: `project:query-builder:error:${v7()}`,
                                    });
                                }

                                return;
                            }

                            const { data } = completion;
                            const matchedSchema = tables.state.value.tableSchemas.find(
                                (table) => table.import_name === data.import_name,
                            );

                            let imported = false;
                            function doImport() {
                                if (imported) {
                                    return;
                                }

                                imported = true;
                                if (matchedSchema) {
                                    queryBuilder.state.schema.value = matchedSchema;
                                }

                                qb.dispatch.reset();
                                qb.state.whereTree.value = data.tree;

                                if (data.columns.length) {
                                    qb.state.selectedCols.value = data.columns;
                                    return;
                                }

                                qb.dispatch.selectAllColumns();
                            }

                            toast.success(
                                $t(
                                    "projects.id.sections.query_builder.generate.events.query_created.title",
                                ),
                                {
                                    description: $t(
                                        "projects.id.sections.query_builder.generate.events.query_created.description",
                                    ),
                                    duration: 10000,
                                    onAutoClose: doImport,
                                    onDismiss: () => (imported = true),
                                    action: {
                                        label: $t(
                                            "projects.id.sections.query_builder.generate.events.query_created.action",
                                        ),
                                        onClick: doImport,
                                    },
                                },
                            );

                            if (!focused.value) {
                                webNotification.show({
                                    title: $t(
                                        "projects.id.sections.query_builder.generate.events.query_created.title",
                                    ),
                                    body: $t(
                                        "projects.id.sections.query_builder.generate.events.query_created.description",
                                    ),
                                    icon: "/icon.jpeg",
                                    tag: `project:query-builder:success:${v7()}`,
                                });
                            }
                        })
                        .catch((error) => $logger.warn(error))
                        .finally(() => (loading.value = false));
                },
            },
        });
    }
</script>

<template>
    <Button variant="secondary" class="cursor-pointer" :disabled="loading" @click="handleGenerate">
        <template v-if="!loading">
            <WandSparkles />
        </template>
        <template v-else>
            <Spinner />
        </template>
        {{ $t("projects.id.sections.query_builder.generate.button") }}
    </Button>
</template>
