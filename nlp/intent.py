"""
nlp/intent.py - intent classification.

Two classifiers are provided so the report can compare them:

  * rule_intent()     - deterministic baseline: looks at which cricket entities were found.
  * NaiveBayesIntent  - multinomial Naive Bayes written from scratch (no scikit-learn),
                        trained on labelled questions in all five input styles.

Features are deliberately script-independent:
    w:<phonetic key>          word identity            (gendbaaz == गेंदबाज़)
    c:<char 3/4-gram of key>  sub-word pieces          (robust to unseen spellings)
    b:<key>_<key>             word bigrams
    e:<category>[=<value>]    entity tags from the gazetteer (doubled weight)

Concepts: text classification, bag-of-features, Naive Bayes, Laplace smoothing,
          character n-grams, precision / recall / F1, confusion matrix.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from .normalize import is_number, token_key

INTENTS = ["batting", "bowling", "fielding", "discipline", "allrounder", "general",
           "greeting", "out_of_scope", "external_data"]
SUB_INTENTS = {"batting", "bowling", "fielding", "discipline", "allrounder", "general"}

MODEL_PATH = Path(__file__).parent / "models" / "intent_nb.json"


# --------------------------------------------------------------------------- #
# Baseline: rules over entities
# --------------------------------------------------------------------------- #
def rule_intent(entities) -> str:
    cats = {}
    for e in entities:
        cats.setdefault(e.category, set()).add(e.canonical)
    metrics, roles = cats.get("metric", set()), cats.get("role", set())
    if cats.get("external"):
        return "external_data"
    if cats.get("oos"):
        return "out_of_scope"
    if metrics & {"wides", "no_balls", "extras", "indiscipline"}:
        return "discipline"
    if metrics & {"catches", "stumpings", "run_outs"} or "fielder" in roles:
        return "fielding"
    if "all-rounder" in roles:
        return "allrounder"
    if "bowler" in roles or metrics & {"economy_rate", "wickets", "dot_balls", "average"} or cats.get("bowler_type"):
        return "bowling"
    if "batter" in roles or metrics & {"strike_rate", "runs", "boundary_pct", "fours", "sixes"} or cats.get("position"):
        return "batting"
    if cats.get("group") or cats.get("player"):
        return "general"
    if cats.get("greeting"):
        return "greeting"
    return "unknown"


# --------------------------------------------------------------------------- #
# Feature extraction
# --------------------------------------------------------------------------- #
def featurize(tokens: list[str], entities) -> list[str]:
    keys = [token_key(t) for t in tokens]
    feats: list[str] = []
    for k in keys:
        feats.append("w:" + k)
        if not is_number(k) and len(k) >= 3:
            padded = f"^{k}$"
            for n in (3, 4):
                feats += ["c:" + padded[i:i + n] for i in range(len(padded) - n + 1)]
    feats += [f"b:{a}_{b}" for a, b in zip(keys, keys[1:])]
    for e in entities:
        feats += [f"e:{e.category}", f"e:{e.category}={e.canonical}"] * 2
    feats.append(f"len:{min(len(tokens), 8)}")
    return feats


# --------------------------------------------------------------------------- #
# Multinomial Naive Bayes
# --------------------------------------------------------------------------- #
class NaiveBayesIntent:
    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha
        self.classes: list[str] = []
        self.log_prior: dict[str, float] = {}
        self.log_like: dict[str, dict[str, float]] = {}
        self.log_unseen: dict[str, float] = {}

    def fit(self, X: list[list[str]], y: list[str]) -> "NaiveBayesIntent":
        self.classes = sorted(set(y))
        class_count = Counter(y)
        feat_count: dict[str, Counter] = defaultdict(Counter)
        vocab = set()
        for feats, label in zip(X, y):
            feat_count[label].update(feats)
            vocab.update(feats)
        V = len(vocab)
        for c in self.classes:
            self.log_prior[c] = math.log(class_count[c] / len(y))
            total = sum(feat_count[c].values())
            denom = total + self.alpha * (V + 1)                 # Laplace / Lidstone smoothing
            self.log_like[c] = {f: math.log((n + self.alpha) / denom) for f, n in feat_count[c].items()}
            self.log_unseen[c] = math.log(self.alpha / denom)
        return self

    def predict_proba(self, feats: list[str]) -> dict[str, float]:
        logp = {}
        for c in self.classes:
            ll, unseen = self.log_like[c], self.log_unseen[c]
            logp[c] = self.log_prior[c] + sum(ll.get(f, unseen) for f in feats)
        m = max(logp.values())
        exps = {c: math.exp(v - m) for c, v in logp.items()}
        z = sum(exps.values())
        return {c: v / z for c, v in exps.items()}

    def predict(self, feats: list[str]) -> tuple[str, float]:
        probs = self.predict_proba(feats)
        label = max(probs, key=probs.get)
        return label, probs[label]

    # -- persistence (plain JSON, no pickle) ---------------------------------
    def save(self, path: Path = MODEL_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"alpha": self.alpha, "classes": self.classes, "log_prior": self.log_prior,
                "log_like": self.log_like, "log_unseen": self.log_unseen}
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = MODEL_PATH) -> "NaiveBayesIntent | None":
        if not Path(path).exists():
            return None
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        m = cls(d["alpha"])
        m.classes, m.log_prior, m.log_like, m.log_unseen = d["classes"], d["log_prior"], d["log_like"], d["log_unseen"]
        return m
