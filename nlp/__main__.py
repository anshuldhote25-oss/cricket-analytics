"""Demo:  python -m nlp "powerplay madhe sarvottam economy asleale golandaj"   (or run with no args for a prompt)"""
import json
import sys

from . import analyze


def show(q: str) -> None:
    f = analyze(q)
    print(f"\n  question      : {q}")
    print(f"  normalized    : {f.normalized}")
    print(f"  tokens        : {f.tokens}")
    print(f"  language      : {f.language_label} [{f.language}]  confidence={f.lang.confidence}")
    print(f"  intent        : {f.intent}  ({f.intent_source}, {f.intent_confidence:.2f})")
    print(f"  entities      : " + ", ".join(f"{e.category}={e.canonical}<{e.text}|{e.how}>" for e in f.entities))
    print(f"  limit/thresh. : {f.limit} / {f.thresholds}")
    print(f"  interpreted as: {f.interpreted_as or '-'}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        show(" ".join(sys.argv[1:]))
    else:
        while True:
            try:
                q = input("\nquestion> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if q:
                show(q)
