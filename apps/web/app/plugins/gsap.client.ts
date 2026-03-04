import gsap from "gsap";

export default defineNuxtPlugin({
    name: "gsap",
    parallel: true,
    setup() {
        return {
            provide: {
                gsap,
            },
        };
    },
});
