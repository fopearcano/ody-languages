"""odylang — command-line access to the languages of the crossable universe.

    odylang derive suchel '*suw-kel'     # replay a sound-change derivation
    odylang family '*gel-'               # one proto-word through every mouth
    odylang lex suchel --domain physics  # dump a lexicon
    odylang places rudgar                # a sister's twenty place names
    odylang phrase 40                    # a phrasebook line, four ways
    odylang phrase --all
    odylang texts suchel                 # the glossed texts
    odylang lorkel                       # the Wolori's Neo-Pelagic coinages
    odylang write 'ver ish-ol' -o hail.svg          # Navcher, careful hand
    odylang write --phrase 40 --hand bridge -o l40.svg
    odylang chart -o navcher.svg         # the full glyph chart
"""

from __future__ import annotations

import argparse
import sys


def _print_derivation(d):
    print(d.trace())


def cmd_derive(args):
    lang = args.lang.lower()
    if lang in ("op", "old-pelagic", "oldpelagic", "lorkel"):
        from .proto import citation
        print(f"{args.proto}  (Old Pelagic citation form — no changes)")
        print(f"  = {citation(args.proto)}")
        return
    derivers = {}
    from .suchel import SUCHEL
    derivers["suchel"] = SUCHEL
    if lang == "nubhel":
        from .nubhel import NUBHEL
        derivers["nubhel"] = NUBHEL
    elif lang == "rudgar":
        from .rudgar import RUDGAR
        derivers["rudgar"] = RUDGAR
    elif lang == "sel":
        from .sel import SEL
        derivers["sel"] = SEL
    elif lang == "beltsel":
        from .beltsel import BELTSEL
        derivers["beltsel"] = BELTSEL
    if lang not in derivers:
        sys.exit(f"unknown language {args.lang!r} "
                 "(suchel, nubhel, rudgar, sel, beltsel, lorkel)")
    _print_derivation(derivers[lang].derive(args.proto))


def cmd_family(args):
    from .family import reflexes
    r = reflexes(args.proto)
    width = max(len(k) for k in r)
    print(f"{args.proto} through every mouth:")
    for lang, form in r.items():
        print(f"  {lang.replace('_', ' '):<{width}}  {form}")


def cmd_lex(args):
    lang = args.lang.lower()
    if lang == "suchel":
        from .suchel import entries
    elif lang == "nubhel":
        from .nubhel import entries
    else:
        sys.exit("lexicons exist for suchel and nubhel; "
                 "for the sisters try: odylang places <lang>")
    for e in entries(args.domain):
        ipa = f"[{e.ipa}]" if e.ipa else ""
        print(f"{e.form:<14} {ipa:<16} {e.gloss}")
        if args.etym:
            print(f"{'':14} {'':16} < {e.etym}")


def cmd_places(args):
    lang = args.lang.lower()
    mods = {"rudgar": "rudgar", "sel": "sel", "beltsel": "beltsel"}
    if lang not in mods:
        sys.exit("place-name tables exist for rudgar, sel, beltsel")
    import importlib
    mod = importlib.import_module(f".{mods[lang]}", __package__)
    for p in mod.PLACES:
        print(f"{p.name:<10} < {p.proto:<12} {p.gloss}")


def cmd_lorkel(args):
    from .lorkel import NEO_PELAGIC, NOTATION_NAMES
    print("Neo-Pelagic — the Wolori's technical coinages (docs/05 §05):")
    for t in NEO_PELAGIC.values():
        formation = " + ".join(t.formation)
        print(f"  {t.form:<8} {formation:<16} {t.meaning}")
        print(f"  {'':8} {'':16} Sūchel reflex: {t.suchel_reflex or '—'}")
    print("\nNotation-names (the zero-tongue):", ", ".join(NOTATION_NAMES))


def _show_line(l):
    print(f"{l.number}  {l.sentence.text()}")
    print(f"    IPA    {l.sentence.ipa()}")
    print(f"    GLOSS  {l.sentence.gloss_line()}")
    print(f"    RHYTHM {' '.join(l.sentence.syl_line())}")
    print(f"    “{l.translation}”")
    if l.note:
        print(f"    use: {l.note}")


def cmd_phrase(args):
    from .phrasebook import LINES, line
    if args.all or args.number is None:
        current = None
        for l in LINES:
            if l.section != current:
                current = l.section
                print(f"\n== {current} ==")
            _show_line(l)
    else:
        _show_line(line(args.number))


def cmd_texts(args):
    lang = (args.lang or "suchel").lower()
    if lang == "suchel":
        from .suchel_texts import K5, TEXTS
        for t in TEXTS:
            print(f"\n== {t.title} ==")
            for p in t.lines:
                print(f"  {p.display()}")
                print(f"    {p.sentence.gloss_line()}")
                print(f"    “{p.translation}”")
            print(f"  — {t.commentary}")
        print("\n== THE SHOWPIECE — Κ5 as conjugation ==")
        for s in K5:
            print(f"  [{s.title} · {s.attribution}]")
            print(f"  {s.sentence.text()}")
            print(f"    {s.sentence.gloss_line()}")
            print(f"    “{s.translation}”")
    elif lang == "nubhel":
        from .nubhel_texts import TEXTS
        for t in TEXTS:
            print(f"\n== {t.title} ==")
            for ln in t.lines:
                tag = f" [{ln.language}]" if ln.language != "Nubhel" else ""
                print(f"  {ln.display}{tag}")
                print(f"    {ln.gloss}")
                print(f"    “{ln.translation}”")
            print(f"  — {t.commentary}")
    else:
        sys.exit("texts exist for suchel and nubhel")


def _sentence_tokens(sentence, hand):
    from .navcher import tokens_bridge, tokens_careful
    out = []
    for w in sentence.words:
        if out:
            out.append(" ")
        if len(w.morphs) == 1 and w.morphs[0].gloss == "GAP":
            out.append("|")  # ne is not spelled — the gap-stroke stands alone
        elif hand == "bridge":
            if len(w.morphs) == 1 and w.morphs[0].gloss == "Q":
                out.append("?")
            else:
                out.extend(tokens_bridge(w))
        else:
            out.extend(tokens_careful(w))
    return out


def cmd_write(args):
    from .navcher import Line, render_svg, tokens_careful
    if args.phrase is not None:
        from .phrasebook import line
        l = line(args.phrase)
        tokens = _sentence_tokens(l.sentence, args.hand)
        label = l.sentence.text()
    else:
        if not args.text:
            sys.exit("give TEXT or --phrase N")
        tokens = tokens_careful(args.text)
        label = args.text
    svg = render_svg([Line(tokens=tokens, label=label)], scale=args.scale)
    _emit(svg, args.out)


def cmd_chart(args):
    from .navcher import render_glyph_chart
    _emit(render_glyph_chart(), args.out)


def _emit(svg, out):
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"wrote {out}")
    else:
        print(svg)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="odylang",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("derive", help="replay a sound-change derivation")
    p.add_argument("lang")
    p.add_argument("proto")
    p.set_defaults(fn=cmd_derive)

    p = sub.add_parser("family", help="one proto-word through every mouth")
    p.add_argument("proto")
    p.set_defaults(fn=cmd_family)

    p = sub.add_parser("lex", help="dump a lexicon")
    p.add_argument("lang")
    p.add_argument("--domain")
    p.add_argument("--etym", action="store_true", help="show derivations")
    p.set_defaults(fn=cmd_lex)

    p = sub.add_parser("places", help="a sister language's place names")
    p.add_argument("lang")
    p.set_defaults(fn=cmd_places)

    p = sub.add_parser("lorkel", help="the Wolori's Neo-Pelagic coinages")
    p.set_defaults(fn=cmd_lorkel)

    p = sub.add_parser("phrase", help="phrasebook lines, four ways")
    p.add_argument("number", nargs="?", type=int)
    p.add_argument("--all", action="store_true")
    p.set_defaults(fn=cmd_phrase)

    p = sub.add_parser("texts", help="the glossed texts")
    p.add_argument("lang", nargs="?")
    p.set_defaults(fn=cmd_texts)

    p = sub.add_parser("write", help="letter a line in Navcher (SVG)")
    p.add_argument("text", nargs="?")
    p.add_argument("--phrase", type=int, help="render phrasebook line N")
    p.add_argument("--hand", choices=("careful", "bridge"), default="careful")
    p.add_argument("--scale", type=float, default=0.5)
    p.add_argument("-o", "--out")
    p.set_defaults(fn=cmd_write)

    p = sub.add_parser("chart", help="the full Navcher glyph chart (SVG)")
    p.add_argument("-o", "--out")
    p.set_defaults(fn=cmd_chart)

    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
