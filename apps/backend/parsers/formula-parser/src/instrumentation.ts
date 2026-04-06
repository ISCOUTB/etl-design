import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import * as otelResources from "@opentelemetry/resources";
import { BatchSpanProcessor, NodeTracerProvider } from "@opentelemetry/sdk-trace-node";
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from "@opentelemetry/semantic-conventions";
import { logger } from "@/utils/logger";

function createResource(attributes: Record<string, string>) {
    const resources = otelResources as {
        resourceFromAttributes?: (attrs: Record<string, string>) => unknown;
        Resource?: new (attrs: Record<string, string>) => unknown;
    };

    if (typeof resources.resourceFromAttributes === "function") {
        return resources.resourceFromAttributes(attributes);
    }

    if (typeof resources.Resource === "function") {
        return new resources.Resource(attributes);
    }

    throw new Error("OpenTelemetry resources API is not available in this runtime");
}

export function setupTelemetry(options: {
    serviceName: string;
    serviceVersion: string;
    endpoint: string;
    enabled: boolean;
}) {
    if (!options.enabled) {
        return;
    }

    const exporter = new OTLPTraceExporter({ url: `${options.endpoint}/v1/traces` });
    logger.info("exporter created", {
        uri: `${options.endpoint}/v1/traces`,
    });

    const provider = new NodeTracerProvider({
        resource: createResource({
            [ATTR_SERVICE_NAME]: options.serviceName,
            [ATTR_SERVICE_VERSION]: options.serviceVersion,
        }),
        spanProcessors: [new BatchSpanProcessor(exporter)],
    });

    provider.register();
}
