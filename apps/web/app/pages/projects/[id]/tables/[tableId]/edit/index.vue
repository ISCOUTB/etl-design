<script setup lang="ts">
    definePageMeta({
        title: "layouts.title",
        layout: "sidebar",
    });

    const { tables } = useProjectTabsSharedState();
</script>

<template>
    <div>
        {{ tables }}
    </div>
</template>
