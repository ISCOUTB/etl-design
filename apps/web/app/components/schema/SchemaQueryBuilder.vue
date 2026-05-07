<script setup lang="ts">
    import { Rocket } from "lucide-vue-next";
    import { FetchError } from "ofetch";

    interface Props {
        rows?: Ref<Record<string, unknown>[]>;
    }

    const props = defineProps<Props>();

    const route = useRoute();
    const rows = useState<Record<string, unknown>[]>(
        NuxtKeys.Components.QueryBuilder.Rows(route.path),
        () => [],
    );

    if (props.rows) {
        syncRef(rows, props.rows, { direction: "both" });
    }

    const qb = useQueryBuilder();
    const errorToast = useErrorToast();
    const { project } = useProject();
    const [loading] = useToggle(false);
    function handleExecute() {
        loading.value = true;
        $fetch("/api/schemas/query-builder/execute", {
            method: "POST",
            body: {
                projectId: project.value.id,
                tree: qb.computed.queryTree.value,
            },
        })
            .then((response) => (rows.value = response.rows))
            .catch((error) => {
                if (error instanceof FetchError) {
                    errorToast.handle(error.statusText);
                }
            })
            .finally(() => (loading.value = false));
    }
</script>

<template>
    <div class="space-y-4">
        <SchemaQueryBuilderCardSelectColumn />
        <SchemaQueryBuilderCardConditions />
        <SchemaQueryBuilderCardOptions />
        <SchemaQueryBuilderPreview />
        <Card>
            <CardHeader>
                <div class="flex items-center justify-between">
                    <div class="space-y-1.5">
                        <CardTitle>
                            {{ $t("projects.id.sections.query_builder.execute.title") }}
                        </CardTitle>
                        <CardDescription>
                            {{ $t("projects.id.sections.query_builder.execute.description") }}
                        </CardDescription>
                    </div>

                    <div>
                        <Button
                            class="border border-green-300 bg-green-50 text-green-600 hover:bg-green-100 hover:text-green-700 disabled:bg-green-50 disabled:text-green-300 disabled:border-green-200 disabled:cursor-not-allowed transition-colors duration-200"
                            :disabled="loading"
                            @click="handleExecute"
                        >
                            <UtilsLoading :loading="loading">
                                <Rocket />
                            </UtilsLoading>
                            {{ $t("projects.id.sections.query_builder.execute.button") }}
                        </Button>
                    </div>
                </div>
            </CardHeader>
        </Card>
        <slot name="output" v-bind="{ rows, loading }" />
    </div>
</template>
