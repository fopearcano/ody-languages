"""A dependency-free HTTP service exposing the Sūchel translator and voice.

This is the machine surface of :mod:`odylang.translate` and
:mod:`odylang.tts`: a small :class:`http.server.ThreadingHTTPServer` that a
LibreChat Action (or any browser / ``curl`` client) can call.  It ships
stdlib-only — no Flask, no FastAPI, no PyYAML.

Routes
------
``GET  /``            the translator chat page (from
                      :mod:`odylang.translator_web`, imported *lazily* so this
                      module never hard-fails while that page is still being
                      written; a placeholder naming the endpoints is served
                      until then).
``GET  /health``      liveness JSON.
``GET  /openapi.json``the OpenAPI 3.1 document (the :data:`OPENAPI_SPEC` dict).
``GET  /voice_spec``  :func:`odylang.tts.voice_spec` — the browser-mirror voice.
``POST /translate``   ``{"text","direction"}`` -> ``dataclasses.asdict`` of a
                      :class:`odylang.translate.Translation`.
``POST /tts``         ``{"text","direction"?}`` -> ``audio/wav`` bytes (English
                      input is translated to Sūchel first, then synthesized;
                      the chosen Sūchel + IPA ride back in the ``X-Suchel`` /
                      ``X-IPA`` headers).  ``?format=base64`` returns
                      ``{"wav_base64","suchel","ipa"}`` JSON instead.

The OpenAPI dict is the *single source of truth*: it is served at
``/openapi.json`` and dumped (by the tiny deterministic YAML emitter below) to
``integrations/librechat/openapi.yaml``, so the JSON and the YAML can never
drift — a test asserts the committed file equals :func:`openapi_yaml`.

CORS is permissive (``Access-Control-Allow-Origin: *`` plus an ``OPTIONS``
preflight) so a browser or the LibreChat client may call it directly, and every
handler is wrapped so a bad request returns ``{"error": ...}`` with a 4xx and an
unexpected failure returns a terse 500 — a stack trace never reaches the wire.
"""

from __future__ import annotations

import base64
import dataclasses
import json
import os
import re
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __version__
from . import translate as _translate
from . import tts as _tts

SERVICE = "odylang-translator"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787

# The committed OpenAPI YAML lives next to the LibreChat integration docs.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPENAPI_YAML_PATH = os.path.join(
    _REPO_ROOT, "integrations", "librechat", "openapi.yaml")


# ---------------------------------------------------------------------------
# the OpenAPI 3.1 document — the single source of truth for JSON *and* YAML


OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": {
        "title": "Suchel Translator & Voice",
        "version": __version__,
        "description": (
            "English <-> Suchel (the Crossing-Speech of the crossable "
            "universe) translation, plus stdlib formant speech synthesis. "
            "Every Suchel string is built through the grammar of the codices; "
            "no root is ever invented, and unknown words are reported "
            "honestly."),
        "license": {"name": "See project README"},
    },
    "servers": [
        {"url": "http://localhost:8787",
         "description": "local odylang server (run: odylang serve)"},
    ],
    "paths": {
        "/health": {
            "get": {
                "operationId": "healthCheck",
                "summary": "Liveness probe.",
                "description": "Returns service name and odylang version.",
                "responses": {
                    "200": {
                        "description": "Service is up.",
                        "content": {"application/json": {
                            "schema": {"$ref": "#/components/schemas/Health"}}},
                    },
                },
            },
        },
        "/voice_spec": {
            "get": {
                "operationId": "voiceSpec",
                "summary": "The voice description.",
                "description": (
                    "The complete, JSON-serializable specification a browser "
                    "synthesizer reproduces: sample rate, base F0, vowel "
                    "formants, timing constants and every consonant recipe."),
                "responses": {
                    "200": {
                        "description": "The voice spec.",
                        "content": {"application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/VoiceSpec"}}},
                    },
                },
            },
        },
        "/translate": {
            "post": {
                "operationId": "translateText",
                "summary": "Translate between English and Suchel.",
                "description": (
                    "Translate a line in either direction. Returns the target "
                    "text, its IPA, an interlinear gloss, the Navcher tokens "
                    "and rhythm array, a per-word alignment, notes, and a "
                    "confidence (1.0 = an attested idiom, 0.9 = composed, "
                    "lower = unknown words present)."),
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/TranslateRequest"}}},
                },
                "responses": {
                    "200": {
                        "description": "The translation.",
                        "content": {"application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/Translation"}}},
                    },
                    "400": {
                        "description": "Bad request.",
                        "content": {"application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}}},
                    },
                },
            },
        },
        "/tts": {
            "post": {
                "operationId": "synthesizeSpeech",
                "summary": "Speak a line of Suchel.",
                "description": (
                    "Synthesize speech. English input is translated to Suchel "
                    "first, then voiced. By default returns audio/wav bytes "
                    "with the chosen Suchel and IPA in the X-Suchel and X-IPA "
                    "response headers (non-ASCII percent-encoded). Pass "
                    "?format=base64 to receive JSON with a base64 WAV instead, "
                    "convenient for a browser or a chat client."),
                "parameters": [
                    {"name": "format", "in": "query", "required": False,
                     "description": (
                         "Set to 'base64' for a JSON response carrying the WAV "
                         "as base64 plus the Suchel and IPA."),
                     "schema": {"type": "string", "enum": ["base64"]}},
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/TtsRequest"}}},
                },
                "responses": {
                    "200": {
                        "description": "The synthesized audio.",
                        "content": {
                            "audio/wav": {
                                "schema": {"type": "string",
                                           "format": "binary"}},
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/"
                                            "TtsBase64Response"}},
                        },
                    },
                    "400": {
                        "description": "Bad request.",
                        "content": {"application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}}},
                    },
                },
            },
        },
    },
    "components": {
        "schemas": {
            "Direction": {
                "type": "string",
                "enum": ["auto", "en2su", "su2en"],
                "default": "auto",
                "description": (
                    "en2su = English to Suchel, su2en = Suchel to English, "
                    "auto = detect from the input."),
            },
            "TranslateRequest": {
                "type": "object",
                "required": ["text"],
                "properties": {
                    "text": {"type": "string",
                             "description": "The line to translate.",
                             "example": "the beacon holds"},
                    "direction": {
                        "$ref": "#/components/schemas/Direction"},
                },
            },
            "TtsRequest": {
                "type": "object",
                "required": ["text"],
                "properties": {
                    "text": {"type": "string",
                             "description": (
                                 "The line to speak. English is translated to "
                                 "Suchel before synthesis."),
                             "example": "the beacon holds"},
                    "direction": {
                        "$ref": "#/components/schemas/Direction"},
                },
            },
            "TWord": {
                "type": "object",
                "description": "One word-level alignment.",
                "properties": {
                    "english": {"type": "string"},
                    "suchel": {"type": "string"},
                    "gloss": {"type": "string"},
                    "ipa": {"type": "string"},
                    "known": {"type": "boolean"},
                    "domain": {"type": "string"},
                },
            },
            "Translation": {
                "type": "object",
                "description": "A full translation result, either direction.",
                "properties": {
                    "source": {"type": "string",
                               "description": "The input text."},
                    "direction": {
                        "type": "string", "enum": ["en2su", "su2en"],
                        "description": "The direction actually used."},
                    "text": {"type": "string",
                             "description": "The translated line."},
                    "ipa": {"type": "string",
                            "description": "IPA of the Suchel side."},
                    "gloss": {"type": "string",
                              "description": "Interlinear gloss."},
                    "tokens": {"type": "array", "items": {"type": "string"},
                               "description": (
                                   "Careful-hand Navcher tokens, Suchel side.")},
                    "syl": {"type": "array", "items": {"type": "string"},
                            "description": (
                                "Rhythm array, Suchel side (empty for su2en).")},
                    "words": {"type": "array",
                              "items": {"$ref": "#/components/schemas/TWord"}},
                    "notes": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": "number",
                                   "description": (
                                       "1.0 attested, 0.9 composed, "
                                       "lower = unknown words."),
                                   "example": 0.9},
                },
            },
            "TtsBase64Response": {
                "type": "object",
                "properties": {
                    "wav_base64": {"type": "string",
                                   "description": "Base64-encoded WAV bytes."},
                    "suchel": {"type": "string",
                               "description": "The Suchel that was voiced."},
                    "ipa": {"type": "string",
                            "description": "IPA of the voiced Suchel."},
                    "content_type": {"type": "string",
                                     "example": "audio/wav"},
                },
            },
            "Health": {
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "service": {"type": "string", "example": SERVICE},
                    "version": {"type": "string"},
                },
            },
            "VoiceSpec": {
                "type": "object",
                "description": (
                    "The formant-voice specification (open shape; see "
                    "odylang.tts.voice_spec)."),
                "additionalProperties": True,
            },
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                },
            },
        },
    },
}


# ---------------------------------------------------------------------------
# a tiny deterministic YAML emitter (block style, 2-space indent)
#
# It handles exactly the value types present in OPENAPI_SPEC: dict, list, str,
# bool, int, float and None.  String scalars are always double-quoted (with the
# YAML escapes) so the output is unambiguous and always re-parses; keys stay
# bare when they are simple.  Being deterministic is the whole point — the same
# emitter writes the committed YAML file and backs the sync test.

_SAFE_KEY = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]*$")


def _yaml_quote(s: str) -> str:
    out = (s.replace("\\", "\\\\").replace('"', '\\"')
            .replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r"))
    return '"' + out + '"'


def _yaml_key(k) -> str:
    k = str(k)
    # Quote all-digit keys (e.g. HTTP status codes) so they stay strings, not
    # ints, under a real YAML loader — OpenAPI response keys are strings.
    if _SAFE_KEY.match(k) and not k.isdigit():
        return k
    return _yaml_quote(k)


def _yaml_scalar(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    return _yaml_quote(str(v))


def _emit_block(obj: dict, indent: int) -> list:
    pad = "  " * indent
    lines = []
    for k, v in obj.items():
        key = _yaml_key(k)
        if isinstance(v, dict):
            if v:
                lines.append(f"{pad}{key}:")
                lines.extend(_emit_block(v, indent + 1))
            else:
                lines.append(f"{pad}{key}: {{}}")
        elif isinstance(v, list):
            if v:
                lines.append(f"{pad}{key}:")
                lines.extend(_emit_list(v, indent))
            else:
                lines.append(f"{pad}{key}: []")
        else:
            lines.append(f"{pad}{key}: {_yaml_scalar(v)}")
    return lines


def _emit_list(seq: list, indent: int) -> list:
    pad = "  " * indent
    lines = []
    for item in seq:
        if isinstance(item, dict) and item:
            inner = _emit_block(item, indent + 1)
            lines.append(f"{pad}- {inner[0][len(pad) + 2:]}")
            lines.extend(inner[1:])
        elif isinstance(item, list) and item:
            inner = _emit_list(item, indent + 1)
            lines.append(f"{pad}- {inner[0][len(pad) + 2:]}")
            lines.extend(inner[1:])
        elif isinstance(item, dict):
            lines.append(f"{pad}- {{}}")
        elif isinstance(item, list):
            lines.append(f"{pad}- []")
        else:
            lines.append(f"{pad}- {_yaml_scalar(item)}")
    return lines


def dump_yaml(obj: dict) -> str:
    """Serialize ``obj`` (the OpenAPI dict shape) to deterministic YAML text."""
    return "\n".join(_emit_block(obj, 0)) + "\n"


def openapi_yaml() -> str:
    """The OpenAPI document as YAML — the exact content of the committed file."""
    return dump_yaml(OPENAPI_SPEC)


def write_openapi_yaml(path: str = None) -> str:
    """Write :func:`openapi_yaml` to ``path`` (default the committed location)."""
    path = path or OPENAPI_YAML_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(openapi_yaml())
    return path


# ---------------------------------------------------------------------------
# shared logic: what Suchel + IPA to actually voice


def speech_target(text: str, direction: str = "auto"):
    """Resolve ``text`` to the Suchel to speak.

    Returns ``(suchel, ipa, synth_input, translation)``.  For English input the
    line is translated and the composed Suchel is voiced; for Suchel input the
    line is voiced as given (its IPA recovered from the per-word alignment).
    """
    tr = _translate.translate(text, direction)
    if tr.direction == "en2su":
        return tr.text, tr.ipa, tr.text, tr
    ipa = " ".join(w.ipa for w in tr.words if w.ipa)
    return tr.source, ipa, text, tr


# ---------------------------------------------------------------------------
# the placeholder page (served until odylang.translator_web is importable)

_PAGE_CANDIDATES = ("document", "page", "html", "render", "render_page",
                    "index", "fragment")
_PAGE_ATTRS = ("HTML", "PAGE", "DOCUMENT")


def _translator_html():
    """The translator chat page from :mod:`odylang.translator_web` if present,
    else a placeholder.  Import is lazy and fully guarded.  The page's
    "THE CODEX" link is pointed at this server's own ``/codex`` route."""
    try:
        from . import translator_web as _tw
    except Exception:
        return _placeholder_html()
    try:
        # preferred: the documented page(codex_url=...) entry point, so the
        # header link resolves to this server's /codex route
        fn = getattr(_tw, "page", None)
        if callable(fn):
            try:
                out = fn(codex_url="/codex")
            except TypeError:
                out = fn()
            if isinstance(out, str) and out.strip():
                return out
        for name in _PAGE_CANDIDATES:
            fn = getattr(_tw, name, None)
            if callable(fn):
                try:
                    out = fn()
                except TypeError:
                    continue
                if isinstance(out, str) and out.strip():
                    return out
        for attr in _PAGE_ATTRS:
            val = getattr(_tw, attr, None)
            if isinstance(val, str) and val.strip():
                return val
    except Exception:
        pass
    return _placeholder_html()


def _codex_html():
    """The interactive codex (the full knowledge system) from
    :mod:`odylang.webgen`, imported lazily; a small pointer page if absent."""
    try:
        from . import webgen as _wg
        out = _wg.document()
        if isinstance(out, str) and out.strip():
            return out
    except Exception:
        pass
    return (
        "<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<title>odylang codex</title></head><body style=\"background:#08070a;"
        "color:#d8d2c8;font-family:monospace;padding:40px\">"
        "<p>The interactive codex is generated by "
        "<code>odylang web -o codex.html</code>.</p>"
        "<p><a href=\"/\" style=\"color:#6fa8ff\">&larr; back to the translator</a></p>"
        "</body></html>")


def _placeholder_html() -> str:
    return (
        "<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,"
        " initial-scale=1\">"
        "<title>Suchel Translator</title>"
        "<style>body{font:16px/1.6 system-ui,sans-serif;max-width:44rem;"
        "margin:3rem auto;padding:0 1.2rem;color:#1a2430;background:#f7f5ef}"
        "code{background:#e8e4d8;padding:.1em .35em;border-radius:.25em}"
        "h1{margin-bottom:.2em}a{color:#2a6}</style></head><body>"
        "<h1>S&#363;chel Translator</h1>"
        "<p>The interactive page is not installed yet. The service is up and "
        "the API endpoints below are live.</p>"
        "<ul>"
        "<li><code>GET /health</code> &mdash; "
        "<a href=\"/health\">/health</a></li>"
        "<li><code>GET /openapi.json</code> &mdash; "
        "<a href=\"/openapi.json\">/openapi.json</a> "
        "(import this as a LibreChat Action)</li>"
        "<li><code>GET /voice_spec</code> &mdash; "
        "<a href=\"/voice_spec\">/voice_spec</a></li>"
        "<li><code>POST /translate</code> &mdash; "
        "<code>{\"text\":\"the beacon holds\"}</code></li>"
        "<li><code>POST /tts</code> &mdash; WAV audio; "
        "<code>?format=base64</code> for JSON</li>"
        "</ul>"
        "<p>See <code>integrations/librechat/</code> for the agent setup.</p>"
        "</body></html>\n")


# ---------------------------------------------------------------------------
# HTTP


class _BadRequest(Exception):
    """A client error carrying a 4xx status."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def _header_safe(value: str) -> str:
    """A header-legal rendering: pass ASCII/latin-1 through untouched, else
    percent-encode (UTF-8) so non-ASCII Suchel/IPA never breaks the wire."""
    try:
        value.encode("latin-1")
        return value
    except UnicodeEncodeError:
        return urllib.parse.quote(value, safe=" =-.|?/:'")


class Handler(BaseHTTPRequestHandler):
    server_version = "odylang/" + __version__
    protocol_version = "HTTP/1.1"

    # -- plumbing ----------------------------------------------------------

    def log_message(self, *args):  # keep the test/serve output quiet
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")

    def _send_bytes(self, status, data, content_type, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def _send_json(self, status, obj, extra=None):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, body, "application/json; charset=utf-8", extra)

    def _send_html(self, status, html):
        self._send_bytes(status, html.encode("utf-8"),
                         "text/html; charset=utf-8")

    def _read_json_body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise _BadRequest("invalid Content-Length")
        raw = self.rfile.read(length) if length > 0 else b""
        if not raw:
            return {}
        try:
            obj = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise _BadRequest("body is not valid JSON")
        if not isinstance(obj, dict):
            raise _BadRequest("body must be a JSON object")
        return obj

    @staticmethod
    def _require_text(data):
        text = data.get("text")
        if not isinstance(text, str) or not text.strip():
            raise _BadRequest("missing required field 'text'")
        return text

    # -- verbs -------------------------------------------------------------

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path
        try:
            if path in ("/", ""):
                self._send_html(200, _translator_html())
            elif path in ("/codex", "/codex/"):
                self._send_html(200, _codex_html())
            elif path == "/health":
                self._send_json(200, {"ok": True, "service": SERVICE,
                                      "version": __version__})
            elif path == "/openapi.json":
                self._send_json(200, OPENAPI_SPEC)
            elif path == "/voice_spec":
                self._send_json(200, _tts.voice_spec())
            elif path == "/favicon.ico":
                self._send_bytes(204, b"", "image/x-icon")
            else:
                self._send_json(404, {"error": f"not found: {path}"})
        except _BadRequest as e:
            self._send_json(e.status, {"error": e.message})
        except Exception:
            self._send_json(500, {"error": "internal error"})

    def do_POST(self):
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        try:
            if path == "/translate":
                self._handle_translate()
            elif path == "/tts":
                self._handle_tts(query)
            else:
                self._send_json(404, {"error": f"not found: {path}"})
        except _BadRequest as e:
            self._send_json(e.status, {"error": e.message})
        except ValueError as e:
            self._send_json(400, {"error": str(e)})
        except Exception:
            self._send_json(500, {"error": "internal error"})

    # -- handlers ----------------------------------------------------------

    def _handle_translate(self):
        data = self._read_json_body()
        text = self._require_text(data)
        direction = data.get("direction", "auto")
        if not isinstance(direction, str):
            raise _BadRequest("'direction' must be a string")
        tr = _translate.translate(text, direction)
        self._send_json(200, dataclasses.asdict(tr))

    def _handle_tts(self, query):
        data = self._read_json_body()
        text = self._require_text(data)
        direction = data.get("direction", "auto")
        if not isinstance(direction, str):
            raise _BadRequest("'direction' must be a string")
        suchel, ipa, synth_input, _tr = speech_target(text, direction)
        wav = _tts.synth(synth_input)
        fmt = (query.get("format") or [""])[0]
        if fmt == "base64":
            self._send_json(200, {
                "wav_base64": base64.b64encode(wav).decode("ascii"),
                "suchel": suchel,
                "ipa": ipa,
                "content_type": "audio/wav",
            })
        else:
            self._send_bytes(200, wav, "audio/wav", {
                "X-Suchel": _header_safe(suchel),
                "X-IPA": _header_safe(ipa),
            })


# ---------------------------------------------------------------------------
# lifecycle


def make_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """Build (but do not start) the server.

    Pass ``port=0`` for an OS-assigned port; read it back from
    ``server.server_address[1]``.  Tests start this on a thread and shut it
    down with ``server.shutdown()``.
    """
    return ThreadingHTTPServer((host, port), Handler)


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """Run the server forever, printing the URL and the LibreChat hint."""
    srv = make_server(host, port)
    addr = srv.server_address
    url = f"http://{addr[0]}:{addr[1]}"
    print(f"odylang translator server listening on {url}")
    print(f"  health     GET  {url}/health")
    print(f"  translate  POST {url}/translate")
    print(f"  tts        POST {url}/tts")
    print(f"  voice      GET  {url}/voice_spec")
    print(f"  openapi    GET  {url}/openapi.json")
    print(f"  page       GET  {url}/")
    print("LibreChat: Agents -> Add Action -> import the OpenAPI URL "
          f"{url}/openapi.json  (see integrations/librechat/).")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
    finally:
        srv.server_close()


if __name__ == "__main__":
    serve()
