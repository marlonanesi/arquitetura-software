"""Configuração do OpenTelemetry: é tudo o que a aplicação sabe sobre observabilidade.

A aplicação só conversa com o Collector, via OTLP. Para onde os traces e as métricas
vão depois (Jaeger, Zipkin, Prometheus, um SaaS) é decisão da configuração do Collector,
não do código.
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

SERVICO = os.environ["SERVICO"]
OTLP = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")


class FormatoJson(logging.Formatter):
    """Log estruturado em JSON, com o trace_id e o span_id da requisição em andamento."""

    def format(self, registro):
        contexto = trace.get_current_span().get_span_context()
        linha = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "nivel": registro.levelname,
            "servico": SERVICO,
            "msg": registro.getMessage(),
        }
        if contexto.is_valid:
            linha["trace_id"] = format(contexto.trace_id, "032x")
            linha["span_id"] = format(contexto.span_id, "016x")
        return json.dumps(linha, ensure_ascii=False)


def configurar(app, propagar_contexto: bool = True):
    resource = Resource.create({
        "service.name": SERVICO,
        "service.version": "1.0.0",
        "deployment.environment": "lab",
    })

    # Traces
    provedor = TracerProvider(resource=resource)
    provedor.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP, insecure=True)))
    trace.set_tracer_provider(provedor)

    # Métricas (o instrumentador do FastAPI já registra a duração de cada requisição)
    leitor = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=OTLP, insecure=True), export_interval_millis=5000)
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[leitor]))

    # Instrumentação automática: spans para cada requisição recebida e cada chamada feita.
    FastAPIInstrumentor.instrument_app(app)
    if propagar_contexto:
        # É o instrumentador do cliente HTTP que injeta o cabeçalho "traceparent" nas chamadas.
        HTTPXClientInstrumentor().instrument()

    # Logs em JSON no stdout, correlacionáveis pelo trace_id.
    manipulador = logging.StreamHandler(sys.stdout)
    manipulador.setFormatter(FormatoJson())
    raiz = logging.getLogger()
    raiz.handlers = [manipulador]
    raiz.setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").disabled = True  # evita duplicar o que o trace já registra
