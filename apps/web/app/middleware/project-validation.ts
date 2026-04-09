import { FetchError } from "ofetch";

export default defineNuxtRouteMiddleware(async (to) => {
    const auth = useAuth();
    const { $api, $localePath } = useNuxtApp();

    const projectId = to.params.id?.toString();

    if (!projectId) {
        return navigateTo($localePath({ name: "index" }));
    }

    if (!auth.data.value?.user) {
        return navigateTo($localePath({ name: "auth-sign-in" }));
    }

    const KEY = NuxtKeys.Projects.SharedState(projectId);
    const sharedState = useState<ResponseProject | undefined>(KEY);

    try {
        const response = await $api(`/projects/id/${projectId}`);
        const parsedResponse = ResponseProjectSchema.safeParse(response);

        if (!parsedResponse.success) {
            return navigateTo(
                $localePath({
                    name: "index",
                    query: { error: ResponseCodesRecord.Server.BadPayload },
                }),
            );
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
