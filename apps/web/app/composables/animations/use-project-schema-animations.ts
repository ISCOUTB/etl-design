export default function () {
    const { $gsap } = useNuxtApp();

    function onSchemaEnter(element: Element, done: () => void) {
        if (!(element instanceof HTMLElement)) {
            done();
            return;
        }

        $gsap.fromTo(
            element,
            {
                autoAlpha: 0,
                y: 16,
                scale: 0.985,
                filter: "blur(6px)",
            },
            {
                autoAlpha: 1,
                y: 0,
                scale: 1,
                filter: "blur(0px)",
                duration: 0.3,
                ease: "power2.out",
                onComplete: done,
            },
        );
    }

    function onSchemaLeave(element: Element, done: () => void) {
        if (!(element instanceof HTMLElement)) {
            done();
            return;
        }

        $gsap.to(element, {
            autoAlpha: 0,
            y: -8,
            scale: 0.99,
            filter: "blur(4px)",
            duration: 0.2,
            ease: "power2.in",
            onComplete: done,
        });
    }

    return {
        onSchemaEnter,
        onSchemaLeave,
    };
}
