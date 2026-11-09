"""Localhost-only HTTP facade; no arbitrary filesystem or model endpoint."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .evidence import EvidenceError, EvidenceStore

STATIC = Path(__file__).with_name("static")
ROUTES = {"/": ("index.html", "text/html"), "/assets/demo.css": ("demo.css", "text/css"), "/assets/demo.js": ("demo.js", "text/javascript")}
DOCUMENT_ROUTES = {"/evidence/closed-loop/report":"report", "/evidence/closed-loop/sources":"sources",
                   "/evidence/fresh-source/sources":"fresh_sources"}


def make_server(port=8765, *, store=None, host="127.0.0.1"):
    if host != "127.0.0.1":
        raise ValueError("Demo chỉ bind 127.0.0.1")
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("Port không hợp lệ")
    # Verify sources and read fixed assets before opening the listening socket.
    evidence = store if store is not None else EvidenceStore()
    assets = {}
    for route, (filename, mime) in ROUTES.items():
        with (STATIC / filename).open("rb") as stream:
            data = stream.read(256 * 1024 + 1)
        if len(data) > 256 * 1024:
            raise EvidenceError("UI asset vượt giới hạn")
        assets[route] = (data, mime)
    for route, name in DOCUMENT_ROUTES.items():
        assets[route] = evidence.documents[name]

    class Handler(BaseHTTPRequestHandler):
        server_version = "ResearchReplay/1"
        sys_version = ""

        def log_message(self, *_):
            pass

        def respond(self, status, data, mime="application/json"):
            if not isinstance(data, bytes):
                data = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", mime + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)

        def do_GET(self):
            port = self.server.server_address[1]
            hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
            host_values = self.headers.get_all("Host", [])
            origins = self.headers.get_all("Origin", [])
            if len(host_values) != 1 or host_values[0] not in hosts or len(origins) > 1 or (origins and origins[0] not in {"http://" + h for h in hosts}):
                return self.respond(403, {"error": "Chỉ cho phép localhost cùng origin"})
            if len(self.path) > 1024:
                return self.respond(414, {"error": "URL quá dài"})
            try:
                url = urlsplit(self.path)
            except ValueError:
                return self.respond(400, {"error": "URL không hợp lệ"})
            if url.scheme or url.netloc or url.fragment:
                return self.respond(400, {"error": "URL không hợp lệ"})
            if url.path == "/favicon.ico" and not url.query:
                return self.respond(204, b"", "image/x-icon")
            if url.path in assets and not url.query:
                data, mime = assets[url.path]
                return self.respond(200, data, mime)
            if url.path == "/api/catalog" and not url.query:
                return self.respond(200, evidence.catalog())
            if url.path == "/api/rq2-source-contrast":
                try:
                    q = parse_qs(url.query, keep_blank_values=True, strict_parsing=True, max_num_fields=3)
                    if set(q) != {"block", "ability", "lambda"} or any(len(v) != 1 for v in q.values()):
                        raise ValueError("query")
                    block, ability = int(q["block"][0]), int(q["ability"][0])
                    if str(block) != q["block"][0] or str(ability) != q["ability"][0]:
                        raise ValueError("canonical integer")
                    return self.respond(200, evidence.fresh_source_snapshot(block, ability, q["lambda"][0]))
                except (ValueError, KeyError):
                    return self.respond(400, {"error": "Block/năng lực/lambda phải thuộc allowlist fresh120"})
            if url.path in {"/api/replay", "/api/closed-loop"}:
                try:
                    q = parse_qs(url.query, keep_blank_values=True, strict_parsing=True, max_num_fields=4)
                    if set(q) != {"profile", "seed", "variant", "step"} or any(len(v) != 1 for v in q.values()):
                        raise ValueError("query")
                    if not q["seed"][0].isascii() or not q["step"][0].isascii():
                        raise ValueError("integer")
                    seed, step = int(q["seed"][0]), int(q["step"][0])
                    if str(seed) != q["seed"][0] or str(step) != q["step"][0]:
                        raise ValueError("canonical integer")
                    project = evidence.snapshot if url.path == "/api/replay" else evidence.closed_loop_snapshot
                    return self.respond(200, project(q["profile"][0], seed, q["variant"][0], step))
                except (ValueError, KeyError):
                    return self.respond(400, {"error": "Profile/seed/variant/step phải thuộc allowlist"})
            self.respond(404, {"error": "Không có route này"})

        do_HEAD = do_GET

        def method_not_allowed(self):
            self.respond(405, {"error": "Demo chỉ đọc: GET/HEAD"})

        do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = method_not_allowed

    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    return server
