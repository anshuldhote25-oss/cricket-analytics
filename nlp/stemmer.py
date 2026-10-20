"""
nlp/stemmer.py - light rule-based suffix stripper for Hindi and Marathi.

Marathi (and to a lesser extent Hindi) glue case markers and plural endings onto the
noun:   नागपूरचे = नागपूर + चे (of)       फलंदाजांमध्ये = फलंदाज + ांमध्ये (among the)
        nagpurche = nagpur + che          powerplaymadhe = powerplay + madhe (in)

This is *conservative* stemming: stem_candidates() only proposes shorter forms; the
caller keeps a candidate only if it matches a known cricket word. That avoids the classic
over-stemming problem of blindly chopping suffixes.

Concepts: morphology, agglutination, stemming vs lemmatisation.
"""
from __future__ import annotations

from .normalize import has_devanagari

# Devanagari: case markers, postpositions, plural endings (longest first matters)
_DEV_SUFFIXES = [
    "ांमध्ये", "ांच्या", "ांपेक्षा", "ियों", "ाओं", "ांना", "ांनी", "ांचे", "ांचा", "ांची", "ांत",
    "मध्ये", "मधील", "मधून", "नुसार", "साठी", "च्या", "चे", "ची", "चा", "ात", "ला", "ों", "ें", "ाँ",
]

# Roman script (Hindi/Marathi typed in English letters) + English plurals
_LAT_SUFFIXES = [
    "anmadhye", "anmadhe", "anmdhe", "amadhe", "madhye", "madhil", "madhun", "madhe", "mdhe", "nusar", "sathi", "anchya", "anche", "ancha",
    "anchi", "chya", "anna", "anni", "che", "chi", "cha", "ala", "on", "es", "s",
]

_DEV_SUFFIXES.sort(key=len, reverse=True)
_LAT_SUFFIXES.sort(key=len, reverse=True)


def stem_candidates(token: str) -> list[str]:
    """Return [token, token-minus-suffix, ...] (original first)."""
    suffixes = _DEV_SUFFIXES if has_devanagari(token) else _LAT_SUFFIXES
    out = [token]
    for suf in suffixes:
        if token.endswith(suf) and len(token) - len(suf) >= 3:
            out.append(token[: -len(suf)])
    return out
