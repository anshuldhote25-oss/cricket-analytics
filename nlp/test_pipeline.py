"""Regression tests for the NLP pipeline.   Run:  python -m unittest nlp.test_pipeline -v"""
import unittest

from nlp import analyze
from nlp.normalize import levenshtein, normalize_text, token_key, tokenize


def slots(frame):
    return {(e.category, e.canonical) for e in frame.entities}


class NormalizeTests(unittest.TestCase):
    def test_devanagari_digits_and_nukta(self):
        self.assertEqual(tokenize("टॉप १०"), ["टॉप", "10"])
        self.assertEqual(token_key("बल्लेबाज़"), token_key("बल्लेबाज"))

    def test_same_word_three_spellings_two_scripts(self):
        keys = {token_key(w) for w in ("gendbaaz", "gendbaj", "gaindbaaz", "गेंदबाज़")}
        self.assertEqual(len(keys), 1)

    def test_symbols_become_words(self):
        self.assertIn("under", tokenize("economy < 7"))

    def test_levenshtein(self):
        self.assertEqual(levenshtein("powerplay", "poweplay"), 1)


class LanguageTests(unittest.TestCase):
    def test_codes(self):
        cases = {
            "Top 10 T20 batters by strike rate": "en",
            "T20 में स्ट्राइक रेट के हिसाब से टॉप 10 बल्लेबाज़": "hi",
            "T20 मध्ये स्ट्राइक रेटनुसार टॉप 10 फलंदाज": "mr",
            "powerplay mein sabse kam economy wale gendbaaz": "hi-Latn",
            "powerplay madhe sarvottam economy asleale golandaj dakhva": "mr-Latn",
        }
        for text, code in cases.items():
            self.assertEqual(analyze(text).language, code, text)


class EntityTests(unittest.TestCase):
    def test_roman_marathi_with_suffix(self):
        f = analyze("nagpurchya golandajanmadhe sarvottam kon")
        self.assertIn(("district", "Nagpur"), slots(f))
        self.assertIn(("role", "bowler"), slots(f))

    def test_threshold_prefix_and_postfix(self):
        for q in ("economy under 7", "economy 7 se kam", "7 पेक्षा कमी इकॉनॉमी"):
            self.assertEqual(analyze(q).thresholds, [{"metric": "economy_rate", "op": "<", "value": 7}], q)

    def test_limit(self):
        self.assertEqual(analyze("top 10 batters").limit, 10)
        self.assertEqual(analyze("सर्वाधिक धावा करणारे टॉप १० फलंदाज").limit, 10)

    def test_player_name_in_devanagari(self):
        f = analyze("रोहित खडसे का स्ट्राइक रेट")
        self.assertIn(("player", "Rohit Khadse"), slots(f))

    def test_function_words_are_not_cricket_terms(self):
        self.assertNotIn(("gender", "male"), slots(analyze("powerplay mein sabse kam economy")))  # mein != men
        self.assertNotIn(("phase", "powerplay"), slots(analyze("namaste aap kaise ho")))          # aap != pp
        self.assertNotIn(("oos", "weather"), slots(analyze("Who is better than him?")))            # better != weather

    def test_spelling_mistake(self):
        self.assertIn(("phase", "powerplay"), slots(analyze("poweplay bowlers economy")))

    def test_over_is_not_a_comparison_without_a_number(self):
        f = analyze("best bowlers in death over")
        self.assertEqual(f.thresholds, [])
        self.assertIn(("phase", "death"), slots(f))


class IntentTests(unittest.TestCase):
    def test_blocked_in_every_style(self):
        for q in ("what is the weather today", "aaj mausam kaisa hai", "आज मौसम कैसा है",
                  "aaj havaman kase aahe", "आज हवामान कसे आहे"):
            self.assertEqual(analyze(q).intent, "out_of_scope", q)
        for q in ("IPL madhe sarvat jast dhava konni kelya", "विराट कोहली का स्ट्राइक रेट"):
            self.assertEqual(analyze(q).intent, "external_data", q)

    def test_cricket_intents(self):
        self.assertEqual(analyze("sabse zyada catch kisne pakde").intent, "fielding")
        self.assertEqual(analyze("sarvat jast wide takanare golandaj").intent, "discipline")
        self.assertEqual(analyze("top 5 all-rounders").intent, "allrounder")

    def test_replies_are_localised(self):
        self.assertIn("Yeh sawal", analyze("aaj mausam kaisa hai").reply())
        self.assertIn("हा प्रश्न", analyze("आज हवामान कसे आहे").reply())



class StubEmbedder:
    """Stand-in for MuRIL so the classifier head can be tested without torch or a download:
    a hashed bag of character 3-grams, L2-normalised. Same interface as TransformerEmbedder."""
    name = "stub-hashed-char-ngrams"

    def encode(self, texts, dim=256):
        import numpy as np
        out = np.zeros((len(texts), dim))
        for i, t in enumerate(texts):
            t = f" {t.lower()} "
            for j in range(len(t) - 2):
                out[i, sum(ord(c) * (k + 7) for k, c in enumerate(t[j:j + 3])) % dim] += 1
        return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-9)


try:
    import numpy as _np  # noqa: F401
except ImportError:                                  # pragma: no cover
    _np = None


@unittest.skipIf(_np is None, "numpy not installed")
class EmbeddingHeadTests(unittest.TestCase):
    """Logic of the pretrained-encoder classifier (head, persistence, ensemble) with a stub encoder."""

    @classmethod
    def setUpClass(cls):
        import csv
        from pathlib import Path
        from nlp.embed_intent import EmbeddingIntent
        path = Path(__file__).parent / "data" / "intent_train.csv"
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        cls.rows = rows
        cls.clf = EmbeddingIntent(StubEmbedder(), epochs=150).fit([r["text"] for r in rows], [r["intent"] for r in rows])

    def test_learns_the_training_set(self):
        preds = self.clf.predict_many([r["text"] for r in self.rows])
        acc = sum(p == r["intent"] for (p, _), r in zip(preds, self.rows)) / len(self.rows)
        self.assertGreater(acc, 0.9)

    def test_probabilities_sum_to_one(self):
        probs = self.clf.predict_proba("top 10 T20 batters by strike rate")
        self.assertAlmostEqual(sum(probs.values()), 1.0, places=6)
        self.assertEqual(set(probs), set(self.clf.classes))

    def test_save_and_load_roundtrip(self):
        import tempfile
        from pathlib import Path
        from nlp.embed_intent import EmbeddingIntent
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "m.json"
            self.clf.save(path)
            again = EmbeddingIntent.load(path, embedder=StubEmbedder())
        q = "powerplay mein sabse kam economy wale gendbaaz"
        self.assertEqual(self.clf.predict_proba(q).keys(), again.predict_proba(q).keys())
        for c, p in self.clf.predict_proba(q).items():
            self.assertAlmostEqual(p, again.predict_proba(q)[c], places=9)

    def test_pipeline_ensemble_uses_encoder_when_given(self):
        # no entities -> falls through to the learned classifiers; source must say the encoder took part
        f = analyze("hello there how is the weather", embed=self.clf)
        self.assertIn(f.intent_source, {"lexicon", "nb+encoder"})
        f = analyze("T20 mein sabse zyada runs kisne banaye", embed=self.clf)
        self.assertEqual(f.intent, "batting")          # rules still decide when entities are clear

if __name__ == "__main__":
    unittest.main()
