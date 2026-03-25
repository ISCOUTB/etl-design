<script setup lang="ts">
    import { Toaster } from "vue-sonner";

    const { $gsap } = useNuxtApp();
    const { finalizePendingLocaleChange } = useI18n();
    const utils = useAnimationsUtils();

    async function onBeforeEnter(element: Element) {
        await finalizePendingLocaleChange();

        if (utils.noAnimations.value) {
            return;
        }

        $gsap.fromTo(element, { opacity: 0 }, { opacity: 1, duration: 0.3 });
    }

    function onLeave(element: Element, done: () => void) {
        $gsap.to(element, { opacity: 0, duration: 0.3, onComplete: done });
    }
</script>

<template>
    <div>
        <NuxtLayout>
            <NuxtLoadingIndicator />
            <NuxtPage :transition="{ css: false, mode: 'out-in', onBeforeEnter, onLeave }" />
            <Toaster rich-colors />
        </NuxtLayout>
    </div>
</template>
