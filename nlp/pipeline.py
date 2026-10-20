"""
nlp/pipeline.py - the full multilingual NLP pipeline.

    raw text
      -> normalize_text            (Unicode, digits, nukta, symbols)
      -> tokenize
      -> detect_language           (en | hi | mr | hi-Latn | mr-Latn)
      -> extract_entities          (gazetteer + stemming + fuzzy matching)
      -> resolve_numbers           (top-N limit, "economy under 7" thresholds)
      -> classify intent           (rules + Naive Bayes)
      -> describe / build_hints    (English summary + LLM grounding notes)

analyze(text) returns a Frame. Nothing here calls the network.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import nlg
from .entities import Entity, extract_entities, resolve_numbers
from .intent import SUB_INTENTS, NaiveBayesIntent, featurize, rule_intent
from .lang_id import LangResult, detect_language
from .lexicon import DOMAIN_CATEGORIES
from .normalize import normalize_text, tokenize

BLOCKING_INTENTS = {"out_of_scope", "external_data", "greeting"}
_MODEL = None
_MODEL_LOADED = False


def get_model():
    global _MODEL, _MODEL_LOADED
    if not _MODEL_LOADED:
        _MODEL, _MODEL_LOADED = NaiveBayesIntent.load(), True
    return _MODEL


@dataclass
class Frame:
    original: str
    normalized: str
    tokens: list
    lang: LangResult
    entities: list
    limit: int | None
    thresholds: list
    intent: str
    intent_confidence: float
    intent_source: str
    interpreted_as: str = ""
    hints: str = ""

    # convenience -----------------------------------------------------------
    @property
    def language(self) -> str:
        return self.lang.code

    @property
    def language_label(self) -> str:
        return self.lang.label

    @property
    def llm_language(self) -> str:
        return self.lang.llm_language

    @property
    def is_blocked(self) -> bool:
        return self.intent in BLOCKING_INTENTS

    def reply(self) -> str:
        return nlg.message(self.intent, self.language)

    def public(self) -> dict:
        shown = [e.public() for e in self.entities if e.category in DOMAIN_CATEGORIES or e.category == "direction"]
        return {
            "language": self.language, "language_label": self.language_label,
            "language_confidence": self.lang.confidence,
            "intent": self.intent, "intent_confidence": round(self.intent_confidence, 2),
            "intent_source": self.intent_source,
            "interpreted_as": self.interpreted_as, "entities": shown,
            "limit": self.limit, "thresholds": self.thresholds,
        }


def _decide_intent(tokens, entities, model):
    cats = [e.category for e in entities]
    domain = [e for e in entities if e.category in DOMAIN_CATEGORIES]
    rule = rule_intent(entities)

    if "external" in cats:
        return "external_data", 1.0, "lexicon"
    if "oos" in cats and len(domain) < 2:
        return "out_of_scope", 1.0, "lexicon"
    if "greeting" in cats and not domain and len(tokens) <= 5:
        return "greeting", 1.0, "lexicon"

    # 1. entities clearly point to a sub-intent -> trust the deterministic rules
    if rule in SUB_INTENTS:
        return rule, 1.0, "rule"
    if model is None:
        return "unknown", 0.0, "rule"

    # 2. no usable entities -> fall back to the learned Naive Bayes classifier
    probs = model.predict_proba(featurize(tokens, entities))
    top = max(probs, key=probs.get)
    p = probs[top]
    # a learned guess may only block a question when it is very sure; greetings need a lexicon hit
    if top == "out_of_scope" and p >= 0.9 and not domain:
        return "out_of_scope", p, "nb"
    if top in SUB_INTENTS and p >= 0.8 and domain:
        return top, p, "nb"
    return "unknown", p, "nb"


def analyze(text: str, model=None) -> Frame:
    model = model if model is not None else get_model()
    normalized = normalize_text(text)
    tokens = tokenize(text)
    lang = detect_language(text, tokens)
    entities = extract_entities(tokens)
    limit, thresholds = resolve_numbers(tokens, entities)
    intent, conf, source = _decide_intent(tokens, entities, model)
    frame = Frame(text, normalized, tokens, lang, entities, limit, thresholds, intent, conf, source)
    frame.interpreted_as = nlg.describe(frame) if any(e.category in DOMAIN_CATEGORIES for e in entities) else ""
    frame.hints = nlg.build_hints(frame)
    return frame
