import type { EventBusKey } from "@vueuse/core";

export const PROJECTS_REFRESH_BUS_KEY: EventBusKey<void> = Symbol("projects:refresh");
