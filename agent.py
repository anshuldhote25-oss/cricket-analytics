"""
agent.py — Natural language to SQL translation via Groq API
"""
import json
import time
import re
from openai import OpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_MAX_TOKENS
from database import SCHEMA_CONTEXT
from nlp import analyze
from nlp.nlg import build_hints
from validator import validate_sql, ValidationError

def classify_intent(question: str) -> tuple:
    """Kept for backward compatibility. Now powered by the multilingual NLP pipeline (nlp/),
    so out-of-scope / external-data detection also works for Hindi, Marathi and Roman-script text."""
    frame = analyze(question)
    if frame.intent == "out_of_scope":
        return ("out_of_scope", frame.reply())
    if frame.intent == "external_data":
        return ("external", frame.reply())
    if frame.intent == "greeting":
        return ("greeting", frame.reply())
    return ("proceed", "")


class CricketAgent:
    def __init__(self):
        self.client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
        self.model = LLM_MODEL

    def _complete(self, user_content: str) -> str:
        """One chat completion. Asks for JSON mode; if the provider rejects that parameter,
        retries without it (the prompt already demands strict JSON and we strip code fences)."""
        kwargs = dict(
            model=self.model, temperature=0.0, max_tokens=LLM_MAX_TOKENS,
            messages=[{"role": "system", "content": SCHEMA_CONTEXT},
                      {"role": "user", "content": user_content}],
        )
        TRANSIENT = ("503", "502", "504", "500", "unavailable", "overloaded", "high demand", "timed out")
        use_json_mode = True
        last_exc = None
        for attempt in range(4):                        # waits 0s, 2s, 5s, 10s between tries
            if attempt:
                time.sleep((2, 5, 10)[attempt - 1])
            try:
                extra = {"response_format": {"type": "json_object"}} if use_json_mode else {}
                response = self.client.chat.completions.create(**extra, **kwargs)
                return (response.choices[0].message.content or "").strip()
            except Exception as e:
                last_exc = e
                msg = str(e).lower()
                if "401" in msg or "403" in msg or "429" in msg or "api key" in msg:
                    raise                               # auth / quota problems: do not retry
                if any(t in msg for t in TRANSIENT):
                    print(f"[agent] provider busy ({str(e)[:90]}...); retrying", flush=True)
                    continue                            # same request again after a short wait
                if use_json_mode:
                    print(f"[agent] JSON mode failed ({e}); retrying without response_format", flush=True)
                    use_json_mode = False
                    continue
                raise
        raise last_exc

    def ask(self, question: str) -> dict:
        # ---- NLP front-end: language ID, normalisation, entities, intent ---------------
        frame = analyze(question)
        nlp_info = frame.public()

        def result(**kw):
            base = {"sql": None, "explanation": None, "assumptions": None,
                    "error": None, "intent": "proceed", "nlp": nlp_info}
            base.update(kw)
            return base

        if frame.is_blocked:                       # greeting / out of scope / data we do not have
            intent = "external" if frame.intent == "external_data" else frame.intent
            return result(explanation=frame.reply(), intent=intent)

        # The original question stays authoritative; the NLP notes only ground the model.
        # Attempt 1 answers in the user's language. Devanagari uses many tokens and can truncate the
        # JSON, so if that fails we retry once asking for an English explanation (the SQL is the same).
        attempts = [f"{question}\n\n{frame.hints}"]
        if frame.language != "en":
            attempts.append(f"{question}\n\n{build_hints(frame, language='English')}")

        parsed, last_error, last_raw = None, "", ""
        for user_content in attempts:
            try:
                raw = self._complete(user_content)
                last_raw = raw
                raw = re.sub(r'^```(?:json)?\s*', '', raw)
                raw = re.sub(r'\s*```$', '', raw)
                parsed = json.loads(raw)
                break
            except json.JSONDecodeError as e:
                last_error = f"Could not parse AI response: {e}"
            except Exception as e:
                last_error = f"API error: {e}"
            print(f"[agent] attempt failed ({frame.language}): {last_error}", flush=True)

        if parsed is None:
            return result(explanation=last_error, error=last_error + (f" | raw: {last_raw[:300]}" if last_raw else ""),
                          intent="error")

        sql = parsed.get("sql")
        explanation = parsed.get("explanation", "")
        assumptions = parsed.get("assumptions", "")

        if not sql:
            return result(explanation=explanation, assumptions=assumptions, intent="unanswerable")

        try:
            sql = validate_sql(sql)
        except ValidationError as e:
            print(f"[agent] SQL validation failed: {e} | sql: {sql}", flush=True)
            return result(explanation=explanation, assumptions=assumptions,
                          error=f"SQL validation failed: {e}", intent="validation_error")

        return result(sql=sql, explanation=explanation, assumptions=assumptions)
