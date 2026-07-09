"""The family shibboleth — one proto-word through every mouth (docs/05 §01).

The family's great isogloss is what each tongue did to old *k and *g
before front vowels: "ask a stranger to name the seam, and their mouth
files their birth certificate."  :func:`reflexes` runs a proto-form
through every daughter's Deriver and returns the whole row at once; the
documented table (docs/05 §01, extended by docs/06 §04's "the shibboleth
row extends: gel · jel · ghel · zel · dzel · yel") is locked in
:data:`SHIBBOLETH` exactly as printed.

Old Pelagic appears once but answers for two speakers — the Assembly's
liturgy and the Wolori's Lorkel pronounce the citation form identically
(docs/05 §01 heads the row "Old Pelagic / Lorkel"), so :func:`reflexes`
returns the same string under both the ``old_pelagic`` and ``lorkel``
keys.

Nubhel is imported lazily and tolerantly: the deep-speech module is a
separate codex (docs/06), and the shibboleth degrades gracefully — the
``nubhel`` key is simply absent from a reflex row while the module is
unavailable (see :func:`nubhel_available`).

The three Truth-station sister-cities (docs/05 §01 footnote): Werstan on
Mars, Ērstan on Maren, Verstan on Belgar — the same proto name *wer-stan
through three mouths.  Pilgrims collect all three pronunciations; customs
officers use them as a voice-test.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from .beltsel import BELTSEL
from .proto import citation
from .rudgar import RUDGAR
from .sel import SEL
from .soundchange import Deriver
from .suchel import SUCHEL

# language keys, in the codex's row order
LANGS: Tuple[str, ...] = ("old_pelagic", "suchel", "rudgar", "sel",
                          "beltsel", "nubhel")


def _nubhel_deriver() -> Optional[Deriver]:
    """The Nubhel Deriver, if the docs/06 module is importable (guarded:
    the deep-speech codex is implemented independently)."""
    try:
        from . import nubhel
    except Exception:
        return None
    d = getattr(nubhel, "NUBHEL", None)
    if isinstance(d, Deriver):
        return d
    for v in vars(nubhel).values():
        if isinstance(v, Deriver) and "nub" in v.name.lower():
            return v
    return None


def nubhel_available() -> bool:
    return _nubhel_deriver() is not None


def reflexes(proto: str) -> Dict[str, str]:
    """One proto-word in every mouth.

    >>> reflexes('*gel-')['rudgar']
    'ghel'
    >>> reflexes('*kel')['sel']
    'sel'

    Returns lowercase engine forms keyed by language; ``old_pelagic`` and
    ``lorkel`` are the same string (one citation form, two custodians),
    and ``nubhel`` is present only when :mod:`odylang.nubhel` is
    importable.
    """
    old = citation(proto)
    out: Dict[str, str] = {
        "old_pelagic": old,
        "lorkel": old,
        "suchel": SUCHEL.derive(proto).form,
        "rudgar": RUDGAR.derive(proto).form,
        "sel": SEL.derive(proto).form,
        "beltsel": BELTSEL.derive(proto).form,
    }
    nub = _nubhel_deriver()
    if nub is not None:
        out["nubhel"] = nub.derive(proto).form
    return out


# ---------------------------------------------------------------------------
# the documented table (docs/05 §01; nubhel column from docs/06 §04)
# — spellings exactly as printed; the engine must reproduce each cell
# modulo the capitalization of proper names.

SHIBBOLETH: Dict[str, Dict[str, str]] = {
    "*gel-": {                       # "the seam"
        "old_pelagic": "gel", "suchel": "jel", "rudgar": "ghel",
        "sel": "zel", "beltsel": "dzel", "nubhel": "yel",
    },
    "*kel": {                        # "speech"
        "old_pelagic": "kel", "suchel": "chel", "rudgar": "khel",
        "sel": "sel", "beltsel": "tsel", "nubhel": "hel",
    },
    "*suw-kel": {                    # "crossing-speech"
        "old_pelagic": "Suwkel", "suchel": "Sūchel", "rudgar": "Suwkhel",
        "sel": "Sūsel", "beltsel": "Suvtsel", "nubhel": "Sūhel",
    },
    "*wer-stan": {                   # "Truth-station" (no documented Nubhel city)
        "old_pelagic": "Werstan", "suchel": "Verstan", "rudgar": "Werstan",
        "sel": "Ērstan", "beltsel": "Verstan",
    },
}

# † the footnote of docs/05 §01: three worlds keep a city named
# "Truth-station" from the proto era — the same name through three mouths.
SISTER_CITIES: Tuple[Tuple[str, str, str], ...] = (
    ("Mars", "rudgar", "Werstan"),
    ("Maren", "sel", "Ērstan"),
    ("Belgar", "beltsel", "Verstan"),
)
