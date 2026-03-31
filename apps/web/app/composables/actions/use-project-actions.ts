export default function () {
    const { $api } = useNuxtApp();
    const [loading] = useToggle(false);

    async function handleDeleteProject(projectId: ResponseProject["id"]) {
        try {
            const response = await $api(`/projects/${projectId}/flush`, {
                method: "DELETE",
            });

            return response;
        } finally {
            loading.value = false;
        }
    }

    return {
        state: {
            loading,
        },
        handleDeleteProject,
    };
}
