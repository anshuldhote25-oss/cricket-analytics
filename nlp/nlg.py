"""
nlp/nlg.py - natural-language generation helpers.

  * message()   : fixed replies (out of scope / external data / greeting) in all 5 input styles
  * describe()  : one-line English "interpreted as ..." summary shown in the UI
  * build_hints(): structured notes that are appended to the question before it goes to the LLM

Concepts: template-based NLG, localisation, grounding an LLM with extracted slots.
"""
from __future__ import annotations

from .lexicon import LABELS

MESSAGES = {
    "out_of_scope": {
        "en": "That question is outside cricket analytics scope. Please ask about player performance, "
              "match statistics, batting/bowling analysis, or tournament data.",
        "hi": "यह सवाल क्रिकेट एनालिटिक्स के दायरे से बाहर है। कृपया खिलाड़ियों के प्रदर्शन, मैच के आंकड़ों, "
              "बल्लेबाज़ी/गेंदबाज़ी विश्लेषण या टूर्नामेंट डेटा के बारे में पूछें।",
        "mr": "हा प्रश्न क्रिकेट विश्लेषणाच्या कक्षेबाहेरचा आहे. कृपया खेळाडूंची कामगिरी, सामन्यांची आकडेवारी, "
              "फलंदाजी/गोलंदाजी विश्लेषण किंवा स्पर्धेचा डेटा याबद्दल विचारा.",
        "hi-Latn": "Yeh sawal cricket analytics ke dayre se bahar hai. Kripya khiladiyon ke pradarshan, match ke "
                   "aankdon, batting/bowling vishleshan ya tournament data ke baare mein poochhein.",
        "mr-Latn": "Ha prashna cricket analytics chya kakshe baherchaa aahe. Krupaya khelaadunchi kamgiri, "
                   "samanyanchi aakdevari, falandaji/golandaji vishleshan kinva spardhecha data yabaddal vichara.",
    },
    "external_data": {
        "en": "That question references data outside this dataset (e.g. IPL or international cricket). "
              "This system covers domestic association cricket only.",
        "hi": "यह सवाल इस डेटासेट से बाहर के डेटा (जैसे IPL या अंतरराष्ट्रीय क्रिकेट) के बारे में है। "
              "यह सिस्टम केवल घरेलू एसोसिएशन क्रिकेट को कवर करता है।",
        "mr": "हा प्रश्न या डेटासेटबाहेरील डेटाबद्दल (उदा. IPL किंवा आंतरराष्ट्रीय क्रिकेट) आहे. "
              "ही प्रणाली फक्त देशांतर्गत असोसिएशन क्रिकेट कव्हर करते.",
        "hi-Latn": "Yeh sawal is dataset ke bahar ke data (jaise IPL ya international cricket) ke baare mein hai. "
                   "Yeh system sirf gharelu association cricket ko cover karta hai.",
        "mr-Latn": "Ha prashna ya dataset baherchya data baddal (udaharan IPL kinva antararashtriya cricket) aahe. "
                   "Hi pranali phakt deshantargat association cricket cover karte.",
    },
    "greeting": {
        "en": "Hello! Ask me about player performance, e.g. 'Top 10 T20 batters by strike rate'. "
              "You can type in English, Hindi or Marathi - even in Roman letters.",
        "hi": "नमस्ते! खिलाड़ियों के प्रदर्शन के बारे में पूछिए, जैसे 'T20 में स्ट्राइक रेट के हिसाब से टॉप 10 बल्लेबाज़'। "
              "आप अंग्रेज़ी, हिंदी या मराठी में लिख सकते हैं।",
        "mr": "नमस्कार! खेळाडूंच्या कामगिरीबद्दल विचारा, उदा. 'T20 मध्ये स्ट्राइक रेटनुसार टॉप 10 फलंदाज'. "
              "तुम्ही इंग्रजी, हिंदी किंवा मराठीत लिहू शकता.",
        "hi-Latn": "Namaste! Khiladiyon ke pradarshan ke baare mein poochhiye, jaise 'T20 mein strike rate ke hisab se "
                   "top 10 ballebaaz'. Aap English, Hindi ya Marathi mein likh sakte hain.",
        "mr-Latn": "Namaskar! Khelaadunchya kamgiribaddal vichara, udaharan 'T20 madhe strike rate nusar top 10 falandaj'. "
                   "Tumhi English, Hindi kinva Marathit lihu shakta.",
    },
}


def message(kind: str, lang_code: str) -> str:
    return MESSAGES[kind].get(lang_code) or MESSAGES[kind]["en"]


# --------------------------------------------------------------------------- #
_SUBJECT = {"batting": "batters", "bowling": "bowlers", "fielding": "fielders", "discipline": "bowlers",
            "allrounder": "all-rounders", "general": "players"}
_ROLE_NOUN = {"batter": "batters", "bowler": "bowlers", "all-rounder": "all-rounders",
              "wicket-keeper": "wicket-keepers", "fielder": "fielders"}
_PHASE = {"powerplay": "in the powerplay", "death": "in the death overs", "middle": "in the middle overs"}


def _unique(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _vals(frame, cat):
    return _unique(e.canonical for e in frame.entities if e.category == cat)


def describe(frame) -> str:
    """English one-liner: how the system understood the question."""
    dirs = _vals(frame, "direction")
    head = ""
    if "asc" in dirs:
        head = f"Lowest {frame.limit}" if frame.limit else "Lowest"
    elif dirs:
        head = f"Top {frame.limit}" if frame.limit else "Top"

    adjs = _vals(frame, "age_group") + _vals(frame, "gender") + _vals(frame, "bowler_type") + _vals(frame, "format")
    adjs += [LABELS.get(p, p) for p in _vals(frame, "position")]

    roles = _vals(frame, "role")
    groups = _vals(frame, "group")
    if "team" in groups:
        noun = "teams"
    elif roles:
        noun = _ROLE_NOUN.get(roles[0], "players")
    else:
        noun = _SUBJECT.get(frame.intent, "players")

    metrics = [LABELS.get(m, m) for m in _vals(frame, "metric")]
    players = _vals(frame, "player")
    if players:
        noun = "stats for " + " and ".join(players)
        head, adjs = "", []
    by = f" by {' and '.join(metrics)}" if metrics else ""
    by += " per district" if "district" in groups else ""

    phase = next((f" {_PHASE[p]}" for p in _vals(frame, "phase")), "")
    tourn = "".join(f" in {t}" for t in _vals(frame, "tournament"))
    dist = "".join(f" from {d}" for d in _vals(frame, "district"))
    thr = "".join(f" with {LABELS.get(t['metric'], t['metric'] or 'value')} {t['op']} {t['value']}"
                  for t in frame.thresholds)

    text = " ".join(x for x in [head, " ".join(adjs), noun] if x) + by + phase + tourn + dist + thr
    return text[:1].upper() + text[1:]


_VIEWS = {"batting": "batting_summary / phase_batting", "bowling": "bowling_summary / phase_bowling",
          "fielding": "fielding_summary", "discipline": "bowler_discipline / extras_summary",
          "allrounder": "batting_summary JOIN bowling_summary JOIN players", "general": "players / matches (player lookups: batting_summary + bowling_summary)"}


def build_hints(frame, language: str | None = None) -> str:
    """Notes appended to the user's question. The LLM is told the question stays authoritative."""
    lines = ["[NLP PREPROCESSOR NOTES - generated automatically; the question above is authoritative]",
             f"Detected language: {frame.language_label}"]
    if frame.entities:
        lines.append(f"Interpreted as: {frame.interpreted_as}")
    if frame.intent in _VIEWS:
        lines.append(f"Likely intent: {frame.intent} (suggested views: {_VIEWS[frame.intent]})")
    filters = _unique(e.sql for e in frame.entities
                      if e.sql and e.category in ("format", "tournament", "gender", "age_group", "bowler_type",
                                                  "phase", "position", "district", "player")
                      or (e.sql and e.category == "role" and e.canonical in ("all-rounder", "wicket-keeper")))
    if filters:
        lines.append("Filters detected: " + "; ".join(filters))
    metrics = _vals(frame, "metric")
    if metrics:
        lines.append("Statistics mentioned: " + ", ".join(m for m in metrics))
    dirs = _vals(frame, "direction")
    if "asc" in dirs:
        lines.append("Ranking: lowest values first" + (f", limit {frame.limit}" if frame.limit else ""))
    elif dirs:
        lines.append("Ranking: best/highest first" + (f", limit {frame.limit}" if frame.limit else ""))
    if frame.thresholds:
        lines.append("Thresholds: " + "; ".join(f"{t['metric']} {t['op']} {t['value']}" for t in frame.thresholds))
    if set(metrics) & {"economy_rate", "average"} and "desc" in dirs:
        lines.append("Note: for economy rate, 'best' means the LOWEST value.")
    lines.append(f'Write the "explanation" and "assumptions" values in: {language or frame.llm_language}. '
                 'Keep each of them to ONE short sentence. '
                 'Keep the "sql" value as plain SQL and keep the JSON keys in English.')
    return "\n".join(lines)
