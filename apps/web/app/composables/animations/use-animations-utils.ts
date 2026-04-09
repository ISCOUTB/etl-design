export default function () {
    const preferredMotion = usePreferredReducedMotion();
    const noAnimations = computed(() => preferredMotion.value === "reduce");

    return {
        noAnimations,
    };
}
