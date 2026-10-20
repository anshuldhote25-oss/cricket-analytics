"""
nlp/normalize.py - text normalization, tokenization and phonetic keys.

Why this file exists
--------------------
Users can type the same question in many ways:
    "powerplay mein sabse kam economy wale gendbaaz"      (Hindi, Roman letters)
    "पावरप्ले में सबसे कम इकॉनमी वाले गेंदबाज़"             (Hindi, Devanagari)
    "powerplay madhe sarvat kami economy asleale golandaj" (Marathi, Roman letters)

Roman-script Hindi/Marathi has NO standard spelling (gendbaaz / gendbaz / gaindbaj ...).
So instead of matching raw strings we map every word - whichever script it is written
in - to a *phonetic key*: a lossy, consonant-centred code. Words that sound alike get
the same key, so "gendbaaz", "gendbaj" and "गेंदबाज़" all collapse to the same key.

Concepts: Unicode normalization, tokenization, transliteration, phonetic hashing
(similar in spirit to Soundex), edit distance.
"""
from __future__ import annotations

import re
import unicodedata

# --------------------------------------------------------------------------- #
# 1. Normalization
# --------------------------------------------------------------------------- #
_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_INVISIBLE = {ord(c): None for c in "​‌‍⁠﻿"}  # ZWSP, ZWNJ, ZWJ ...
_SYMBOLS = [("<=", " under "), (">=", " above "), ("≤", " under "), ("≥", " above "),
            ("<", " under "), (">", " above ")]


def normalize_text(text: str) -> str:
    """Unicode-normalise, unify digits, drop invisible characters, lowercase."""
    t = unicodedata.normalize("NFC", text or "")
    t = t.translate(_INVISIBLE).translate(_DEVANAGARI_DIGITS)
    t = t.replace("़", "")        # nukta:  ज़ -> ज , ड़ -> ड   (बल्लेबाज़ == बल्लेबाज)
    t = t.replace("ँ", "ं")  # chandrabindu -> anusvara (में == मेँ)
    t = t.lower()                      # only affects Latin letters
    for sym, word in _SYMBOLS:
        t = t.replace(sym, word)
    t = re.sub(r"[।॥]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# --------------------------------------------------------------------------- #
# 2. Tokenization
# --------------------------------------------------------------------------- #
# numbers | Latin words | Devanagari words (matras/virama stay inside the word)
_TOKEN_RE = re.compile(r"\d+(?:\.\d+)?|[a-z]+|[ऀ-ॣ०-ॿ]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(normalize_text(text))


def has_devanagari(s: str) -> bool:
    return any("ऀ" <= ch <= "ॿ" for ch in s)


def is_number(tok: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:\.\d+)?", tok))


# --------------------------------------------------------------------------- #
# 3. Devanagari -> Latin transliteration (rough, ITRANS-like)
# --------------------------------------------------------------------------- #
_CONS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "ळ": "l", "व": "v",
    "श": "sh", "ष": "sh", "स": "s", "ह": "h",
}
_VOWELS = {"अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo", "ऋ": "ri",
           "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऑ": "o", "ऍ": "e"}
_MATRAS = {"ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo", "ृ": "ri",
           "े": "e", "ै": "ai", "ो": "o", "ौ": "au", "ॉ": "o", "ॅ": "e"}
_SIGNS = {"ं": "n", "ः": "h"}
_VIRAMA = "्"


def devanagari_to_latin(word: str) -> str:
    out: list[str] = []
    i, n = 0, len(word)
    while i < n:
        ch = word[i]
        if ch in _CONS:
            out.append(_CONS[ch])
            nxt = word[i + 1] if i + 1 < n else ""
            if nxt == _VIRAMA:          # conjunct: no inherent vowel
                i += 2
                continue
            if nxt in _MATRAS:
                out.append(_MATRAS[nxt])
                i += 2
                continue
            out.append("a")             # inherent vowel (removed later by the key)
        elif ch in _VOWELS:
            out.append(_VOWELS[ch])
        elif ch in _SIGNS:
            out.append(_SIGNS[ch])
        elif ch in _MATRAS:             # stray matra
            out.append(_MATRAS[ch])
        i += 1
    return "".join(out)


# --------------------------------------------------------------------------- #
# 4. Keys
# --------------------------------------------------------------------------- #
_CLUSTERS = [("cchh", "C"), ("cch", "C"), ("chh", "C"), ("ch", "C"), ("sh", "s"),
             ("kh", "k"), ("gh", "g"), ("jh", "j"), ("th", "t"), ("dh", "d"),
             ("bh", "b"), ("ph", "p"), ("ck", "k")]
_LETTER_MAP = str.maketrans({"w": "v", "z": "j", "q": "k", "f": "p", "c": "k"})


def light_key(word: str) -> str:
    """Gentle spelling normalisation used for language-ID marker words.
    Keeps vowels (so Hindi 'hai' and Marathi 'ahe' stay different)."""
    w = re.sub(r"[^a-z]", "", word.lower())
    for a, b in (("aa", "a"), ("ee", "i"), ("ii", "i"), ("oo", "u"), ("uu", "u")):
        w = w.replace(a, b)
    w = w.translate(str.maketrans({"w": "v", "z": "j"}))
    return re.sub(r"(.)\1+", r"\1", w)


def phonetic_key(word: str) -> str:
    """Aggressive phonetic hash for Latin-script text (see module docstring)."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return ""
    for a, b in _CLUSTERS:                       # aspirated / affricate clusters
        w = w.replace(a, b)
    w = w.replace("x", "ks").translate(_LETTER_MAP)
    w = re.sub(r"ai|ay|ei|ey", "e", w)           # vowel digraphs
    w = re.sub(r"au|ou", "o", w)
    w = re.sub(r"ee|ii", "i", w)
    w = re.sub(r"oo|uu", "u", w)
    w = w.replace("a", "")                       # schwa deletion: Hindi/Marathi drop it
    w = re.sub(r"(.)\1+", r"\1", w)              # doubled letters
    return w or re.sub(r"[^a-z]", "", word.lower())


def token_key(tok: str) -> str:
    """Script-independent key for one token."""
    if is_number(tok):
        return tok
    if has_devanagari(tok):
        tok = devanagari_to_latin(tok)
    return phonetic_key(tok)


# --------------------------------------------------------------------------- #
# 5. Edit distance (Levenshtein) - used for fuzzy matching of misspellings
# --------------------------------------------------------------------------- #
def levenshtein(a: str, b: str, limit: int = 99) -> int:
    if a == b:
        return 0
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
