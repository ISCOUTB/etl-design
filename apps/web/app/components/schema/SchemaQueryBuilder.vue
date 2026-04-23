<script setup lang="ts">
    import { Rocket } from "lucide-vue-next";
    import { FetchError } from "ofetch";

    const { $logger } = useNuxtApp();

    const errorToast = useErrorToast();

    const qb = useQueryBuilder();
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
            .then((response) => $logger.log(response))
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
                <CardTitle> Execute Query </CardTitle>
                <CardDescription>
                    Lorem ipsum dolor sit amet consectetur, adipisicing elit. Necessitatibus, veniam
                    molestiae nam dolorum labore eum facere itaque nihil incidunt at autem illo
                    accusantium aperiam sit assumenda ipsa, perspiciatis maiores. Illo.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div class="flex justify-end">
                    <Button
                        variant="outline"
                        :disabled="loading"
                        class="cursor-pointer"
                        @click="handleExecute"
                    >
                        <UtilsLoading :loading="loading">
                            <Rocket />
                        </UtilsLoading>
                        Execute
                    </Button>
                </div>
            </CardContent>
        </Card>
    </div>
</template>
