export default function () {
    const { $gsap } = useNuxtApp();
    const utils = useAnimationsUtils();

    function onStateEnter(element: Element, done: () => void) {
        if (utils.noAnimations.value) {
            done();
            return;
        }

        $gsap.fromTo(
            element,
            { autoAlpha: 0, y: 6 },
            { autoAlpha: 1, y: 0, duration: 0.1, ease: "power2.out", onComplete: done },
        );
    }

    function onStateLeave(element: Element, done: () => void) {
        if (utils.noAnimations.value) {
            done();
            return;
        }

        $gsap.to(element, {
            autoAlpha: 0,
            y: -4,
            duration: 0.1,
            ease: "power2.in",
            onComplete: done,
        });
    }

    function onItemEnter(element: Element, done: () => void) {
        if (utils.noAnimations.value) {
            done();
            return;
        }

        $gsap.fromTo(
            element,
            { autoAlpha: 0, y: 8 },
            { autoAlpha: 1, y: 0, duration: 0.1, ease: "power2.out", onComplete: done },
        );
    }

    function onItemLeave(element: Element, done: () => void) {
        if (utils.noAnimations.value) {
            done();
            return;
        }

        $gsap.to(element, {
            autoAlpha: 0,
            y: -6,
            duration: 0.1,
            ease: "power1.in",
            onComplete: done,
        });
    }

    return {
        onStateEnter,
        onStateLeave,
        onItemEnter,
        onItemLeave,
    };
}
