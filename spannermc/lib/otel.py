from litestar.contrib.opentelemetry import OpenTelemetryConfig
from opentelemetry import metrics, trace
from opentelemetry.exporter.cloud_monitoring import (
    CloudMonitoringMetricsExporter,
)
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.cloud_trace_propagator import CloudTraceFormatPropagator
from opentelemetry.resourcedetector.gcp_resource_detector import GoogleCloudResourceDetector
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, get_aggregated_resources
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

from . import db, settings

__all__ = ["configure_instrumentation"]


def configure_instrumentation() -> OpenTelemetryConfig:
    """Initialize Open Telemetry configuration."""
    _resources = get_aggregated_resources(
        [
            GoogleCloudResourceDetector(),  # type: ignore[no-untyped-call]
        ],
        initial_resource=Resource.create(
            {
                "service.name": settings.app.NAME,
                "service.namespace": settings.app.slug,
                "service.version": settings.app.BUILD_NUMBER,
            }
        ),
        timeout=60,
    )
    meter_provider = MeterProvider(
        metric_readers=[
            PeriodicExportingMetricReader(
                CloudMonitoringMetricsExporter(add_unique_identifier=True),
            )
        ],
        resource=_resources,
    )

    metrics.set_meter_provider(meter_provider)
    # Create and export one trace every 25 requests
    _sampler = ParentBasedTraceIdRatio(1 / 25)
    tracer_provider = TracerProvider(resource=_resources, sampler=_sampler)
    trace.set_tracer_provider(tracer_provider)
    trace.get_tracer_provider().add_span_processor(  # type: ignore[attr-defined]
        BatchSpanProcessor(CloudTraceSpanExporter(), max_queue_size=10000)  # type: ignore
    )
    set_global_textmap(CloudTraceFormatPropagator())
    GrpcInstrumentorClient().instrument()  # type: ignore[no-untyped-call]
    SQLAlchemyInstrumentor().instrument(engine=db.engine)
    return OpenTelemetryConfig(
        meter=metrics.get_meter(__name__), tracer_provider=tracer_provider, meter_provider=meter_provider
    )


config = configure_instrumentation()
