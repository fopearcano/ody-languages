# odylang × LibreChat

This directory turns the odylang Sūchel translator and voice into a
[LibreChat](https://www.librechat.ai/) Agent. Run one stdlib HTTP server
(`odylang serve`), import its OpenAPI document as a LibreChat **Action**, and
attach the [agent definition](agent.md): the agent then translates English ⇄
Sūchel through the real grammar (quoting the Sūchel, IPA, and interlinear
gloss, honest about confidence and unknown words) and can speak any line aloud —
all with no third-party dependencies, backed by the same engine that powers the
offline browser page served at `/`.

- **[`openapi.yaml`](openapi.yaml)** — the OpenAPI 3.1 Action spec. It is
  generated from the single source-of-truth dict in `odylang/server.py` and is
  byte-for-byte what the server serves at `GET /openapi.json` (a test asserts
  they never drift). Import either the URL or this file into LibreChat.
- **[`agent.md`](agent.md)** — the agent Name, Description, Instructions, and
  step-by-step setup.

## Start the server

```bash
odylang serve                      # http://127.0.0.1:8787
odylang serve --host 0.0.0.0 --port 9000
```

## Endpoints, by curl

Health:

```bash
curl -s http://localhost:8787/health
# {"ok": true, "service": "odylang-translator", "version": "1.1.0"}
```

Translate (English → Sūchel; use `"direction":"su2en"` or `"auto"` as needed):

```bash
curl -s http://localhost:8787/translate \
  -H 'Content-Type: application/json' \
  -d '{"text":"the beacon holds","direction":"auto"}'
# {"direction":"en2su","text":"kad tan-a=ka.","ipa":"kad taˈna.ka",
#  "gloss":"beacon hold-T=BEAC","confidence":0.9, ... }
```

Translate back:

```bash
curl -s http://localhost:8787/translate \
  -H 'Content-Type: application/json' \
  -d '{"text":"ver ish-ol.","direction":"su2en"}'
# {"direction":"su2en","text":"truth you.","gloss":"truth you-DAT", ... }
```

Speak a line — WAV bytes, with the chosen Sūchel and IPA in response headers:

```bash
curl -s http://localhost:8787/tts \
  -H 'Content-Type: application/json' \
  -d '{"text":"the beacon holds"}' \
  -D - -o beacon.wav
# ... X-Suchel: kad tan-a=ka.
# ... X-IPA: kad taˈna.ka
```

Speak a line as base64 JSON (handy for a browser or a chat client):

```bash
curl -s 'http://localhost:8787/tts?format=base64' \
  -H 'Content-Type: application/json' \
  -d '{"text":"the beacon holds"}'
# {"wav_base64":"UklGR...","suchel":"kad tan-a=ka.","ipa":"kad taˈna.ka",
#  "content_type":"audio/wav"}
```

The voice specification (the single source a browser synth mirrors):

```bash
curl -s http://localhost:8787/voice_spec
# {"sampleRate":22050,"f0":..., "formants":{...}, "consonants":{...}, ...}
```

The OpenAPI document (import this into a LibreChat Action):

```bash
curl -s http://localhost:8787/openapi.json
```

> Non-ASCII values in the `X-Suchel` / `X-IPA` response headers (macrons, stress
> marks) are percent-encoded (UTF-8); the ASCII-only base64 JSON response
> carries them unescaped.

## The offline page and the LibreChat path

They share one engine. `GET /` serves the interactive translator chat page
(from `odylang.translator_web`; until that module is present the server returns
a placeholder that still names every endpoint) — open it in a browser to
translate and hear Sūchel with **no LibreChat and no network**. The LibreChat
path adds a conversational agent on top of the *same* `/translate` and `/tts`
endpoints: the browser page is the standalone tool, the Action is the same tools
handed to an LLM agent. Because both read from the identical OpenAPI dict and the
identical translator/TTS engines, what you hear in the browser is exactly what
the agent produces.

## CORS

Every endpoint sends `Access-Control-Allow-Origin: *` and answers the `OPTIONS`
preflight, so a browser client or the LibreChat frontend can call the server
directly.
