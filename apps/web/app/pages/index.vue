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

    const auth = useAuth();
</script>

<template>
    <div>
        Lorem ipsum dolor sit amet consectetur adipisicing elit. Vitae maxime molestias provident
        esse earum ratione, sint magnam architecto officiis rem aliquid, impedit, nam consequatur
        similique debitis perspiciatis numquam eius laudantium!

        <pre>
            {{ auth.data.value?.accessToken }}
        </pre>
    </div>
</template>
