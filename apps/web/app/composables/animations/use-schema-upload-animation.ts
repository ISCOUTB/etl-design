export default function () {
    const { $gsap } = useNuxtApp();
    const utils = useAnimationsUtils();

    function onUploadStateEnter(element: Element, done: () => void) {
        if (utils.noAnimations.value) {
            done();
            return;
        }

        $gsap.fromTo(
            element,
            { autoAlpha: 0, y: 14, scale: 0.985 },
            {
                autoAlpha: 1,
                y: 0,
                scale: 1,
                duration: 0.28,
                ease: "power2.out",
                clearProps: "transform,opacity,visibility",
                onComplete: done,
            },
        );
    }

    function onUploadStateLeave(element: Element, done: () => void) {
        if (utils.noAnimations.value) {
            done();
            return;
        }

        $gsap.to(element, {
            autoAlpha: 0,
            y: -10,
            scale: 0.99,
            duration: 0.2,
            ease: "power2.in",
            onComplete: done,
        });
    }

    function animateDropzoneHover(element: Element | undefined | null, isOver: boolean) {
        if (utils.noAnimations.value || !element) {
            return;
        }

        $gsap.killTweensOf(element);
        $gsap.to(element, {
            scale: isOver ? 1.01 : 1,
            duration: 0.18,
            ease: "power2.out",
        });
    }

    return {
        onUploadStateEnter,
        onUploadStateLeave,
        animateDropzoneHover,
    };
}
