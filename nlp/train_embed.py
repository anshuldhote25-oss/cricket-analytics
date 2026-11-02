"""
Train the intent head on top of a pretrained multilingual encoder (MuRIL by default).

    pip install torch transformers
    python -m nlp.train_embed                       # google/muril-base-cased
    NLP_EMBED_MODEL=sentence-transformers/LaBSE python -m nlp.train_embed

The encoder is frozen; only the small softmax-regression head is learned. Saves nlp/models/intent_embed.json.
"""
import csv
import sys
from collections import Counter
from pathlib import Path

from .embed_intent import EMBED_PATH, INSTALL_HINT, EmbeddingIntent, TransformerEmbedder, deps_available, model_name

TRAIN = Path(__file__).parent / "data" / "intent_train.csv"


def main() -> None:
    if not deps_available():
        sys.exit(INSTALL_HINT)
    if not TRAIN.exists():
        sys.exit("Training CSV missing - run  python -m nlp.train  first")
    with open(TRAIN, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    texts, labels = [r["text"] for r in rows], [r["intent"] for r in rows]
    print(f"encoder : {model_name()}  (pretrained, frozen)")
    print(f"training: {len(rows)} questions, {len(set(labels))} intents  {dict(Counter(labels))}")
    clf = EmbeddingIntent(TransformerEmbedder()).fit(texts, labels)
    clf.save(EMBED_PATH)
    train_acc = sum(p[0] == y for p, y in zip(clf.predict_many(texts), labels)) / len(labels)
    print(f"train accuracy {train_acc:.1%}")
    print(f"saved {EMBED_PATH}")
    print("next: python -m nlp.evaluate")


if __name__ == "__main__":
    main()
