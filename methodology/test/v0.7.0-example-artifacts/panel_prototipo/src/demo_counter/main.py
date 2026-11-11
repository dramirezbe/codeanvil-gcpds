import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from .config.logger import get_logger
from .config.runtime import DEFAULT_PORT
from .hal.port import RuntimeMockHAL
from .processing.value import identity

log = get_logger(__name__)
PAGE = b"""<!doctype html><meta charset="utf-8"><title>Mock value preview</title>
<h1>Synthetic UI fixture</h1><p>Mock HAL; no hardware validation.</p>
<output id="value">Loading</output><script>
async function update(){const r=await fetch('/api/value');
document.getElementById('value').textContent=(await r.json()).value;}
update();setInterval(update,1000);</script>"""


def main() -> None:
    """Run one local preview process until interrupted."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    source = RuntimeMockHAL()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == '/':
                body, kind = PAGE, 'text/html; charset=utf-8'
            elif self.path == '/api/value':
                body = json.dumps({'value': identity(source.read())}).encode()
                kind = 'application/json'
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *values) -> None:
            log.info(fmt, *values)

    server = HTTPServer(('127.0.0.1', args.port), Handler)
    log.info('Mock preview on http://127.0.0.1:%s/', server.server_port)
    try:
        server.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        log.info('Stopping preview')
    finally:
        server.server_close()
