import { FetchError } from "ofetch";

export default defineNuxtRouteMiddleware(async (to) => {
    const auth = useAuth();
    const { $localePath } = useNuxtApp();

    const projectId = to.params.id;
    if (!auth.data.value?.user) {
        return navigateTo($localePath({ name: "auth-sign-in" }));
    }

    const api = useApi();
    try {
        const response = await api(`/projects/id/${projectId}`);
        const parsedResponse = ResponseProjectSchema.safeParse(response);

        if (!parsedResponse.success) {
            return navigateTo(
                $localePath({
                    name: "index",
                    query: { error: ResponseCodesRecord.Server.BadPayload },
                }),
            );
        }
    } catch (error) {
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
    }
});
