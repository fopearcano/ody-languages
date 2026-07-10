# Setup & run

Everything here is **Python ≥ 3.9, standard library only — the package has no
dependencies to install.** Pick the entry point you want; they range from
"open a file in a browser" to "run a local LibreChat agent."

---

## 0. Fastest path — nothing to set up

The generated pages are fully self-contained (no server, no network). Just open
them in a browser:

- `examples/translator.html` — the translator chat: type English or Sūchel, get
  the translation with IPA, gloss, Navcher lettering, and synthesized speech.
- `examples/odylang-web.html` — the interactive codex: the whole language family,
  lexicons, phrasebook, texts, script, and page studies.

If all you want is to *use* the translator, you're done. The rest is for running
it locally from source.

---

## 1. Get the code (the branch matters)

The implementation lives on the branch `claude/peterson-language-system-q2z1l9`.
The default branch (`main`) contains only the source documents, so a fresh clone
lands with no code — check out the branch:

```bash
git clone <repo-url> ody-languages      # or cd into an existing clone
cd ody-languages
git fetch origin claude/peterson-language-system-q2z1l9
git checkout claude/peterson-language-system-q2z1l9
git pull                                 # ensure it's current (v1.2.0)
```

Confirm you're on the right code — this file must exist:

```bash
ls odylang/server.py
```

---

## 2. Run it — no install needed

From the repo root, the package runs directly with `python3 -m`:

```bash
python3 -m odylang.cli translate "the beacon holds"
python3 -m odylang.cli say "surface again" -o hail.wav
python3 -m odylang.cli serve
```

---

## 3. (Optional) install the `odylang` command

So you can type `odylang …` instead of `python3 -m odylang.cli …`:

```bash
python3 -m pip install -e .
odylang --version        # -> odylang 1.2.0
```

Two common snags:

- **`command not found: pip`** (macOS/zsh) — use `python3 -m pip`, not bare `pip`.
- **`error: externally-managed-environment`** (Homebrew / PEP 668) — use a venv:

  ```bash
  python3 -m venv .venv && source .venv/bin/activate
  pip install -e .
  ```

If a command shows an out-of-date subcommand list, your installed copy is stale —
re-run `python3 -m pip install -e .`. `odylang --version` tells you what you're
actually running.

---

## 4. The four ways to use it

### A. Open a page in a browser (zero setup)

```bash
open examples/translator.html     # translator chat   (Linux: xdg-open)
open examples/odylang-web.html    # interactive codex
open examples/odylang-manual.pdf  # the printable grammar/vocab/sentence manual
```

All three are prebuilt, self-contained, and work offline.

### B. Command line

```bash
odylang translate "take her down"            # -> nuv jed-u!  (DOWN go-IMP)
odylang translate "hōl-t-eshe=zu." --to su2en
odylang say "open the seam" -o seam.wav      # synthesize speech to a WAV file
odylang phrase 40                            # a phrasebook line, four ways
odylang family '*gel-'                       # one proto-word through every mouth
odylang vocab --domain sea                   # the coined working vocabulary
odylang page vigil --seed 42 -o vigil.svg    # a Current Hand page study
odylang manual -o odylang-manual.pdf         # the printable PDF manual
```

Run `odylang --help` for the full command list.

### C. The local server (chat page + API)

This is the same service LibreChat calls.

```bash
odylang serve                 # -> http://127.0.0.1:8787   (--host / --port to change)
```

Then open `http://127.0.0.1:8787/` for the chat page, or call the API directly:

```bash
# translate (English or Sūchel; direction auto-detected)
curl -X POST http://127.0.0.1:8787/translate \
     -H 'Content-Type: application/json' \
     -d '{"text":"the beacon holds"}'

# synthesize speech (English is translated to Sūchel first) -> WAV
curl -X POST http://127.0.0.1:8787/tts \
     -H 'Content-Type: application/json' \
     -d '{"text":"surface again"}' --output hail.wav
```

Other endpoints: `GET /health`, `GET /openapi.json`, `GET /voice_spec`.

### D. The LibreChat agent (conversational, your choice of model)

The translator itself is **not an LLM** — the Sūchel, grammar, and audio are
deterministic. The LLM in LibreChat is only the conversational agent that calls
the translator as a tool, so which model you run is free choice.

1. Start the server and leave it running:

   ```bash
   odylang serve
   ```

2. In LibreChat: **Agents → Create Agent → Add Action → Import from URL** and
   paste `http://localhost:8787/openapi.json`. (If LibreChat runs in Docker, use
   `http://host.docker.internal:8787/openapi.json` so the container can reach your
   host.) It discovers two operations: `translateText` and `synthesizeSpeech`.

3. Paste the **Name / Description / Instructions** from
   [`integrations/librechat/agent.md`](integrations/librechat/agent.md) into the
   agent, and attach the Action.

4. **Choose the model** (details + `librechat.yaml` snippets in `agent.md`):

   - **LM Studio (local, offline):** start its server, add a custom endpoint
     `baseURL: http://localhost:1234/v1`.
   - **Ollama (local, offline):** `baseURL: http://localhost:11434/v1`.
   - **Anthropic (Claude) / OpenAI (cloud):** built-in endpoints — add your key.

   Caveat: for the agent to call the tool *automatically* mid-chat, the model must
   support function/tool calling. Cloud models do reliably; many recent local
   models do too, but smaller ones can be unreliable. If yours isn't tool-capable,
   translate via the chat page (`http://localhost:8787/`) or `curl` instead.

See [`integrations/librechat/README.md`](integrations/librechat/README.md) for a
one-page overview and endpoint reference.

---

## 5. (Optional) run the test suite

The package needs no dependencies, but the test runner does:

```bash
python3 -m pip install pytest
python3 -m pytest tests/ -q          # 1418 passing
```

---

## Minimal recipe

```bash
git checkout claude/peterson-language-system-q2z1l9
python3 -m odylang.cli serve
# open http://127.0.0.1:8787/
```

If something errors, the two most common causes are being on `main` instead of
the branch, or a stale editable install — check `ls odylang/server.py` and
`odylang --version`.
