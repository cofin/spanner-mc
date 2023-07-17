from litestar.contrib.opentelemetry import OpenTelemetryConfig
from opentelemetry import metrics, trace
from opentelemetry.exporter.cloud_monitoring import (
    CloudMonitoringMetricsExporter,
)
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.cloud_trace_propagator import (
    CloudTraceFormatPropagator,
)
from opentelemetry.resourcedetector.gcp_resource_detector import GoogleCloudResourceDetector
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, get_aggregated_resources
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

from . import db, settings

set_global_textmap(CloudTraceFormatPropagator())
GrpcInstrumentorClient().instrument()  # type: ignore[no-untyped-call]
SQLAlchemyInstrumentor().instrument(engine=db.engine)
staging_labels = {"environment": settings.app.ENVIRONMENT}
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
            export_interval_millis=15000,
            export_timeout_millis=45000,
        )
    ],
    resource=_resources,
)

metrics.set_meter_provider(meter_provider)
metrics.get_meter_provider().start_pipeline(metrics.get_meter(__name__), CloudMonitoringMetricsExporter(), 5)  # type: ignore[attr-defined]
# Create and export one trace every 100 requests
_sampler = ParentBasedTraceIdRatio(1 / 250)
tracer_provider = TracerProvider(resource=_resources, sampler=_sampler)
trace.set_tracer_provider(tracer_provider)
trace.get_tracer_provider().add_span_processor(  # type: ignore[attr-defined]
    BatchSpanProcessor(CloudTraceSpanExporter(), max_queue_size=10000)  # type: ignore
)
config = OpenTelemetryConfig(tracer_provider=tracer_provider, meter_provider=meter_provider)
