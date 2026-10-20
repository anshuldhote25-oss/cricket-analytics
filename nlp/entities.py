"""
nlp/entities.py - gazetteer-based named-entity recognition + number/threshold parsing.

Pipeline for one question:
    tokens -> phonetic keys -> longest-match lookup in the lexicon index
              (exact key  ->  stemmed key  ->  fuzzy key)  -> Entity spans
    then numbers are interpreted as either a threshold ("economy under 7")
    or a result limit ("top 10").

Concepts: NER (dictionary / gazetteer approach), longest-match tokenisation,
          morphological back-off (stemming), fuzzy matching (Levenshtein), slot filling.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from .lang_id import _EN_STRONG_SET, _HI_LAT_STRONG, _MR_LAT_STRONG
from .lexicon import DOMAIN_CATEGORIES, LEXICON
from .normalize import is_number, levenshtein, light_key, token_key, tokenize
from .stemmer import stem_candidates


@dataclass
class Entity:
    category: str
    canonical: str
    sql: str | None
    text: str            # surface text as the user typed it
    start: int           # token index (inclusive)
    end: int             # token index (exclusive)
    how: str = "exact"   # exact | stem | fuzzy

    def public(self) -> dict:
        return {"category": self.category, "value": self.canonical, "text": self.text, "match": self.how}


# --------------------------------------------------------------------------- #
# Build the lookup index once at import time
# --------------------------------------------------------------------------- #
INDEX: dict[tuple, tuple] = {}          # tuple-of-keys -> (category, canonical, sql)
RAW_INDEX: dict[tuple, tuple] = {}      # forms written "=word" in the lexicon: exact spelling only
COLLISIONS: list[tuple] = []
MAX_LEN = 1

# Short words such as "men" or "hi" share a phonetic key with common Hindi function words
# ("में"/"mein", "hai"). A lexicon form written with a leading "=" therefore skips the
# phonetic key and must match the exact spelling.
for _cat, _entries in LEXICON.items():
    for _canon, _spec in _entries.items():
        for _form in _spec["forms"]:
            if _form.startswith("="):
                _raw = tuple(tokenize(_form[1:]))
                if _raw:
                    RAW_INDEX[_raw] = (_cat, _canon, _spec["sql"])
                    MAX_LEN = max(MAX_LEN, len(_raw))
                continue
            _keys = tuple(token_key(t) for t in tokenize(_form))
            if not _keys or not all(_keys):
                continue
            _val = (_cat, _canon, _spec["sql"])
            if _keys in INDEX and INDEX[_keys][:2] != _val[:2]:
                COLLISIONS.append((_form, INDEX[_keys][:2], _val[:2]))
                continue
            INDEX[_keys] = _val
            MAX_LEN = max(MAX_LEN, len(_keys))

# Player names come from the database export, so users can look a player up in any script:
# "रोहित खडसे", "rohit khadse" and "Rohit Khadse" share the same phonetic keys.
PLAYERS_CSV = Path(__file__).resolve().parent.parent / "data" / "players.csv"


def load_players(path: Path = PLAYERS_CSV) -> int:
    if not Path(path).exists():
        return 0
    n = 0
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = (row.get("name") or "").strip()
            keys = tuple(token_key(t) for t in tokenize(name))
            if len(keys) >= 2 and all(keys) and keys not in INDEX and keys not in RAW_INDEX:
                INDEX[keys] = ("player", name, "name ILIKE '%" + name.replace("'", "''") + "%'")
                n += 1
                globals()["MAX_LEN"] = max(MAX_LEN, len(keys))
    return n


N_PLAYERS = load_players()

# single-word keys long enough to be safely fuzzy-matched - cricket vocabulary only. Fuzzy matching
# the out-of-scope / external / greeting lists made "better" look like "weather" and "france" like "finance".
_FUZZY = {k[0]: v for k, v in INDEX.items()
          if len(k) == 1 and len(k[0]) >= 5 and not k[0].isdigit()
          and v[0] in DOMAIN_CATEGORIES and v[0] != "player"}

# never fuzzy-match ordinary function words
_NO_FUZZY = set(_EN_STRONG_SET)
_NO_FUZZY |= {light_key(w) for w in _HI_LAT_STRONG + _MR_LAT_STRONG}
_NO_FUZZY_KEYS = {token_key(w) for w in _NO_FUZZY}


def _fuzzy_lookup(key: str):
    """Return the unique lexicon entry within edit distance 1 (2 for long words)."""
    if len(key) < 5 or key in _NO_FUZZY_KEYS:
        return None
    limit = 2 if len(key) >= 9 else 1
    best, best_d, tie = None, limit + 1, False
    for cand, val in _FUZZY.items():
        d = levenshtein(key, cand, limit)
        if d < best_d:
            best, best_d, tie = val, d, False
        elif d == best_d and best is not None and val[:2] != best[:2]:
            tie = True
    return best if best is not None and not tie and best_d <= limit else None


def extract_entities(tokens: list[str]) -> list[Entity]:
    keys = [token_key(t) for t in tokens]
    entities: list[Entity] = []
    i, n = 0, len(tokens)
    while i < n:
        matched = False
        for length in range(min(MAX_LEN, n - i), 0, -1):          # longest match first
            val = RAW_INDEX.get(tuple(tokens[i:i + length])) or INDEX.get(tuple(keys[i:i + length]))
            if val:
                entities.append(Entity(val[0], val[1], val[2], " ".join(tokens[i:i + length]), i, i + length))
                i += length
                matched = True
                break
        if matched:
            continue

        tok = tokens[i]
        if not is_number(tok):
            # back-off 1: strip a Hindi/Marathi suffix, then retry
            for cand in stem_candidates(tok)[1:]:
                val = INDEX.get((token_key(cand),)) or RAW_INDEX.get((cand,))
                if val:
                    entities.append(Entity(val[0], val[1], val[2], tok, i, i + 1, "stem"))
                    matched = True
                    break
            # back-off 2: tolerate a spelling mistake
            if not matched and len(tok) >= 5:
                val = _fuzzy_lookup(keys[i])
                if val:
                    entities.append(Entity(val[0], val[1], val[2], tok, i, i + 1, "fuzzy"))
                    matched = True
        i += 1
    return entities


# --------------------------------------------------------------------------- #
# Numbers: thresholds ("economy under 7") and limits ("top 10")
# --------------------------------------------------------------------------- #
def resolve_numbers(tokens: list[str], entities: list[Entity]):
    """Returns (limit, thresholds). thresholds = [{'metric','op','value'}]."""
    used = {i for e in entities for i in range(e.start, e.end)}
    metrics = [e for e in entities if e.category == "metric"]
    consumed: set[int] = set()
    thresholds: list[dict] = []
    cmp_used: set[int] = set()

    for c in [e for e in entities if e.category == "cmp"]:
        op = "<" if c.canonical.startswith("lt") else ">"
        idx = None
        if c.canonical.endswith("_pre"):                # "under 7"
            for j in range(c.end, min(c.end + 2, len(tokens))):
                if is_number(tokens[j]) and j not in used and j not in consumed:
                    idx = j
                    break
        else:                                           # "7 se kam", "7 pexa kami"
            for j in range(c.start - 1, max(c.start - 3, -1), -1):
                if is_number(tokens[j]) and j not in used and j not in consumed:
                    idx = j
                    break
        if idx is None:
            continue
        consumed.add(idx)
        cmp_used.add(id(c))
        metric = None
        if metrics:
            m = min(metrics, key=lambda e: (min(abs(e.start - idx), abs(e.end - 1 - idx)), e.start > idx))
            metric = m.canonical
        thresholds.append({"metric": metric, "op": op, "value": float(tokens[idx]) if "." in tokens[idx] else int(tokens[idx])})

    # a comparison word with no number next to it (e.g. cricket "over") is not a comparison
    entities[:] = [e for e in entities if e.category != "cmp" or id(e) in cmp_used]

    limit = None
    if any(e.category == "direction" for e in entities):
        for j, tok in enumerate(tokens):
            if is_number(tok) and j not in used and j not in consumed and "." not in tok and 0 < int(tok) <= 100:
                limit = int(tok)
                break
    return limit, thresholds
