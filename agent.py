import json
import re
from openai import OpenAI
from config import GITHUB_TOKEN
from database import SCHEMA_CONTEXT
from validator import validate_sql, ValidationError

# unrelated questions
OUT_OF_SCOPE_PATTERNS = [
    r'\bweather\b', r'\bstock\b', r'\bfinance\b', r'\bnews\b',
    r'\bpolitics?\b', r'\brecipe\b', r'\btravel\b', r'\bmovie\b',
    r'\bsong\b', r'\bpoem\b',
]

# unanswerable related questions
EXTERNAL_DATA_PATTERNS = [
    r'\bipl\b', r'\bworld\s*cup\b', r'\binternational\b',
    r'\bnational\s+team\b',
]


def classify_intent(question: str) -> tuple:
    q = question.lower()
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, q):
            return (
                "out_of_scope",
                "That question is outside cricket analytics scope. "
                "Please ask about player performance, match statistics, "
                "batting/bowling analysis, or tournament data."
            )
    for pattern in EXTERNAL_DATA_PATTERNS:
        if re.search(pattern, q):
            return (
                "external",
                "That question references data outside this dataset "
                "(e.g. IPL or international cricket). "
                "This system covers domestic association cricket only."
            )
    return ("proceed", "")


class CricketAgent:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=GITHUB_TOKEN,
        )
        self.model = "gpt-4o-mini"

    def ask(self, question: str) -> dict:
        intent, message = classify_intent(question)
        if intent != "proceed":
            return {
                "sql": None,
                "explanation": message,
                "assumptions": None,
                "error": None,
                "intent": intent,
            }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.0,
                max_tokens=1024,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": SCHEMA_CONTEXT,
                    },
                    {
                        "role": "user",
                        "content": question,
                    }
                ]
            )
            raw = response.choices[0].message.content.strip()
        except Exception as e:
            return {
                "sql": None,
                "explanation": None,
                "assumptions": None,
                "error": f"API error: {e}",
                "intent": "error",
            }

        try:
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            result = json.loads(raw)
        except json.JSONDecodeError as e:
            return {
                "sql": None,
                "explanation": f"Could not parse AI response: {e}",
                "assumptions": None,
                "error": raw,
                "intent": "error",
            }

        sql         = result.get("sql")
        explanation = result.get("explanation", "")
        assumptions = result.get("assumptions", "")

        if not sql:
            return {
                "sql": None,
                "explanation": explanation,
                "assumptions": assumptions,
                "error": None,
                "intent": "unanswerable",
            }

        try:
            sql = validate_sql(sql)
        except ValidationError as e:
            return {
                "sql": None,
                "explanation": explanation,
                "assumptions": assumptions,
                "error": f"SQL validation failed: {e}",
                "intent": "validation_error",
            }

        return {
            "sql": sql,
            "explanation": explanation,
            "assumptions": assumptions,
            "error": None,
            "intent": "proceed",
        }