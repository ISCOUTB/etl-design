export default function () {
    const { $gsap } = useNuxtApp();

    function onEnter(element: Element, done: () => void) {
        $gsap.fromTo(
            element,
            { height: 0, opacity: 0, overflow: "hidden" },
            { height: "auto", opacity: 1, duration: 0.4, ease: "power2.out", onComplete: done },
        );
    }

    function onLeave(element: Element, done: () => void) {
        $gsap.to(element, {
            height: 0,
            opacity: 0,
            duration: 0.3,
            ease: "power2.in",
            onComplete: done,
        });
    }

    return {
        onEnter,
        onLeave,
    };
}
