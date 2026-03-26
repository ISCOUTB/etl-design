export default function () {
    const [loading] = useToggle(false);
    const api = useApi();

    async function handleDeleteProject(projectId: ResponseProject["id"]) {
        try {
            const response = await api(`/projects/${projectId}/flush`, {
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
