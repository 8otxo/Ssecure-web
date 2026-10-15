#!/bin/sh
# ===========================================================================
# Sniffer PASIVO (Demo A — capa red, L3/L4) · solo laboratorio educativo
# ---------------------------------------------------------------------------
# Este contenedor NO está en la ruta cliente->servidor. Comparte el network
# namespace del backend (network_mode: "service:backend" en docker-compose),
# lo que simula a un atacante que ha comprometido un host del MISMO segmento
# de red y se limita a ESCUCHAR. No modifica ni reenvía tráfico: solo lee.
#
# Como el tráfico interno nginx->backend también viaja en HTTP plano (sin TLS),
# la contraseña aparece en claro en los bytes capturados. Es la diferencia con
# la Demo B (proxy mitmproxy, L7), donde el atacante SÍ está en la ruta.
# ===========================================================================
set -e

IFACE="${SNIFF_IFACE:-any}"
FILTER="${SNIFF_FILTER:-tcp port 8000}"

echo "[sniffer] Escucha PASIVA en iface='${IFACE}' filtro='${FILTER}'"
echo "[sniffer] (atacante silencioso en el segmento del backend; no reenvía tráfico)"

# -A  : imprime el payload en ASCII (se lee la contraseña directamente)
# -s0 : captura el paquete completo
# -l  : salida line-buffered para que 'docker compose logs' la muestre en vivo
exec tcpdump -i "${IFACE}" -A -s 0 -l "${FILTER}"
