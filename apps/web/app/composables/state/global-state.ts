export const useGlobalState = createGlobalState(() => {
    const BREADCRUMB_OVERRIDES = useState<Record<string, string>>(NuxtKeys.GlobalState, () => ({}));

    return {
        BREADCRUMB_OVERRIDES,
    };
});
