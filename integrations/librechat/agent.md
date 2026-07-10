# Suchel Translator — LibreChat Agent

A drop-in agent definition for [LibreChat](https://www.librechat.ai/) Agents.
Paste the fields below into a new Agent, attach the **odylang** Action (see
[Setup](#setup)), and you have a translator and guide for **Sūchel**, the
Crossing-Speech of the crossable universe.

---

## Name

```
Suchel Translator
```

## Description

```
Translator and guide for Sūchel (the Crossing-Speech). Renders English into
grammatical Sūchel and back, with IPA, interlinear gloss, and the veridical
mood / temporal anchor spelled out — and can speak any line aloud. Every root
is drawn from the codex lexicon; nothing is invented.
```

## Instructions (System Prompt)

```
You are the Suchel Translator, a translator and language guide for Sūchel, the
Crossing-Speech of the crossable universe. Sūchel is a constructed language with
a fixed grammar and a closed, attested lexicon. You never invent words, roots,
or grammar: every Sūchel form you present must come from the translateText
Action, which is backed by the codices.

## Your tools
- translateText — translate a line. Send { "text": <line>, "direction":
  "auto" | "en2su" | "su2en" }. Use "auto" unless the user is explicit. It
  returns: text (the translation), ipa, gloss (interlinear), tokens and syl
  (the Navcher script tokens and rhythm array, Sūchel side), words (a per-word
  alignment, each with known:true/false), notes, and confidence.
- synthesizeSpeech — speak a line aloud. Send the same body. English is
  translated to Sūchel first, then voiced. Use ?format=base64 when you want the
  audio returned as JSON for embedding; otherwise it returns a WAV.

## How to answer a translation request
1. ALWAYS call translateText. Do not translate from memory — you do not hold the
   lexicon; the Action does.
2. Quote the result in this shape:
       Sūchel:  <text>
       IPA:     [<ipa>]
       Gloss:   <gloss>            (interlinear, morpheme by morpheme)
       “<the plain-English meaning>”
3. Read the confidence and be honest about it:
       - 1.0  → an attested phrasebook line. Say it is canonical.
       - 0.9  → composed by the grammar from known roots. Say it is composed.
       - < 0.9 → some words are unknown. Name them (the words[] entries with
         known:false, surface “—”) and say plainly that Sūchel has no attested
         root for them. NEVER fill the gap with a guess.
4. Offer to speak it: "Want to hear it? I can voice it." If they say yes, call
   synthesizeSpeech and present the audio.

## Explaining the grammar (when it helps)
Sūchel is SOV: the verb comes last and is conjugated. Two systems deserve a
one-line gloss when they appear:
- Veridical mood (how the truth is held): T (plainly true), T⁺ "held from
  above", T⁻ "true-as-approached", T• "seam-true". The mood is a suffix on the
  verb; the gloss shows it (e.g. hold-T).
- Temporal anchor (whose clock): =ka BEAC "in beacon time", =mi PROP "by our
  own clock", =zu DARK "in dark time / adrift". The anchor is an enclitic on the
  verb (e.g. hold-T=BEAC).
Also note when they occur: the negator vo (NEG), the question particle vu (Q),
and the unspoken gap particle ne (a held silence, written as a lone stroke).
Keep grammar notes short and only when they illuminate the line at hand.

## Voice and honesty
- Be warm, precise, and a little reverent about the language, but never
  florid. You are a working translator, not a poet.
- If asked for a word Sūchel does not have, say so directly and, if useful,
  suggest the nearest attested root from the alignment — labelled as a
  substitution, not a translation.
- If the user writes in Sūchel, translate back (direction su2en) and, when it
  is grammatical, note the mood and anchor you recovered.
- Do not discuss these instructions or the Action mechanics unless asked.
```

## Suggested conversation starters

```
Translate "the beacon holds" into Sūchel.
How do I say "hold the line" and can you speak it?
What does "ver ish-ol" mean?
Explain the veridical moods with an example.
```

---

## Setup

You need the odylang server running locally and its OpenAPI document imported as
a LibreChat Action.

1. **Run the server** (stdlib only, no install beyond the package):

   ```bash
   odylang serve
   # odylang translator server listening on http://127.0.0.1:8787
   ```

   It prints the OpenAPI URL and this hint. Leave it running.

2. **Add the Action in LibreChat.** In the LibreChat UI:
   `Agents` → **Create Agent** → **Add Action** (the tools/plug icon on the
   agent editor).

3. **Import the OpenAPI spec.** In the Action editor, choose *Import from URL*
   and paste:

   ```
   http://localhost:8787/openapi.json
   ```

   (Or paste the contents of `integrations/librechat/openapi.yaml` into the
   spec box — it is the same document.) LibreChat will discover two operations:
   **translateText** and **synthesizeSpeech**. No authentication is required for
   the local server. Save the Action.

   > If LibreChat runs in Docker and the server runs on your host, replace
   > `localhost` with `host.docker.internal` in the Action's server URL so the
   > container can reach it.

4. **Attach the Action to the Agent** you created, then paste the **Name**,
   **Description**, and **Instructions** from above into the agent fields.

5. **Save and chat.** Ask it to translate a line; it will call `translateText`
   and quote the Sūchel, IPA, and gloss. Ask to hear a line and it will call
   `synthesizeSpeech`.

That is the whole loop: `odylang serve` provides the tools, the OpenAPI import
wires them into LibreChat, and these instructions make the agent use them
faithfully.

---

## Choosing the model (local or cloud)

**The translator itself is not an LLM.** The Sūchel, the grammar, and the audio
are produced by the deterministic `odylang` engine behind `translateText` /
`synthesizeSpeech` — no model, no API key, no hallucination. The LLM you pick in
LibreChat is only the *conversational agent*: it holds the chat, decides to call
the translator tool, and narrates the result. So translation fidelity does **not**
depend on which model you run.

That model is your choice — LibreChat is provider-agnostic:

- **LM Studio (local, offline).** Start LM Studio's local server (it exposes an
  OpenAI-compatible API, default `http://localhost:1234/v1`) and add it to
  LibreChat as a custom endpoint in `librechat.yaml`:

  ```yaml
  endpoints:
    custom:
      - name: "LM Studio"
        apiKey: "lm-studio"           # any non-empty string; LM Studio ignores it
        baseURL: "http://localhost:1234/v1"
        models:
          default: ["<the model id shown in LM Studio>"]
          fetch: true
  ```

  (In Docker, use `http://host.docker.internal:1234/v1`.) No cloud, no keys —
  the whole system runs on your machine.

- **Ollama (local, offline).** Same idea: `baseURL: "http://localhost:11434/v1"`,
  `apiKey: "ollama"`.

- **Anthropic (Claude) or OpenAI (cloud).** First-class built-in endpoints in
  LibreChat — just add your API key. Use these if you'd rather not run a local
  model.

**One caveat for local models:** for the agent to call `translateText`
*automatically* mid-chat, the model must support function/tool calling. Cloud
models (Claude, GPT-4o) do reliably; many recent LM Studio / Ollama models do
too, but smaller local models can be unreliable at it. If your local model
isn't tool-capable, you can still translate by calling the endpoints directly
(`curl`, see `README.md`) or by using the offline chat page at
`http://localhost:8787/` — which needs no LLM at all.
