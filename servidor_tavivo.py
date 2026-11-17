"""Servidor Web HTTP nativo do TaVivo (porta 9876).

Serve a interface estática em app/static/ e expõe a API local para
o agente RAG (tavivo_agent.py) e o motor llama-server na porta 9931.
Usa apenas a biblioteca padrão do Python (100% offline).

Construído por Capitain Of Cruzades.
"""

import json
import os
import socket
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tavivo_agent import (  # noqa: E402
    DEFAULT_LLAMA_PORT,
    LibraryRAG,
    check_llama_status,
    stream_chat,
)

WEB_HOST = os.environ.get("TAVIVO_WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.environ.get("TAVIVO_WEB_PORT", "9876"))
STATIC_DIR = os.path.join(ROOT, "app", "static")

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".json": "application/json; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}

RAG = LibraryRAG()


class TaVivoHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        # Log compacto para terminal
        sys.stderr.write(f"[TaVivo] {self.address_string()} - {format % args}\n")

    def _send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filepath):
        if not os.path.isfile(filepath):
            self.send_error(404, "Arquivo nao encontrado")
            return
        ext = os.path.splitext(filepath)[1].lower()
        ctype = MIME_TYPES.get(ext, "application/octet-stream")
        with open(filepath, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            return self._send_file(os.path.join(STATIC_DIR, "index.html"))

        if path.startswith("/static/"):
            rel = path[len("/static/"):].lstrip("/")
            safe = os.path.normpath(os.path.join(STATIC_DIR, rel))
            if not safe.startswith(os.path.abspath(STATIC_DIR)):
                self.send_error(403, "Acesso negado")
                return
            return self._send_file(safe)

        if path == "/api/status":
            ai = check_llama_status()
            lib_ok = RAG.available
            articles, sources = RAG.stats() if lib_ok else (0, 0)
            return self._send_json(200, {
                "ai_online": ai["online"],
                "ai_port": DEFAULT_LLAMA_PORT,
                "library_online": lib_ok,
                "articles": articles,
                "sources": sources,
            })

        if path == "/api/sources":
            items = []
            if RAG.available and RAG.db:
                rows = RAG.db.execute(
                    "SELECT id, label, topic, license FROM sources ORDER BY id"
                ).fetchall()
                for sid, label, topic, lic in rows:
                    docs = RAG.db.execute(
                        "SELECT d.title, MIN(p.id) FROM docs d "
                        "LEFT JOIN passages p ON p.doc_id = d.id "
                        "WHERE d.source_id=? GROUP BY d.id ORDER BY d.id",
                        (sid,),
                    ).fetchall()
                    items.append({
                        "label": label,
                        "topic": topic,
                        "license": lic or "",
                        "articles": [{"title": t, "id": pid} for t, pid in docs],
                    })
            return self._send_json(200, {"sources": items})

        if path == "/api/legal":
            legal_path = os.path.join(ROOT, "AVISO_LEGAL.md")
            try:
                with open(legal_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except OSError:
                text = "AVISO_LEGAL.md não encontrado neste pacote."
            return self._send_json(200, {"text": text})

        if path == "/api/search":
            qs = parse_qs(parsed.query)
            q = (qs.get("q") or [""])[0].strip()
            try:
                limit = max(1, min(50, int((qs.get("limit") or ["15"])[0])))
            except ValueError:
                limit = 15
            results = RAG.search(q, limit=limit) if q else []
            return self._send_json(200, {"query": q, "results": results})

        if path == "/api/article":
            qs = parse_qs(parsed.query)
            try:
                pid = int((qs.get("id") or ["0"])[0])
            except ValueError:
                return self._send_json(400, {"error": "ID inválido"})
            doc = RAG.document(pid)
            if not doc:
                return self._send_json(404, {"error": "Artigo não encontrado"})
            return self._send_json(200, doc)

        self.send_error(404, "Rota nao encontrada")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/chat":
            self.send_error(404, "Rota nao encontrada")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._send_json(400, {"error": "Content-Length inválido"})

        if length <= 0 or length > 25 * 1024 * 1024:
            return self._send_json(400, {"error": "Payload vazio ou maior que 25MB"})

        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except ValueError:
            return self._send_json(400, {"error": "JSON inválido"})

        user_text = data.get("message") or ""
        history = data.get("history") or []
        images = data.get("images") or []

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        try:
            for event in stream_chat(RAG, user_text, history=history, images=images):
                line = f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode("utf-8")
                self.wfile.write(line)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


class DualStackHTTPServer(ThreadingHTTPServer):
    address_family = socket.AF_INET6

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


def main():
    bind_mode = "ipv4"
    if WEB_HOST in ("0.0.0.0", "::", ""):
        try:
            server = DualStackHTTPServer(("::", WEB_PORT), TaVivoHandler)
            bind_mode = "dual-stack"
        except OSError:
            server = ThreadingHTTPServer(("0.0.0.0", WEB_PORT), TaVivoHandler)
    else:
        server = ThreadingHTTPServer((WEB_HOST, WEB_PORT), TaVivoHandler)
    print(f"TaVivo Terminal Offline ativo em http://127.0.0.1:{WEB_PORT} ({bind_mode})")
    print(f"Motor IA esperado na porta: {DEFAULT_LLAMA_PORT}")
    print(f"Biblioteca SQLite: {'OK' if RAG.available else 'AUSENTE'} ({RAG.db_path})")
    print("Construído por Capitain Of Cruzades.")
    if os.environ.get("TAVIVO_OPEN_BROWSER") == "1":
        url = f"http://127.0.0.1:{WEB_PORT}"
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor TaVivo...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
