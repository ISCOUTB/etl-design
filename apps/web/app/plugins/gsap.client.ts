import { gsap } from "gsap";
import { Draggable, InertiaPlugin, Observer, ScrollTrigger } from "gsap/all";

export default defineNuxtPlugin({
    name: "gsap",
    parallel: true,
    setup() {
        gsap.registerPlugin(Draggable, InertiaPlugin, Observer, ScrollTrigger);

        return {
            provide: {
                gsap,
            },
        };
    },
});
