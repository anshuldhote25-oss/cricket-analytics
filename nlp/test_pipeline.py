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


if __name__ == "__main__":
    unittest.main()
