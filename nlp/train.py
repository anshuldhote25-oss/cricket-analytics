"""Train the Naive Bayes intent classifier.   Usage:  python -m nlp.train"""
from collections import Counter
from pathlib import Path

from .dataset import generate, write_csv
from .entities import extract_entities, resolve_numbers
from .intent import MODEL_PATH, NaiveBayesIntent, featurize
from .normalize import tokenize


def features_for(text: str) -> list[str]:
    tokens = tokenize(text)
    ents = extract_entities(tokens)
    resolve_numbers(tokens, ents)
    return featurize(tokens, ents)


def main() -> None:
    rows = generate()
    write_csv(Path(__file__).parent / "data" / "intent_train.csv", rows)
    X = [features_for(t) for t, _, _ in rows]
    y = [i for _, i, _ in rows]
    model = NaiveBayesIntent(alpha=0.5).fit(X, y)
    model.save(MODEL_PATH)
    print(f"trained on {len(rows)} generated questions")
    for k, v in sorted(Counter(y).items()):
        print(f"  {k:14} {v}")
    print(f"model saved to {MODEL_PATH}")
    print("next: python -m nlp.evaluate")


if __name__ == "__main__":
    main()
