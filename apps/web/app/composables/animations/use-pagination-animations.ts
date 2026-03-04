export default function () {
    const { $gsap } = useNuxtApp();

    function onStateEnter(element: Element, done: () => void) {
        $gsap.fromTo(
            element,
            { autoAlpha: 0, y: 8 },
            { autoAlpha: 1, y: 0, duration: 0.22, ease: "power2.out", onComplete: done },
        );
    }

    function onStateLeave(element: Element, done: () => void) {
        $gsap.to(element, {
            autoAlpha: 0,
            y: -6,
            duration: 0.18,
            ease: "power2.in",
            onComplete: done,
        });
    }

    function onItemEnter(element: Element, done: () => void) {
        const i = Number((element as HTMLElement).dataset.index ?? 0);

        $gsap.set(element, { autoAlpha: 0, y: 15 });

        $gsap.to(element, {
            autoAlpha: 1,
            y: 0,
            duration: 0.4,
            delay: i * 0.05,
            ease: "power3.out",
            onComplete: done,
        });
    }

    function onItemLeave(element: Element, done: () => void) {
        $gsap.to(element, {
            autoAlpha: 0,
            y: -8,
            duration: 0.14,
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
