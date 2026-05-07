<script setup lang="ts">
    import type { UserRole } from "#shared/utils/schemas/types";

    interface Props {
        role?: UserRole;
    }

    withDefaults(defineProps<Props>(), {
        role: "sudo",
    });

    const auth = useAuth();
</script>

<template>
    <template v-if="auth.data.value?.user.role === role">
        <slot />
    </template>
</template>
