"""Addon mitmproxy: registra cuerpos POST en el log (solo laboratorio)."""
from mitmproxy import http


def request(flow: http.HTTPFlow) -> None:
    if flow.request.method == "POST" and flow.request.content:
        body = flow.request.get_text(strict=False)
        if body:
            print(f"[MITM-BODY] {flow.request.pretty_url} -> {body}")
