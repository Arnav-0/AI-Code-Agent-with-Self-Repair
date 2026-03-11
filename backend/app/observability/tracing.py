from __future__ import annotations

import asyncio
import functools
import time
from typing import Any, Callable, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_tracer_provider: Optional[TracerProvider] = None


def setup_tracing(service_name: str, otlp_endpoint: str) -> None:
    global _tracer_provider
    resource = Resource(attributes={"service.name": service_name})
    provider = TracerProvider(resource=resource)

    try:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    except Exception:
        # If OTLP exporter fails (no collector running), skip
        pass

    trace.set_tracer_provider(provider)
    _tracer_provider = provider

    try:
        FastAPIInstrumentor().instrument()
    except Exception:
        pass


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)


def traced(
    name: Optional[str] = None, attributes: Optional[dict] = None
) -> Callable:
    """Decorator that creates a span for the decorated async function."""

    def decorator(func: Callable) -> Callable:
        span_name = name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                start = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute(
                        "duration_ms", int((time.perf_counter() - start) * 1000)
                    )
                    return result
                except Exception as exc:
                    span.record_exception(exc)
                    span.set_status(
                        trace.StatusCode.ERROR, str(exc)
                    )
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute(
                        "duration_ms", int((time.perf_counter() - start) * 1000)
                    )
                    return result
                except Exception as exc:
                    span.record_exception(exc)
                    span.set_status(
                        trace.StatusCode.ERROR, str(exc)
                    )
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
