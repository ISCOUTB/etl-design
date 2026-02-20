<script setup lang="ts">
    definePageMeta({
        title: "layouts.title",
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
        <pre>{{ auth.data.value }}</pre>
        <Button v-if="auth.status.value === 'authenticated'" @click="auth.signOut()">
            Sign Out
        </Button>
    </div>
</template>
