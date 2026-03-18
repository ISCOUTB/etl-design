export default function () {
    const { $gsap } = useNuxtApp();

    function onIconEnter(el: Element, done: () => void) {
        $gsap.fromTo(
            el,
            { scale: 0.6, opacity: 0, rotate: -15 },
            {
                scale: 1,
                opacity: 1,
                rotate: 0,
                duration: 0.3,
                ease: "back.out(1.8)",
                onComplete: done,
            },
        );
    }

    function onIconLeave(el: Element, done: () => void) {
        $gsap.to(el, {
            scale: 0.6,
            opacity: 0,
            duration: 0.2,
            ease: "power2.in",
            onComplete: done,
        });
    }

    function animateButtonClick(event: MouseEvent) {
        const target = event.target;
        if (!(target instanceof HTMLElement)) {
            return;
        }

        $gsap.to(target, {
            scale: 0.92,
            duration: 0.1,
            yoyo: true,
            repeat: 1,
            ease: "power1.inOut",
        });
    }

    return {
        onIconEnter,
        onIconLeave,
        animateButtonClick,
    };
}
