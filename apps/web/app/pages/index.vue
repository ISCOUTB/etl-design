<script setup lang="ts">
    definePageMeta({
        title: "layouts.title",
        layout: "sidebar",
        i18n: {
            paths: {
                en: "/",
            },
        },
    });

    const { on } = useRouteError();
    const errorToast = useErrorToast();
    onMounted(() => {
        on("error:unauthorized", () => {
            errorToast.handle(ResponseCodesRecord.Server.UnAuthorized);
        });

        on("error:project-not-found", () => {
            errorToast.handle(ResponseCodesRecord.Server.Project.NotFound);
        });
    });
</script>

<template>
    <div>
        Lorem ipsum dolor sit amet consectetur adipisicing elit. Vitae maxime molestias provident
        esse earum ratione, sint magnam architecto officiis rem aliquid, impedit, nam consequatur
        similique debitis perspiciatis numquam eius laudantium!
    </div>
</template>
