"""Send OpenTelemetry traces to local Langfuse (OTLP HTTP).

FastMCP already emits MCP spans if a TracerProvider is global *before*
FastMCP is imported. This registers that provider against Langfuse's
`/api/public/otel` endpoint so the MCP-only lab does not need LangChain
or the Langfuse callback.

    LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_BASE_URL
"""

from __future__ import annotations

import base64
import os
from typing import Sequence

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export import SpanExporter
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace import ReadableSpan


class _McpTags(SpanProcessor):
    """Stamp every span so the MCP run is filterable next to LangGraph traces."""

    def __init__(self, session: str, tags: Sequence[str]) -> None:
        self.session = session
        self.tags = list(tags)

    def on_start(self, span, parent_context=None) -> None:  # noqa: ANN001
        span.set_attribute("session.id", self.session)
        span.set_attribute("langfuse.session.id", self.session)
        span.set_attribute("langfuse.trace.tags", self.tags)

    def on_end(self, span: ReadableSpan) -> None:
        return

    def shutdown(self) -> None:
        return

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


def traces_endpoint() -> str:
    base = (
        os.getenv("LANGFUSE_BASE_URL")
        or os.getenv("LANGFUSE_HOST")
        or "http://localhost:3000"
    ).rstrip("/")
    if base.endswith("/api/public/otel/v1/traces"):
        return base
    if base.endswith("/api/public/otel"):
        return f"{base}/v1/traces"
    return f"{base}/api/public/otel/v1/traces"


def register_langfuse_otel(
    service_name: str | None = None,
    session: str | None = None,
) -> TracerProvider:
    pk = os.getenv("LANGFUSE_PUBLIC_KEY")
    sk = os.getenv("LANGFUSE_SECRET_KEY")
    if not pk or not sk:
        raise RuntimeError(
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env."
        )

    service = service_name or os.getenv("LANGFUSE_MCP_SERVICE", "mcp-plant-fabric")
    sess = session or os.getenv("LANGFUSE_MCP_SESSION", "mcp-plant-fabric")
    token = base64.b64encode(f"{pk}:{sk}".encode()).decode()
    exporter: SpanExporter = OTLPSpanExporter(
        endpoint=traces_endpoint(),
        headers={
            "Authorization": f"Basic {token}",
            "x-langfuse-ingestion-version": "4",
        },
        timeout=30,
    )
    provider = TracerProvider(
        resource=Resource.create({"service.name": service})
    )
    provider.add_span_processor(_McpTags(sess, ["mcp"]))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    print(f"Langfuse OTLP: {traces_endpoint()}")
    print(f"service.name={service} session={sess}")
    return provider
