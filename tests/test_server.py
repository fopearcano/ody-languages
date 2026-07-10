"""The LibreChat HTTP service, locked end-to-end.

A real :class:`~odylang.server.make_server` is started on an OS-assigned port
in a background thread and hit over the loopback with stdlib ``urllib`` — no
third-party HTTP client, no PyYAML.  We assert the health/openapi/voice reads,
both translation directions, that ``/tts`` returns a valid WAV (and a decodable
base64 one), the CORS preflight, and that the embedded OpenAPI dict is byte-for-
byte the committed YAML.  The CLI parsers (translate / say / serve) are locked
through ``main()`` too.
"""

import base64
import json
import re
import threading
import urllib.error
import urllib.request

import pytest

from odylang import __version__, server
from odylang.cli import main


# ---------------------------------------------------------------------------
# a live server on port 0, shared across the module


@pytest.fixture(scope="module")
def base_url():
    srv = server.make_server("127.0.0.1", 0)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    host, port = srv.server_address
    try:
        yield f"http://{host}:{port}"
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def _get(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.status, r.headers, r.read()


def _post(url, payload, raw=None):
    data = raw if raw is not None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, r.headers, r.read()


# ---------------------------------------------------------------------------
# GET endpoints


def test_health(base_url):
    status, headers, body = _get(base_url + "/health")
    assert status == 200
    obj = json.loads(body)
    assert obj == {"ok": True, "service": "odylang-translator",
                   "version": __version__}
    # CORS on a plain GET too
    assert headers.get("Access-Control-Allow-Origin") == "*"


def test_openapi_json(base_url):
    status, _headers, body = _get(base_url + "/openapi.json")
    assert status == 200
    spec = json.loads(body)
    assert spec["openapi"].startswith("3.1")
    assert spec == server.OPENAPI_SPEC
    # the two named operations LibreChat wires up
    assert spec["paths"]["/translate"]["post"]["operationId"] == "translateText"
    assert spec["paths"]["/tts"]["post"]["operationId"] == "synthesizeSpeech"
    assert spec["servers"][0]["url"] == "http://localhost:8787"


def test_voice_spec(base_url):
    status, _headers, body = _get(base_url + "/voice_spec")
    assert status == 200
    spec = json.loads(body)
    for key in ("sampleRate", "f0", "formants", "timing", "consonants"):
        assert key in spec


def test_index_serves_html(base_url):
    status, headers, body = _get(base_url + "/")
    assert status == 200
    assert headers.get("Content-Type", "").startswith("text/html")
    text = body.decode("utf-8")
    assert text.startswith("<!DOCTYPE html>")
    # the real translator chat page is served now that odylang.translator_web
    # exists; it embeds the offline snapshot (window.ODYT) and the voice model
    assert "translator" in text.lower() and "window.ODYT" in text


def test_index_placeholder_names_endpoints():
    """When translator_web is unavailable, GET / degrades to a placeholder
    that still names the endpoints — never a hard failure."""
    from odylang import server as srv
    html = srv._placeholder_html()
    assert "/openapi.json" in html and "/translate" in html


def test_unknown_get_is_404_json(base_url):
    try:
        _get(base_url + "/nope")
    except urllib.error.HTTPError as e:
        assert e.code == 404
        assert "error" in json.loads(e.read())
    else:
        pytest.fail("expected 404")


# ---------------------------------------------------------------------------
# POST /translate — both directions


def test_translate_en2su(base_url):
    status, _headers, body = _post(base_url + "/translate",
                                   {"text": "the beacon holds"})
    assert status == 200
    tr = json.loads(body)
    assert tr["direction"] == "en2su"
    assert tr["text"] == "kad tan-a=ka."
    assert "hold" in tr["gloss"]
    assert tr["confidence"] == pytest.approx(0.9)
    assert isinstance(tr["words"], list) and tr["words"]
    assert set(tr["words"][0]) == {
        "english", "suchel", "gloss", "ipa", "known", "domain"}


def test_translate_su2en(base_url):
    status, _headers, body = _post(
        base_url + "/translate",
        {"text": "ver ish-ol.", "direction": "su2en"})
    assert status == 200
    tr = json.loads(body)
    assert tr["direction"] == "su2en"
    assert "truth" in tr["text"]
    assert "truth" in tr["gloss"]


def test_translate_missing_text_is_400(base_url):
    try:
        _post(base_url + "/translate", {"direction": "auto"})
    except urllib.error.HTTPError as e:
        assert e.code == 400
        assert "error" in json.loads(e.read())
    else:
        pytest.fail("expected 400")


def test_translate_bad_json_is_400(base_url):
    try:
        _post(base_url + "/translate", None, raw=b"{not json")
    except urllib.error.HTTPError as e:
        assert e.code == 400
    else:
        pytest.fail("expected 400")


# ---------------------------------------------------------------------------
# POST /tts


def test_tts_returns_wav(base_url):
    status, headers, body = _post(base_url + "/tts",
                                  {"text": "the beacon holds"})
    assert status == 200
    assert headers.get("Content-Type") == "audio/wav"
    assert body[:4] == b"RIFF"
    assert body[8:12] == b"WAVE"
    # the chosen Suchel rides back in the header (ASCII case is verbatim)
    assert headers.get("X-Suchel") == "kad tan-a=ka."
    assert headers.get("X-IPA")


def test_tts_base64(base_url):
    status, headers, body = _post(
        base_url + "/tts?format=base64", {"text": "the beacon holds"})
    assert status == 200
    assert headers.get("Content-Type", "").startswith("application/json")
    obj = json.loads(body)
    assert obj["suchel"] == "kad tan-a=ka."
    wav = base64.b64decode(obj["wav_base64"])
    assert wav[:4] == b"RIFF"


def test_tts_suchel_input(base_url):
    # Suchel input is spoken as given, not re-translated to English
    status, _headers, body = _post(
        base_url + "/tts", {"text": "ver ish-ol.", "direction": "su2en"})
    assert status == 200
    assert body[:4] == b"RIFF"


def test_tts_missing_text_is_400(base_url):
    try:
        _post(base_url + "/tts", {})
    except urllib.error.HTTPError as e:
        assert e.code == 400
    else:
        pytest.fail("expected 400")


# ---------------------------------------------------------------------------
# CORS preflight


def test_options_preflight(base_url):
    req = urllib.request.Request(base_url + "/translate", method="OPTIONS")
    with urllib.request.urlopen(req, timeout=10) as r:
        assert r.status in (200, 204)
        assert r.headers.get("Access-Control-Allow-Origin") == "*"
        methods = r.headers.get("Access-Control-Allow-Methods", "")
        assert "POST" in methods and "OPTIONS" in methods


# ---------------------------------------------------------------------------
# the OpenAPI dict and the committed YAML never drift


def test_openapi_yaml_matches_dict():
    # the committed file is exactly what the dict dumps to — they cannot drift
    with open(server.OPENAPI_YAML_PATH, encoding="utf-8") as fh:
        on_disk = fh.read()
    assert on_disk == server.openapi_yaml()


def test_openapi_yaml_is_wellformed_and_faithful():
    # An independent structural read (a tiny key:value scanner, no PyYAML): the
    # YAML carries the load-bearing facts from the dict, and every schema $ref
    # resolves against components.schemas.
    text = server.openapi_yaml()
    pairs = _scan_scalars(text)
    last = dict(pairs)             # last value seen per key
    values = {v for _, v in pairs}
    assert last["openapi"] == server.OPENAPI_SPEC["openapi"]
    assert last["version"] == __version__
    assert last["url"] == "http://localhost:8787"
    assert "translateText" in values
    assert "synthesizeSpeech" in values
    declared = set(server.OPENAPI_SPEC["components"]["schemas"])
    refs = set(re.findall(r"#/components/schemas/(\w+)", text))
    assert refs and refs <= declared


def _scan_scalars(text):
    # (key, scalar) pairs — a tiny independent read, tolerant of `- ` list items
    out = []
    for line in text.split("\n"):
        m = re.match(r'\s*(?:-\s+)?"?([A-Za-z0-9_$./-]+)"?:\s+"?(.*?)"?\s*$',
                     line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


# ---------------------------------------------------------------------------
# CLI parser wiring


def test_cli_translate(capsys):
    main(["translate", "the beacon holds"])
    out = capsys.readouterr().out
    assert "kad tan-a=ka." in out
    assert "hold" in out


def test_cli_translate_json(capsys):
    main(["translate", "ver ish-ol.", "--to", "su2en", "--json"])
    out = capsys.readouterr().out
    obj = json.loads(out)
    assert obj["direction"] == "su2en"
    assert "truth" in obj["text"]


def test_cli_say_writes_wav(capsys, tmp_path):
    wav = tmp_path / "line.wav"
    main(["say", "the beacon holds", "-o", str(wav)])
    assert wav.read_bytes()[:4] == b"RIFF"
    out = capsys.readouterr().out
    assert "kad tan-a=ka." in out


def test_cli_serve_help_does_not_block():
    # --help must exit(0) via argparse, never start the server
    with pytest.raises(SystemExit) as exc:
        main(["serve", "--help"])
    assert exc.value.code == 0

