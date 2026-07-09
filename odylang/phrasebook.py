"""The Sūchel phrasebook: all 41 ready-to-letter lines of docs/02.

Every line is *composed from the grammar, not around it* (docs/02 intro):
the Sūchel words are built exclusively through :mod:`odylang.suchel_grammar`
constructors — never raw strings — so the romanized text, morpheme gloss,
IPA and docs/04 rhythm array are all generated, then locked against the
codex by tests/test_phrasebook.py.

Data carried per line: the codex pronunciation string verbatim (with its
brackets), the translation, and an abridged usage note.  Documented
exceptions used here:

* line 01 *ish-ol* is [iˈʃol] — lexicalized greeting prosody (docs/02 §01,
  docs/04 line 01): built with ``stress_override=1``;
* entangled pronoun + case stressing *-mai* (line 02 *ishmai-ol*
  [iʃˈmai.ol], line 31 *enmai-eth* [enˈmai.eth]) is automatic in the core;
* line 07 *en jed-a=mi* is the attested bare motion verb (casual
  leave-taking): built with ``bare_motion_ok=True``;
* line 18 *oshu* is the denominal imperative written solid (docs/02 §04
  intro and §18): built with ``solid=True``;
* line 29's satellite is *zu* 'adrift' — the death formula patterns it
  with the depth directionals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .suchel_grammar import (Break, Sentence, Word, compound, directional,
                             imperative, noun, particle, pronoun, verb)

#: docs/02 section headings.
SECTIONS: Dict[str, str] = {
    "A": "HAILS & PARTINGS",
    "B": "BRIDGE CHATTER",
    "C": "CURSES & OATHS",
    "D": "PRAYERS & BLESSINGS",
    "E": "THE DRIVE-LITANY",
}


@dataclass
class Line:
    number: int
    section: str        # 'A'..'E'
    sentence: Sentence
    ipa: str            # the codex pronunciation string, verbatim
    translation: str
    note: str           # usage note, abridged from docs/02


def _n(form: str, gloss: str) -> Word:
    """A bare lexical word (noun or uninflected content word)."""
    return Word.plain(form, gloss)


def _sornmai() -> Word:
    return noun("Sōrn", entangled=True, mai_sep="", gloss="drive")


def _zukad(case=None) -> Word:
    return noun("zu", second="kad", gloss="dark.time", case=case)


def _build() -> List[Line]:
    L: List[Line] = []

    def add(n, sec, words, ipa, trans, note, punct=".", breaks=(), gap=False):
        L.append(Line(n, sec, Sentence(list(words), punct, list(breaks), gap),
                      ipa, trans, note))

    # -- A · HAILS & PARTINGS -------------------------------------------------
    add(1, "A",
        [_n("ver", "truth"), pronoun(2, case="DAT", stress_override=1)],
        "[ver iˈʃol]",
        "Truth to you. — Hello.",
        "The standard hail, any register. Neutral, safe, universal.")
    add(2, "A",
        [_n("ver", "truth"), pronoun(2, entangled=True, case="DAT")],
        "[ver iʃˈmai.ol]",
        "Truth to you, kin. — the warm reply.",
        "Answering 01 with the entangled form upgrades the greeting to "
        "intimacy. Answering a stranger this way is forward; answering crew "
        "any other way is cold.")
    add(3, "A",
        [particle("ō"), _n("mān", "crew.hand")],
        "[oː maːn]",
        "Hey, mate!",
        "Attention-getter across a deck or a bar. Friendly-rough.",
        punct="!")
    add(4, "A",
        [_n("kad", "beacon"), pronoun(2, case="ACC"), imperative("tan", "hold")],
        "[kad ˈi.ʃen ˈta.nu]",
        "Beacon keep you.",
        "Parting, when the other stays inside coverage. The default farewell "
        "of settled folk.")
    add(5, "A",
        [_zukad("LOC"), _n("lesh", "alignment"), pronoun(2, case="ACC"),
         imperative("tan", "hold")],
        "[ˈzu.ka.deth · leʃ ˈi.ʃen ˈta.nu]",
        "In the dark, may fair phase keep you.",
        "Parting for someone leaving coverage: where no beacon can vouch, "
        "only lesh — alignment, luck — remains to invoke. Solemn.",
        breaks=[Break(0, ",", "·")])
    add(6, "A",
        [imperative("hōl", "surface"), _n("ret", "again")],
        "[ˈhoː.lu ret]",
        "Surface again. — the divers' goodbye.",
        "Between divers, always. Saying a 04/05-type goodbye to a diver "
        "about to dive is a faux pas verging on omen.")
    add(7, "A",
        [pronoun(1), verb("jed", "T", "mi", gloss="go", bare_motion_ok=True)],
        "[en dʒeˈda.mi]",
        "I'm off — by my own clock.",
        "Casual leave-taking. The =mi anchor is the shrug: my time, my "
        "business.")
    add(8, "A",
        [imperative("men", "wait"), _n("mān", "crew.hand")],
        "[ˈme.nu maːn]",
        "Hold on, mate.",
        "Stopping someone mid-turn; softening bad news to come.",
        breaks=[Break(0, ",")])

    # -- B · BRIDGE CHATTER ---------------------------------------------------
    add(9, "B",
        [particle("nuv"), imperative("jed", "go", directional="nuv")],
        "[nuv ˈdʒe.du]",
        "Take her down!",
        "The dive order. Motion verbs demand a depth word — the command is "
        "two syllables of pure tower-grammar.",
        punct="!")
    add(10, "B",
        [particle("hau"), imperative("jed", "go", directional="hau")],
        "[hau ˈdʒe.du]",
        "Bring her up!",
        "The surfacing order; also shouted as an abort.",
        punct="!")
    add(11, "B",
        [_n("jel", "seam"), imperative("id", "open")],
        "[dʒel ˈi.du]",
        "Open the seam.",
        "The crossing order. By fleet custom spoken quietly, never "
        "shouted — you do not shout at the seam.")
    add(12, "B",
        [_sornmai(), imperative("tan", "hold")],
        "[ˈsoːrn.mai ˈta.nu]",
        "Hold, my Sōrn.",
        "Murmured to the engine under strain. The entangled -mai on one's "
        "own drive is universal among pilots; the drive is kin, not property.",
        breaks=[Break(0, ",")])
    add(13, "B",
        [_n("kad", "beacon"), verb("ver", "T", "ka", gloss="speak.true"),
         particle("vu")],
        "[kad veˈra.ka vu]",
        "Does the beacon hold? — Are we in coverage?",
        "The standard nav query after any maneuver.",
        punct="?")
    add(14, "B",
        [verb("ver", "T", "ka", gloss="true")],
        "[veˈra.ka]",
        "It holds. — Lock confirmed.",
        "The good answer. Two words that mean we exist in shared time.")
    add(15, "B",
        [particle("vo"), verb("ver", "T", "ka", gloss="true"), _zukad()],
        "[vo veˈra.ka · ˈzu.kad]",
        "No lock. We're dark.",
        "The bad answer. The single word zukad as a sentence is fleet "
        "shorthand for we are beyond all vouching.",
        breaks=[Break(1, ".", "·", "·")])
    add(16, "B",
        [_n("tem", "pattern"), imperative("tan", "hold"),
         pronoun(1, plural=True), _n("om", "all")],
        "[tem ˈta.nu · ˈe.ni om]",
        "Hold the pattern, all hands.",
        "Pre-crossing order. tem is both the ship's formation and, "
        "ominously, the Κ5 word for what may or may not survive.",
        breaks=[Break(1, ",", "·", "·")])

    # -- C · CURSES & OATHS ---------------------------------------------------
    add(17, "C",
        [compound("jel", "vos", gloss="seam.scar")],
        "[ˈdʒel.vos]",
        "Scar! — Damn it.",
        "The everyday expletive, for things gone subtly wrong. A scar is "
        "where the vacuum lies to you.",
        punct="!")
    add(18, "C",
        [compound("vel", "osh", gloss="Formless.mouth"),
         pronoun(2, case="ACC"), imperative("osh", "swallow", solid=True)],
        "[ˈve.loʃ ˈi.ʃen ˈo.ʃu]",
        "May a Formless mouth swallow you!",
        "The strong curse — fight-starting in any port bar. Invoking the "
        "mouths at someone is wishing them the one fate with no verdict.",
        punct="!")
    add(19, "C",
        [compound("vo", "tem", sep="-", glosses=("NEG", "pattern"))],
        "[ˈvo.tem]",
        "Shapeless! — you incoherent waste.",
        "Insult for incompetence. To have no tem is to be the thing that "
        "couldn't even survive a crossing in principle.",
        punct="!")
    add(20, "C",
        [_n("kru", "blood"), noun("jel", case="LOC", gloss="seam")],
        "[kru ˈdʒe.leth]",
        "Blood at the seam!",
        "Oath of dismay — invokes failed condensation, the smeared "
        "crossing. Said when witnessing disaster.",
        punct="!")
    add(21, "C",
        [pronoun(3), particle("vo"), imperative("hōl", "surface")],
        "[an vo ˈhoː.lu]",
        "May he never surface!",
        "The vicious curse for an enemy diver — the exact inversion of "
        "farewell 06. Unforgivable between crew.",
        punct="!")
    add(22, "C",
        [_n("gal", "the.still"), pronoun(2, case="ACC"),
         imperative("tan", "hold")],
        "[gal ˈi.ʃen ˈta.nu]",
        "May the Still hold you!",
        "Pilot's curse — gal is the becalmed vacuum, the Dead-Sea. Wishing "
        "someone held motionless in structureless calm: a sailor's hell.",
        punct="!")
    add(23, "C",
        [noun("vurel", case="GEN", gloss="madman"), _n("chel", "speech")],
        "[ˈvu.re.len tʃel]",
        "Madman's talk!",
        "Dismissal of nonsense — with built-in dramatic irony, since the "
        "Madman's Theorem is the one thing that could break the trap.",
        punct="!")
    add(24, "C",
        [pronoun(1), verb("ver", "T", "mi", gloss="speak.true")],
        "[en veˈra.mi]",
        "I swear by my own clock: …",
        "The oath-formula: swearing on =mi renounces all external backing, "
        "the gravest oath. Breaking a =mi oath makes one vo-tem.",
        punct=": …")

    # -- D · PRAYERS & BLESSINGS ----------------------------------------------
    add(25, "D",
        [noun("Tur", entangled=True, mai_sep="", gloss="Tower"),
         pronoun(1, case="ACC"), imperative("tan", "hold")],
        "[ˈtur.mai ˈe.nen ˈta.nu]",
        "O our Tower, hold me.",
        "The universal short prayer — the entangled -mai claims kinship "
        "with the whole hierarchy. Said at need, by everyone.",
        breaks=[Break(0, ",")])
    add(26, "D",
        [_n("kad", "beacon"), noun("om", case="DAT", gloss="all"),
         imperative("ver", "speak.true")],
        "[kad ˈo.mol ˈve.ru]",
        "Beacon, speak true for all.",
        "Assembly versicle, opening services. The congregation is praying "
        "for shared time itself.")
    add(27, "D",
        [_n("jel", "seam"), noun("lesh", case="LOC", gloss="alignment"),
         imperative("id", "open")],
        "[dʒel ˈle.ʃeth ˈi.du]",
        "Seam, open in fair phase.",
        "The pre-crossing prayer — whispered by crew as the drive spins "
        "up. Companion to order 11.")
    add(28, "D",
        [pronoun(1, entangled=True),
         noun("nexath", entangled=True, mai_sep="-", gloss="gap"),
         verb("tan", "T", "mi", gloss="hold")],
        "[ˈen.mai ˈne.ksath.mai taˈna.mi]",
        "We keep our gaps.",
        "The crossers' creed: gaps take entangled possession — the holes "
        "in a life are kin, not property. Said at reunions, before dives.")
    add(29, "D",
        [pronoun(3), directional("zu"),
         verb("jed", "T", "mi", pfv=True, gloss="go", directional="zu")],
        "[an zu dʒedˈta.mi]",
        "She has gone adrift. — She is dead.",
        "The death formula: plain T — a fact — but anchored =mi: only her "
        "own clock knows when. The fleet does not say died.")
    add(30, "D",
        [verb("hōl", "Ts", "zu", gloss="surface"), _n("maiel", "kinsman")],
        "[hoːˈle.ʃe.zu ˈmai.el]",
        "Surface — seam-true — in the dark, kinsman.",
        "Said over the unreturned: their surfacing can be neither asserted "
        "nor denied, so the mourning mood is the self-dual one.",
        breaks=[Break(0, ",")])
    add(31, "D",
        [_n("ver", "truth"), pronoun(1, entangled=True, case="LOC"),
         verb("ve", "T", "ka", gloss="be")],
        "[ver enˈmai.eth veˈa.ka]",
        "Truth is among us.",
        "Assembly congregational response — the confident register: plain "
        "T, beacon-anchored, truth located inside coverage.")
    add(32, "D",
        [compound("eshe", "ver", sep="-", glosses=("seam.true", "truth")),
         verb("men", "T", "zu", gloss="wait")],
        "[ˈe.ʃe.ver meˈna.zu]",
        "The Tragic Truth waits in the dark.",
        "Heretical folk-prayer, never in Assembly hearing: a T-mood "
        "assertion about the T• truth, anchored where no one can check.")

    # -- E · THE DRIVE-LITANY -------------------------------------------------
    add(33, "E",
        [_sornmai(), _n("ān", "breath"), imperative("tan", "hold")],
        "[ˈsoːrn.mai aːn ˈta.nu]",
        "My Sōrn, hold breath.",
        "Litany opening — the engineer addresses the drive as kin and "
        "stills it.",
        breaks=[Break(0, ",")])
    add(34, "E",
        [_n("ān", "breath"), verb("tan", "T", "mi", gloss="hold")],
        "[aːn taˈna.mi]",
        "Breath held — by our clock.",
        "Crew response. Reports take =mi from here on: the ship is about "
        "to leave every other clock behind.")
    add(35, "E",
        [particle("nuv"), particle("nuv"), noun("jel", case="DAT", gloss="seam")],
        "[nuv nuv ˈdʒe.lol]",
        "Down, down, to the seam.",
        "The descent chant — pure directionals, no verb at all. Repeatable "
        "panel-over-panel as the dive deepens.",
        breaks=[Break(0, ","), Break(1, ",")])
    add(36, "E",
        [compound("nuv", "ran", gloss="running.under"),
         verb("ve", "T", "mi", gloss="be")],
        "[ˈnuv.ran veˈa.mi]",
        "We are running under.",
        "The vertigo confirmed — the crew names the desync as it takes "
        "them.")
    add(37, "E",
        [_n("jel", "seam"), verb("id", "Ts", "mi", gloss="open")],
        "[dʒel iˈde.ʃe.mi]",
        "The seam opens — seam-true.",
        "Phase-lock called. First T• of the litany: from here, assertion "
        "and denial weigh the same.")
    add(38, "E",
        [particle("ne")],
        "[ne]",
        "— (the interval that has no sentence)",
        "Spoken aloud by all hands at the crossing — the only word said "
        "inside. Letter as its own black panel.",
        gap=True)
    add(39, "E",
        [verb("hōl", "Ts", "zu", pfv=True, gloss="surface"), particle("vu")],
        "[hoːlˈte.ʃe.zu vu]",
        "Surfaced — seam-true, in the dark — yes?",
        "The far-side call. Even the question of arrival must be asked in "
        "T•, in dark time.",
        punct="?")
    add(40, "E",
        [verb("hōl", "Ts", "zu", pfv=True, gloss="surface"),
         pronoun(1, entangled=True), verb("ve", "T", "mi", gloss="be")],
        "[hoːlˈte.ʃe.zu · ˈen.mai veˈa.mi]",
        "Surfaced. We are — by our own clock.",
        "The Resurrection response: the crossing stays T•, but existence "
        "is reasserted in plain T, anchored only to proper time.",
        breaks=[Break(0, ".", "·", "·")])
    add(41, "E",
        [_n("kad", "beacon"), _n("ret", "again"),
         verb("ver", "T", "ka", gloss="true")],
        "[kad ret veˈra.ka]",
        "The beacon holds again.",
        "Reacquisition — the litany's release of tension, the first =ka "
        "since line 33. Letter it small, after silence.")

    return L


LINES: List[Line] = _build()
BY_NUMBER: Dict[int, Line] = {ln.number: ln for ln in LINES}


def line(number: int) -> Line:
    return BY_NUMBER[number]
