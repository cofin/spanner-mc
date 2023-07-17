from litestar.contrib.opentelemetry import OpenTelemetryConfig
from opentelemetry import metrics, trace
from opentelemetry.exporter.cloud_monitoring import (
    CloudMonitoringMetricsExporter,
)
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.cloud_trace_propagator import CloudTraceFormatPropagator
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

from . import settings

set_global_textmap(CloudTraceFormatPropagator())
staging_labels = {"environment": settings.app.ENVIRONMENT}
meter_provider = MeterProvider(
    metric_readers=[
        PeriodicExportingMetricReader(
            CloudMonitoringMetricsExporter(add_unique_identifier=True),
            export_interval_millis=15000,
            export_timeout_millis=45000,
        )
    ],
    resource=Resource.create(
        {
            "service.name": settings.app.NAME,
            "service.namespace": settings.app.slug,
            "service.version": settings.app.BUILD_NUMBER,
        }
    ),
)
meter = metrics.get_meter(__name__)

# Create and export one trace every 100 requests
sampler = ParentBasedTraceIdRatio(1 / 10)
tracer_provider = TracerProvider(sampler=sampler)
processor = BatchSpanProcessor(CloudTraceSpanExporter())  # type: ignore
trace.set_tracer_provider(tracer_provider)
tracer_provider.add_span_processor(processor)
config = OpenTelemetryConfig(meter=meter, tracer_provider=tracer_provider)
