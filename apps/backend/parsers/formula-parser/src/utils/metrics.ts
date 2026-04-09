import http from "node:http";
import type { AddressInfo } from "node:net";
import {
    Counter,
    Histogram,
    collectDefaultMetrics,
    Registry,
    type Histogram as HistogramType,
} from "prom-client";
import { logger } from "@/utils/logger";

type MetricsServer = {
    server: http.Server;
    port: number;
};

const metricsRegistry = new Registry();
collectDefaultMetrics({ register: metricsRegistry });

type GrpcMetricBaseLabels = {
    grpc_type: string;
    grpc_service: string;
    grpc_method: string;
};

type GrpcMetricHandledLabels = GrpcMetricBaseLabels & {
    grpc_code: string;
};

const grpcServerStartedTotal = new Counter<"grpc_type" | "grpc_service" | "grpc_method">({
    name: "grpc_server_started_total",
    help: "Total number of RPCs started on the server.",
    labelNames: ["grpc_type", "grpc_service", "grpc_method"],
    registers: [metricsRegistry],
});

const grpcServerHandledTotal = new Counter<
    "grpc_type" | "grpc_service" | "grpc_method" | "grpc_code"
>({
    name: "grpc_server_handled_total",
    help: "Total number of RPCs completed on the server, regardless of success or failure.",
    labelNames: ["grpc_type", "grpc_service", "grpc_method", "grpc_code"],
    registers: [metricsRegistry],
});

const grpcServerMsgReceivedTotal = new Counter<"grpc_type" | "grpc_service" | "grpc_method">({
    name: "grpc_server_msg_received_total",
    help: "Total number of RPC stream messages received on the server.",
    labelNames: ["grpc_type", "grpc_service", "grpc_method"],
    registers: [metricsRegistry],
});

const grpcServerMsgSentTotal = new Counter<"grpc_type" | "grpc_service" | "grpc_method">({
    name: "grpc_server_msg_sent_total",
    help: "Total number of gRPC stream messages sent by the server.",
    labelNames: ["grpc_type", "grpc_service", "grpc_method"],
    registers: [metricsRegistry],
});

const grpcServerHandlingSeconds = new Histogram<"grpc_type" | "grpc_service" | "grpc_method">({
    name: "grpc_server_handling_seconds",
    help: "Histogram of response latency (seconds) of gRPC that had been application-level handled by the server.",
    labelNames: ["grpc_type", "grpc_service", "grpc_method"],
    registers: [metricsRegistry],
});

const grpcServerHandledLatencySeconds = new Histogram<
    "grpc_type" | "grpc_service" | "grpc_method" | "grpc_code"
>({
    name: "grpc_server_handled_latency_seconds",
    help: "Histogram of response latency (seconds) of gRPC that had been application-level handled by the server",
    labelNames: ["grpc_type", "grpc_service", "grpc_method", "grpc_code"],
    registers: [metricsRegistry],
});

export function getGrpcMetricBaseLabels(
    methodPath: string,
    grpcType = "unary",
): GrpcMetricBaseLabels {
    const cleanedPath = methodPath.startsWith("/") ? methodPath.slice(1) : methodPath;
    const [grpcService = "unknown", grpcMethod = "unknown"] = cleanedPath.split("/");

    return {
        grpc_type: grpcType,
        grpc_service: grpcService,
        grpc_method: grpcMethod,
    };
}

export function incrementGrpcServerStarted(labels: GrpcMetricBaseLabels): void {
    grpcServerStartedTotal.inc(labels);
}

export function incrementGrpcServerHandled(labels: GrpcMetricHandledLabels): void {
    grpcServerHandledTotal.inc(labels);
}

export function incrementGrpcServerMsgReceived(labels: GrpcMetricBaseLabels): void {
    grpcServerMsgReceivedTotal.inc(labels);
}

export function incrementGrpcServerMsgSent(labels: GrpcMetricBaseLabels): void {
    grpcServerMsgSentTotal.inc(labels);
}

export function startGrpcServerHandlingTimer(
    labels: GrpcMetricBaseLabels,
): ReturnType<HistogramType<"grpc_type" | "grpc_service" | "grpc_method">["startTimer"]> {
    return grpcServerHandlingSeconds.startTimer(labels);
}

export function startGrpcServerHandledLatencyTimer(
    labels: GrpcMetricBaseLabels,
): ReturnType<
    HistogramType<"grpc_type" | "grpc_service" | "grpc_method" | "grpc_code">["startTimer"]
> {
    return grpcServerHandledLatencySeconds.startTimer(labels);
}

export function recordGrpcServerHandling(labels: GrpcMetricBaseLabels, seconds: number): void {
    grpcServerHandlingSeconds.observe(labels, seconds);
}

export function recordGrpcServerHandledLatency(
    labels: GrpcMetricHandledLabels,
    seconds: number,
): void {
    grpcServerHandledLatencySeconds.observe(labels, seconds);
}

export function startPrometheusMetricsServer(port: number): MetricsServer {
    const server = http.createServer(async (req, res) => {
        const url = req.url ?? "/";
        const method = req.method ?? "GET";

        if (method === "GET" && url === "/metrics") {
            try {
                const metrics = await metricsRegistry.metrics();
                res.statusCode = 200;
                res.setHeader("Content-Type", metricsRegistry.contentType);
                res.end(metrics);
            } catch (error) {
                logger.error("[METRICS] Failed to render Prometheus metrics", {
                    module: "metrics",
                    funcName: "startPrometheusMetricsServer",
                    error: error instanceof Error ? error.message : String(error),
                });
                res.statusCode = 500;
                res.end("failed to render metrics");
            }
            return;
        }

        res.statusCode = 404;
        res.end("not found");
    });

    server.on("error", (error) => {
        logger.error("[METRICS] Prometheus metrics server failed", {
            module: "metrics",
            funcName: "startPrometheusMetricsServer",
            error: error instanceof Error ? error.message : String(error),
        });
    });

    server.listen(port, () => {
        const address = server.address() as AddressInfo | null;
        logger.info("[METRICS] Prometheus metrics server started", {
            module: "metrics",
            funcName: "startPrometheusMetricsServer",
            port: address?.port ?? port,
        });
    });

    return { server, port };
}
