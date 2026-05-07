<script setup lang="ts">
    import { Sonner } from "@/components/ui/sonner";

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
            <NuxtLoadingIndicator color="var(--accent)" />
            <NuxtPage :transition="{ css: false, mode: 'out-in', onBeforeEnter, onLeave }" />
            <Sonner rich-colors />
            <NuxtPwaManifest />
        </NuxtLayout>
    </div>
</template>
