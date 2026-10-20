"""
nlp/evaluate.py - evaluate every NLP component on the hand-written test set.

    python -m nlp.evaluate            # summary tables
    python -m nlp.evaluate --errors   # also list every wrong prediction

Reports: language-ID accuracy, intent accuracy / macro-F1 (rule baseline vs Naive Bayes vs
final pipeline), per-class precision/recall/F1, confusion matrix, and entity (slot) P/R/F1
per input style.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

from .entities import extract_entities, resolve_numbers
from .intent import INTENTS, NaiveBayesIntent, featurize, rule_intent
from .normalize import tokenize
from .dataset import generate
from .pipeline import analyze

TEST_PATH = Path(__file__).parent / "data" / "intent_test.csv"
SLOT_CATS = {"format", "phase", "gender", "age_group", "bowler_type", "role", "metric",
             "district", "tournament", "position", "group"}


def load_test():
    with open(TEST_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def frame_slots(frame) -> set:
    slots = {f"{e.category}={e.canonical}" for e in frame.entities if e.category in SLOT_CATS}
    if frame.limit:
        slots.add(f"limit={frame.limit}")
    slots |= {f"thr={t['metric']}{t['op']}{t['value']}" for t in frame.thresholds}
    return slots


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def intent_report(name, gold, pred):
    labels = sorted(set(gold) | set(pred) - {"unknown"})
    acc = sum(g == p for g, p in zip(gold, pred)) / len(gold)
    rows, f1s = [], []
    for c in labels:
        tp = sum(g == c and p == c for g, p in zip(gold, pred))
        fp = sum(g != c and p == c for g, p in zip(gold, pred))
        fn = sum(g == c and p != c for g, p in zip(gold, pred))
        p_, r_, f_ = prf(tp, fp, fn)
        f1s.append(f_)
        rows.append((c, p_, r_, f_, sum(g == c for g in gold)))
    print(f"\n=== Intent: {name}   accuracy={acc:.1%}   macro-F1={sum(f1s)/len(f1s):.3f}")
    return acc, sum(f1s) / len(f1s), rows, labels


def main(show_errors: bool = False) -> None:
    data = load_test()
    model = NaiveBayesIntent.load()
    if model is None:
        print("No trained model found - run:  python -m nlp.train")
    n = len(data)
    print(f"{n} hand-written test questions  ({dict(Counter(r['lang'] for r in data))})")

    # ablation: the same Naive Bayes, but WITHOUT the gazetteer entity features (words + char n-grams only)
    gen = generate()
    text_nb = NaiveBayesIntent(alpha=0.5).fit([featurize(tokenize(t), []) for t, _, _ in gen], [i for _, i, _ in gen])
    gold_lang, pred_lang = [], []
    gold_int, rule_pred, nb_pred, final_pred, text_pred = [], [], [], [], []
    slot_stats = defaultdict(lambda: [0, 0, 0])      # lang -> tp, fp, fn
    errors = []

    for r in data:
        frame = analyze(r["text"], model=model)
        gold_lang.append(r["lang"]); pred_lang.append(frame.language)
        gold_int.append(r["intent"])
        tokens = tokenize(r["text"]); ents = extract_entities(tokens); resolve_numbers(tokens, ents)
        rule_pred.append(rule_intent(ents))
        nb_pred.append(model.predict(featurize(tokens, ents))[0] if model else "unknown")
        final_pred.append(frame.intent)
        text_pred.append(text_nb.predict(featurize(tokens, []))[0])

        gold = {s for s in r["slots"].split("|") if s}
        pred = frame_slots(frame)
        st = slot_stats[r["lang"]]
        st[0] += len(gold & pred); st[1] += len(pred - gold); st[2] += len(gold - pred)
        if frame.language != r["lang"]:
            errors.append(("language", r["text"], r["lang"], frame.language))
        if frame.intent != r["intent"]:
            errors.append(("intent", r["text"], r["intent"], f"{frame.intent} ({frame.intent_source})"))
        if gold != pred:
            errors.append(("slots", r["text"], f"missing={sorted(gold - pred)}", f"extra={sorted(pred - gold)}"))

    # ---- language ID
    acc = sum(g == p for g, p in zip(gold_lang, pred_lang)) / n
    print(f"\n=== Language identification   accuracy={acc:.1%}")
    langs = ["en", "hi", "mr", "hi-Latn", "mr-Latn"]
    cm = Counter(zip(gold_lang, pred_lang))
    print("gold \\ pred  " + "".join(f"{l:>9}" for l in langs))
    for g in langs:
        print(f"{g:12} " + "".join(f"{cm[(g, p)]:>9}" for p in langs))

    # ---- intent
    for name, pred in (("rule baseline (entities only)", rule_pred),
                       ("Naive Bayes, text features only (no gazetteer)", text_pred),
                       ("Naive Bayes, text + entity features", nb_pred),
                       ("final pipeline (lexicon + NB + rules)", final_pred)):
        a, mf, rows, labels = intent_report(name, gold_int, pred)
        if name.startswith("final"):
            print(f"{'class':14}{'precision':>10}{'recall':>8}{'F1':>7}{'support':>9}")
            for c, p_, r_, f_, s in rows:
                print(f"{c:14}{p_:>10.2f}{r_:>8.2f}{f_:>7.2f}{s:>9}")
            labs = INTENTS
            cmx = Counter(zip(gold_int, pred))
            print("\nconfusion matrix (rows = gold, cols = predicted; 'unk' = unknown)")
            short = {l: l[:5] for l in labs}
            print(f"{'':14}" + "".join(f"{short[l]:>6}" for l in labs) + f"{'unk':>6}")
            for g in labs:
                print(f"{g:14}" + "".join(f"{cmx[(g, p)]:>6}" for p in labs) + f"{cmx[(g, 'unknown')]:>6}")

    # ---- slots
    print("\n=== Entity / slot extraction (exact-match sets)")
    print(f"{'input style':12}{'precision':>10}{'recall':>8}{'F1':>7}")
    tot = [0, 0, 0]
    for l in langs:
        tp, fp, fn = slot_stats[l]
        tot = [tot[0] + tp, tot[1] + fp, tot[2] + fn]
        p_, r_, f_ = prf(tp, fp, fn)
        print(f"{l:12}{p_:>10.2f}{r_:>8.2f}{f_:>7.2f}")
    p_, r_, f_ = prf(*tot)
    print(f"{'ALL':12}{p_:>10.2f}{r_:>8.2f}{f_:>7.2f}")

    if show_errors:
        print(f"\n=== {len(errors)} error lines")
        for kind, text, a, b in errors:
            print(f"[{kind:8}] {text}\n            expected {a}\n            got      {b}")


if __name__ == "__main__":
    main("--errors" in sys.argv)
