import { diag, DiagConsoleLogger, DiagLogLevel } from "@opentelemetry/api";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import * as otelResources from "@opentelemetry/resources";
import { BatchSpanProcessor, NodeTracerProvider } from "@opentelemetry/sdk-trace-node";
import {
    ATTR_SERVICE_NAME,
    ATTR_SERVICE_VERSION,
    SEMRESATTRS_DEPLOYMENT_ENVIRONMENT,
} from "@opentelemetry/semantic-conventions";
import { trace } from "@opentelemetry/api";

type ConfigureTracingParams = {
    enabled: boolean;
    serviceName: string;
    serviceVersion: string;
    environment: string;
    endpoint: string;
    debug?: boolean;
};

let provider: NodeTracerProvider | null = null;
let isTracingInitialized = false;

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

export async function configureOtelTracing(params: ConfigureTracingParams): Promise<void> {
    if (!params.enabled || isTracingInitialized) {
        return;
    }

    if (params.debug) {
        diag.setLogger(new DiagConsoleLogger(), DiagLogLevel.ERROR);
    }

    const resource = createResource({
        [ATTR_SERVICE_NAME]: params.serviceName,
        [ATTR_SERVICE_VERSION]: params.serviceVersion,
        [SEMRESATTRS_DEPLOYMENT_ENVIRONMENT]: params.environment,
    });

    provider = new NodeTracerProvider({
        resource,
        spanProcessors: [
            new BatchSpanProcessor(
                new OTLPTraceExporter({
                    url: `${params.endpoint.replace(/\/$/, "")}/v1/traces`,
                }),
            ),
        ],
    });

    provider.register();

    isTracingInitialized = true;
}

export function getGrpcTracer(name = "formula_parser.grpc") {
    return trace.getTracer(name);
}

export async function shutdownOtelTracing(): Promise<void> {
    if (!provider) {
        return;
    }

    await provider.shutdown();
    provider = null;
    isTracingInitialized = false;
}
