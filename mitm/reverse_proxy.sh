#!/bin/sh
# Proxy inverso: todo el tráfico del alumno pasa por aquí (demo MITM educativa)
set -e

UPSTREAM="${MITM_UPSTREAM:-http://frontend:80}"
PORT="${MITM_PORT:-8080}"
LOG="${CAPTURE_LOG:-/var/log/mitm/capture.log}"

mkdir -p /var/log/mitm
echo "[mitm] Reverse proxy ${PORT} -> ${UPSTREAM}" | tee "$LOG"

exec mitmdump \
  --mode "reverse:${UPSTREAM}" \
  --listen-host 0.0.0.0 \
  --listen-port "${PORT}" \
  -s /log_bodies.py \
  --flow-detail 3 \
  2>&1 | tee -a "$LOG"
