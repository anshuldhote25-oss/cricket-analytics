"""Multilingual (English / Hindi / Marathi, Devanagari or Roman letters) NLP front-end
for the cricket analytics agent.  Usage:  from nlp import analyze;  frame = analyze(question)"""
from .pipeline import Frame, analyze, BLOCKING_INTENTS

__all__ = ["analyze", "Frame", "BLOCKING_INTENTS"]
