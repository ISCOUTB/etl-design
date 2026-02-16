<script setup lang="ts">
    const auth = useAuth();
</script>

<template>
    <div>
        <Button @click="auth.signIn('credentials')"> SignIn </Button>
        <Button v-if="auth.status.value === 'authenticated'" @click="auth.signOut()">
            Sign out
        </Button>
        <pre>{{ auth.data.value }}</pre>
    </div>
</template>
