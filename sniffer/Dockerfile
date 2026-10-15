# Sniffer pasivo (L3/L4) para la demo MITM educativa — Clase 01
FROM alpine:3.20

RUN apk add --no-cache tcpdump

COPY sniff.sh /sniff.sh
RUN chmod +x /sniff.sh

CMD ["/sniff.sh"]
