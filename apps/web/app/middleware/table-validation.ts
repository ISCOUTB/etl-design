import { FetchError } from "ofetch";

export default defineNuxtRouteMiddleware(async (to) => {
    const auth = useAuth();
    const { $api, $localePath } = useNuxtApp();

    const projectId = to.params.id?.toString();
    const tableName = to.params.tableName?.toString();

    if (!projectId || !tableName) {
        return navigateTo($localePath({ name: "index" }));
    }

    if (!auth.data.value?.user) {
        return navigateTo($localePath({ name: "auth-sign-in" }));
    }

    const KEY = NuxtKeys.Projects.Tables.SharedState(projectId, tableName);
    const sharedState = useState<MongoRaw | undefined>(KEY);

    try {
        const response = await $api(`/schemas/${projectId}/raw`, {
            method: "GET",
            query: {
                table_name: tableName,
            },
        });
        const parsedResponse = MongoRawSchema.safeParse(response);

        if (!parsedResponse.success) {
            return navigateTo($localePath({ name: "projects-id", params: { id: projectId } }));
        }

        sharedState.value = parsedResponse.data;
    } catch (error) {
        clearNuxtData(KEY);

        if (error instanceof FetchError) {
            const parsedError = ApiErrorSchema.safeParse(error.data);
            if (!parsedError.success) {
                return navigateTo(
                    $localePath({
                        name: "index",
                        query: { error: ResponseCodesRecord.Server.UnknownError },
                    }),
                );
            }

            return navigateTo(
                $localePath({ name: "index", query: { error: parsedError.data.error } }),
            );
        }

        return navigateTo(
            $localePath({
                name: "index",
                query: { error: ResponseCodesRecord.Server.UnknownError },
            }),
        );
    }
});
