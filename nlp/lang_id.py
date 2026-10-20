"""
nlp/lang_id.py - language + script identification for English / Hindi / Marathi,
in Devanagari *or* Roman letters ("Hinglish", "Marathi typed in English").

Method (a small hand-built linear classifier):
  1. Script detection from Unicode ranges (Devanagari vs Latin).
  2. Each token is checked against marker-word lists. Function words are the best
     signal because they are language specific and very frequent:
        Hindi   : है, में, सबसे, कितने, किसने ...   hai, mein, sabse, kitne, kisne ...
        Marathi : आहे, मध्ये, सर्वात, किती, कोणी ...  aahe, madhe, sarvat, kiti, koni ...
        English : the, of, by, who, which ...
  3. Score = weighted marker hits; the highest score wins. Ties -> Hindi (more common).
  4. Output code: en | hi | mr | hi-Latn | mr-Latn  (Latn = typed in Roman letters).

Concepts: language identification, function words / stop-words, script detection.
"""
from __future__ import annotations

from dataclasses import dataclass

from .normalize import has_devanagari, light_key, tokenize

LANG_LABELS = {
    "en": "English", "hi": "Hindi", "mr": "Marathi",
    "hi-Latn": "Hindi (Roman letters)", "mr-Latn": "Marathi (Roman letters)",
}

# Used to tell the LLM which language/script to answer in.
LLM_LANGUAGE = {
    "en": "English",
    "hi": "Hindi, written in Devanagari script",
    "mr": "Marathi, written in Devanagari script",
    "hi-Latn": "Hinglish - Hindi written in Roman/English letters, like the user's own message",
    "mr-Latn": "Marathi written in Roman/English letters, like the user's own message",
}

# strong = 2 points, weak = 1 point (weak words are shared with English or the other language)
_HI_DEV_STRONG = "है हैं में सबसे कितने कितनी कितना किसने कौन कौनसा कौनसे वाले वाला वाली दिखाओ दिखाइए बताओ बताइए " \
                 "हिसाब ज्यादा ज़्यादा अच्छे अच्छा अच्छी मुझे क्या कैसे किस लिए लिये बनाए बनाये लिए खिलाड़ी खिलाड़ियों " \
                 "कृपया".split()
_HI_DEV_WEAK = "के का की से को और या नहीं".split()
_MR_DEV_STRONG = "आहे आहेत किती कोणी कोणती कोणता कोणत्या मध्ये सर्वात जास्त कमी पेक्षा दाखवा सांगा सांग मला तुम्ही " \
                 "नुसार मधील मधले केल्या केले घेतले घेणारे असलेले असणारे खेळाडू खेळाडूंची कसे कसा कुठे आणि किंवा चे ची चा च्या".split()
_MR_DEV_WEAK = "ने ला साठी".split()

_HI_LAT_STRONG = "hai hain hay kitne kitni kitna sabse kisne kaun kaunsa kaunse wale wala wali vale dikhao dikhaiye " \
                 "batao bataiye hisab hisaab zyada jyada jada mein kya kaise kis liye liya diye banaye banaya " \
                 "acche achhe accha acchi achi behtar khiladi khiladiyon mujhe kripya".split()
_HI_LAT_WEAK = "ke ka ki se ko aur ya nahi me".split()
_MR_LAT_STRONG = "aahe ahe aahet ahet kiti koni konni konti konta konatya kontya madhe mdhe madhye madhil madhale mdhil sarvat sarvadhik " \
                 "jast jasta kami pexa peksha dakhva dakhava sanga sang mala tumhi nusar kelya kele kelela ghetle ghenare " \
                 "takanare asleale asnare kasa kase kuthe ani kinva khelaadu khelaadunchi changle changla falandaj " \
                 "golandaj chya che chi cha".split()
_MR_LAT_WEAK = "la sathi".split()

_EN_STRONG = "the of in by who which what with and for show me list give are is has have had than from per this how " \
             "many took scored taken did does do where when between among across all any please tell".split()
_EN_WEAK = "top best highest lowest most under above".split()


def _dev_set(words) -> set:
    return set(words)


def _lat_set(words) -> set:
    return {light_key(w) for w in words}


_SETS = {
    "hi": {"dev": (_dev_set(_HI_DEV_STRONG), _dev_set(_HI_DEV_WEAK)),
           "lat": (_lat_set(_HI_LAT_STRONG), _lat_set(_HI_LAT_WEAK))},
    "mr": {"dev": (_dev_set(_MR_DEV_STRONG), _dev_set(_MR_DEV_WEAK)),
           "lat": (_lat_set(_MR_LAT_STRONG), _lat_set(_MR_LAT_WEAK))},
}
_EN_STRONG_SET, _EN_WEAK_SET = set(_EN_STRONG), set(_EN_WEAK)

# Words that are in BOTH Hindi and Marathi lists would confuse the vote; drop them.
for _kind in ("dev", "lat"):
    _both = _SETS["hi"][_kind][0] & _SETS["mr"][_kind][0]
    _SETS["hi"][_kind][0].difference_update(_both)
    _SETS["mr"][_kind][0].difference_update(_both)


# Marathi glues case endings onto nouns; Hindi writes them as separate words.  A long token ending
# in one of these is therefore strong evidence for Marathi.  ("अनुसार"/"anusar" is Hindi - excluded.)
_MR_DEV_SUFFIX = ("ांमध्ये", "च्या", "मध्ये", "ांचे", "ांचा", "ांची", "ाचे", "ाचा", "ाची", "नुसार")
_MR_LAT_SUFFIX = ("anmadhe", "anmdhe", "amadhe", "madhe", "mdhe", "madhye", "nchya", "chya", "nusar")
_NOT_MARATHI = {"अनुसार", "anusar", "anusaar"}


def _marathi_suffix(tok: str, dev: bool) -> bool:
    if tok in _NOT_MARATHI:
        return False
    return any(tok.endswith(s) and len(tok) > len(s) + 1 for s in (_MR_DEV_SUFFIX if dev else _MR_LAT_SUFFIX))


@dataclass
class LangResult:
    code: str            # en | hi | mr | hi-Latn | mr-Latn
    script: str          # Latin | Devanagari
    confidence: float
    scores: dict

    @property
    def label(self) -> str:
        return LANG_LABELS[self.code]

    @property
    def llm_language(self) -> str:
        return LLM_LANGUAGE[self.code]


def detect_language(text: str, tokens: list[str] | None = None) -> LangResult:
    tokens = tokens if tokens is not None else tokenize(text)
    dev_chars = sum(1 for ch in text if "ऀ" <= ch <= "ॿ")
    lat_chars = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    script = "Devanagari" if dev_chars and dev_chars >= 0.3 * (dev_chars + lat_chars) else "Latin"

    scores = {"en": 0.0, "hi": 0.0, "mr": 0.0}
    for tok in tokens:
        if has_devanagari(tok):
            # a Devanagari function word is unambiguous evidence, even inside an English sentence
            for lang in ("hi", "mr"):
                strong, weak = _SETS[lang]["dev"]
                scores[lang] += 3 if tok in strong else 1.5 if tok in weak else 0
            if _marathi_suffix(tok, dev=True):
                scores["mr"] += 3
        elif tok.isalpha():
            key = light_key(tok)
            for lang in ("hi", "mr"):
                strong, weak = _SETS[lang]["lat"]
                scores[lang] += 2 if key in strong else 1 if key in weak else 0
            if _marathi_suffix(tok, dev=False):
                scores["mr"] += 2
            scores["en"] += 2 if tok in _EN_STRONG_SET else 1 if tok in _EN_WEAK_SET else 0

    # Devanagari text can never be English, even when no marker word was found.
    if script == "Devanagari":
        scores["en"] = 0.0
    best = max(scores, key=lambda k: (scores[k], k == "hi"))   # ties -> Hindi, then others
    total = sum(scores.values())

    if total == 0:
        lang, confidence = ("hi", 0.34) if script == "Devanagari" else ("en", 0.5)
    else:
        lang, confidence = best, scores[best] / total
        # Roman text where English is only weakly ahead of a *strong* Indic signal: prefer Indic.
        if lang == "en" and max(scores["hi"], scores["mr"]) >= 4 and script == "Latin":
            alt = "hi" if scores["hi"] >= scores["mr"] else "mr"
            if scores[alt] >= scores["en"] - 1:
                lang = alt

    if lang == "en":
        code = "en"
    elif dev_chars > 0:                      # any Devanagari at all: the user can read it, so answer in it
        code = lang
    else:
        code = f"{lang}-Latn"
    return LangResult(code=code, script=script, confidence=round(confidence, 2), scores=scores)
