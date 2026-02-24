<script setup lang="ts">
    interface Props {
        emptyString?: string;
    }

    withDefaults(defineProps<Props>(), {
        emptyString: "---",
    });
</script>

<template>
    <div class="text-muted-foreground">{{ emptyString }}</div>
</template>
