"""odylang — the languages of the crossable universe.

One proto-tongue (Old Pelagic) and its daughters, implemented from the
NERV//Pelagian Assembly codices in docs/, built the way Peterson builds
languages: a proto-language, ordered regular sound changes per daughter,
and grammars that encode what each speaker community cannot afford to be
vague about.

Modules
-------
proto        Old Pelagic roots, affixes, and the late-OP verb machinery
soundchange  the ordered rewrite engine shared by every daughter
phonology    family-wide segments, syllabification, IPA
word         morpheme-structured words + the four-rule stress algorithm
suchel       Sūchel, the Crossing-Speech: SC-1..7 + the codex lexicon
suchel_grammar, phrasebook, suchel_texts
             Sūchel morphosyntax, the 41 ready-to-letter lines, the texts
nubhel       Nubhel, the Deep-Speech: D-1..7 + lexicon + grammar + texts
rudgar, sel, beltsel
             the sisters, at naming depth (sound changes + 20 place names)
lorkel       working Old Pelagic: the Wolori's Neo-Pelagic coinages
family       the shibboleth: one proto-word through every mouth
navcher      the fleet script, rendered to SVG
"""

__version__ = "1.0.0"
