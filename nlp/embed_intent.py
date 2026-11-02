"""
nlp/embed_intent.py - intent classification with a PRETRAINED multilingual transformer encoder.

    question text
      -> MuRIL (google/muril-base-cased)      pretrained BERT for 17 Indian languages, incl. Roman-script text
      -> mean-pooled 768-d sentence vector    (encoder is FROZEN - we do not fine-tune it)
      -> softmax / multinomial logistic regression head   (the only part we train, on nlp/data/intent_train.csv)
      -> intent + probability

Honest summary for the viva: the encoder is pretrained by Google; the small classifier head on top is
trained by us. Compare with nlp/intent.py, where Naive Bayes is trained from scratch on hand-made features.

Needs (optional - the rest of the project works without them):
    pip install torch transformers
Choose another encoder with the NLP_EMBED_MODEL environment variable, e.g.
    sentence-transformers/LaBSE   |   sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

Train / evaluate:
    python -m nlp.train_embed
    python -m nlp.evaluate
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .normalize import normalize_text

DEFAULT_MODEL = "google/muril-base-cased"
MODEL_DIR = Path(__file__).parent / "models"
EMBED_PATH = MODEL_DIR / "intent_embed.json"

INSTALL_HINT = ("The embedding classifier needs PyTorch and Hugging Face transformers:\n"
                "    pip install torch transformers\n"
                "(the first run downloads the pretrained model, about 1 GB for MuRIL)")


def model_name() -> str:
    return os.environ.get("NLP_EMBED_MODEL", DEFAULT_MODEL)


def deps_available() -> bool:
    try:
        import numpy, torch, transformers  # noqa: F401
        return True
    except ImportError:
        return False


# --------------------------------------------------------------------------- encoder
class TransformerEmbedder:
    """Sentence embeddings = attention-masked mean of the last hidden states, then L2-normalised.

    Vectors are cached on disk (one .npz per model) so re-running training / evaluation is instant.
    Any object with  .name  and  .encode(list[str]) -> ndarray  can replace this class (used in tests).
    """

    def __init__(self, name: str | None = None, max_length: int = 64, batch_size: int = 32, cache: bool = True):
        self.name = name or model_name()
        self.max_length, self.batch_size = max_length, batch_size
        self._tok = self._model = None
        slug = re.sub(r"[^A-Za-z0-9]+", "_", self.name).strip("_")
        self._cache_path = MODEL_DIR / f"embed_cache_{slug}.npz" if cache else None
        self._cache: dict[str, "object"] | None = None

    # -- model loading ---------------------------------------------------------------
    def _load(self):
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except ImportError as e:                                   # pragma: no cover
            raise RuntimeError(INSTALL_HINT) from e
        print(f"[embed] loading {self.name} (first run downloads it) ...")
        self._tok = AutoTokenizer.from_pretrained(self.name)
        self._model = AutoModel.from_pretrained(self.name).eval()
        self._torch = torch

    def _embed_batch(self, texts: list[str]):
        import numpy as np
        torch = self._torch
        enc = self._tok(texts, padding=True, truncation=True, max_length=self.max_length, return_tensors="pt")
        with torch.no_grad():
            hidden = self._model(**enc).last_hidden_state              # (batch, tokens, 768)
        mask = enc["attention_mask"].unsqueeze(-1).to(hidden.dtype)    # ignore padding
        pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)  # mean pooling
        pooled = torch.nn.functional.normalize(pooled, dim=1)          # unit length
        return pooled.cpu().numpy().astype(np.float32)

    # -- cache -------------------------------------------------------------------------
    def _load_cache(self):
        import numpy as np
        if self._cache is not None:
            return
        self._cache = {}
        if self._cache_path and self._cache_path.exists():
            try:
                d = np.load(self._cache_path, allow_pickle=False)
                self._cache = dict(zip(d["texts"].tolist(), d["vecs"]))
            except Exception:                                          # corrupt cache -> rebuild
                self._cache = {}

    def _save_cache(self):
        import numpy as np
        if not self._cache_path or not self._cache:
            return
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        texts = list(self._cache)
        np.savez(self._cache_path, texts=np.array(texts, dtype=str), vecs=np.stack([self._cache[t] for t in texts]))

    # -- public --------------------------------------------------------------------------
    def encode(self, texts: list[str]):
        import numpy as np
        self._load_cache()
        todo = [t for t in dict.fromkeys(texts) if t not in self._cache]
        if todo:
            self._load()
            for i in range(0, len(todo), self.batch_size):
                chunk = todo[i:i + self.batch_size]
                for t, v in zip(chunk, self._embed_batch(chunk)):
                    self._cache[t] = v
                print(f"[embed] {min(i + self.batch_size, len(todo))}/{len(todo)}", end="\r", flush=True)
            if len(todo) >= self.batch_size:
                print()
            self._save_cache()
        return np.stack([self._cache[t] for t in texts]) if texts else np.zeros((0, 0), dtype=np.float32)


# --------------------------------------------------------------------------- classifier head
def _softmax(z):
    import numpy as np
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


class EmbeddingIntent:
    """Multinomial logistic (softmax) regression on top of frozen sentence embeddings.

    Trained with full-batch Adam on the cross-entropy loss + L2 penalty. Features are standardised
    with the training mean / std. Weights are stored as plain JSON (no pickle).
    """

    def __init__(self, embedder=None, l2: float = 1e-3, epochs: int = 400, lr: float = 0.05):
        self.embedder = embedder
        self.l2, self.epochs, self.lr = l2, epochs, lr
        self.classes: list[str] = []
        self.W = self.b = self.mu = self.sd = None
        self.encoder_name = getattr(embedder, "name", None)

    # -- training -------------------------------------------------------------------------
    def fit_vectors(self, X, y: list[str]) -> "EmbeddingIntent":
        import numpy as np
        X = np.asarray(X, dtype=np.float64)
        self.classes = sorted(set(y))
        idx = {c: i for i, c in enumerate(self.classes)}
        Y = np.zeros((len(y), len(self.classes)))
        Y[np.arange(len(y)), [idx[c] for c in y]] = 1.0
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-8
        Z = (X - self.mu) / self.sd
        n, d = Z.shape
        W, b = np.zeros((d, len(self.classes))), np.zeros(len(self.classes))
        mW, vW, mb, vb = np.zeros_like(W), np.zeros_like(W), np.zeros_like(b), np.zeros_like(b)
        b1, b2, eps = 0.9, 0.999, 1e-8
        for t in range(1, self.epochs + 1):
            P = _softmax(Z @ W + b)
            gW = Z.T @ (P - Y) / n + self.l2 * W
            gb = (P - Y).mean(0)
            mW = b1 * mW + (1 - b1) * gW; vW = b2 * vW + (1 - b2) * gW ** 2
            mb = b1 * mb + (1 - b1) * gb; vb = b2 * vb + (1 - b2) * gb ** 2
            W -= self.lr * (mW / (1 - b1 ** t)) / (np.sqrt(vW / (1 - b2 ** t)) + eps)
            b -= self.lr * (mb / (1 - b1 ** t)) / (np.sqrt(vb / (1 - b2 ** t)) + eps)
        self.W, self.b = W, b
        return self

    def fit(self, texts: list[str], labels: list[str]) -> "EmbeddingIntent":
        return self.fit_vectors(self.embedder.encode([normalize_text(t) for t in texts]), labels)

    # -- inference ------------------------------------------------------------------------
    def _proba_matrix(self, X):
        import numpy as np
        return _softmax(((np.asarray(X, dtype=np.float64) - self.mu) / self.sd) @ self.W + self.b)

    def _need_embedder(self):
        if self.embedder is None:
            self.embedder = TransformerEmbedder(self.encoder_name)
        return self.embedder

    def predict_many(self, texts: list[str]) -> list[tuple[str, float]]:
        P = self._proba_matrix(self._need_embedder().encode([normalize_text(t) for t in texts]))
        return [(self.classes[int(r.argmax())], float(r.max())) for r in P]

    def predict_proba(self, text: str) -> dict[str, float]:
        P = self._proba_matrix(self._need_embedder().encode([normalize_text(text)]))[0]
        return {c: float(p) for c, p in zip(self.classes, P)}

    # -- persistence ------------------------------------------------------------------------
    def save(self, path: Path = EMBED_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"encoder": self.encoder_name, "classes": self.classes, "l2": self.l2,
                "W": self.W.tolist(), "b": self.b.tolist(), "mu": self.mu.tolist(), "sd": self.sd.tolist()}
        path.write_text(json.dumps(data), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = EMBED_PATH, embedder=None) -> "EmbeddingIntent | None":
        import numpy as np
        if not Path(path).exists():
            return None
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        m = cls(embedder)
        m.encoder_name, m.classes, m.l2 = d["encoder"], d["classes"], d["l2"]
        m.W, m.b, m.mu, m.sd = (np.array(d[k]) for k in ("W", "b", "mu", "sd"))
        return m
