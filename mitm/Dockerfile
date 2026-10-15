FROM mitmproxy/mitmproxy:11.0.2

COPY mitmproxy.yml /home/mitmproxy/.mitmproxy/config.yaml
COPY reverse_proxy.sh /reverse_proxy.sh
COPY log_bodies.py /log_bodies.py
RUN chmod +x /reverse_proxy.sh

EXPOSE 8080

CMD ["/reverse_proxy.sh"]
