from litestar.contrib.opentelemetry import OpenTelemetryConfig
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

config = OpenTelemetryConfig()


# Create and export one trace every 100 requests
sampler = ParentBasedTraceIdRatio(1 / 10)
# Use the default tracer provider
trace.set_tracer_provider(TracerProvider(sampler=sampler))
trace.get_tracer_provider().add_span_processor(  # type: ignore[attr-defined]
    # Initialize the cloud tracing exporter
    BatchSpanProcessor(CloudTraceSpanExporter())
)
