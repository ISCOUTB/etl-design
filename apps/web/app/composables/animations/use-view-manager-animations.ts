export default function () {
    const { $gsap } = useNuxtApp();
    const utils = useAnimationsUtils();

    function onPanelEnter(element: Element, done: () => void) {
        if (utils.noAnimations.value) {
            done();
            return;
        }

        $gsap.fromTo(
            element,
            { autoAlpha: 0, y: 10 },
            {
                autoAlpha: 1,
                y: 0,
                duration: 0.18,
                ease: "power2.out",
                clearProps: "opacity,visibility,transform",
                onComplete: done,
            },
        );
    }

    function onPanelLeave(element: Element, done: () => void) {
        if (utils.noAnimations.value) {
            done();
            return;
        }

        $gsap.to(element, {
            autoAlpha: 0,
            y: -8,
            duration: 0.12,
            ease: "power2.in",
            onComplete: done,
        });
    }

    return { onPanelEnter, onPanelLeave };
}
