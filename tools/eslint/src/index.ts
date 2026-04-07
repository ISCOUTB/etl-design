import type { Rules } from "@antfu/eslint-config";
import { antfu } from "@antfu/eslint-config";
import { merge } from "es-toolkit/compat";
import depend from "eslint-plugin-depend";
import sonarjs from "eslint-plugin-sonarjs";
// @ts-expect-error "The plugin does not come with types"
import lodash from "eslint-plugin-you-dont-need-lodash-underscore";

interface PluginOptions {
    depend?: boolean;
    sonarjs?: boolean;
    lodash?: boolean;
}

interface PluginConfig {
    enabled: boolean;
    name: string;
    plugin: any;
    rules: Record<string, unknown>;
}

export function withConfig(
    config?: Parameters<typeof antfu>[0],
    plugins: PluginOptions = {},
): ReturnType<typeof antfu> {
    const {
        depend: _enableDepend = true,
        lodash: _enableLodash = true,
        sonarjs: _enableSonar = true,
    } = plugins;

    const pluginConfigs: PluginConfig[] = [
        {
            enabled: _enableDepend,
            name: "depend",
            plugin: depend,
            rules: { "depend/ban-dependencies": "error" },
        },
        {
            enabled: _enableSonar,
            name: "sonarjs",
            plugin: sonarjs,
            rules: sonarjs.configs.recommended.rules,
        },
        {
            enabled: _enableLodash,
            name: "you-dont-need-lodash-underscore",
            plugin: lodash,
            rules: lodash.configs.compatible.rules,
        },
    ];

    const { plugins: activePlugins, rules: activeRules } = pluginConfigs
        .filter((config) => config.enabled)
        .reduce(
            (acc, config) => ({
                plugins: { ...acc.plugins, [config.name]: config.plugin },
                rules: { ...acc.rules, ...config.rules },
            }),
            { plugins: {}, rules: {} } as {
                plugins: Record<string, unknown>;
                rules: Record<string, unknown>;
            },
        );

    const defaultConfig = {
        stylistic: {
            quotes: "double",
            indent: 4,
            semi: true,
        },
        rules: {
            "yaml/indent": ["warn", 4, { indicatorValueIndent: 2 }],
            "style/arrow-parens": ["warn", "always"],
            "style/operator-linebreak": ["off"],
            "style/brace-style": ["warn", "1tbs"],
            "style/quote-props": ["error", "as-needed"],
        },
    };

    return antfu(merge({}, defaultConfig, config), {
        rules: activeRules as Rules,
        plugins: activePlugins,
    });
}
