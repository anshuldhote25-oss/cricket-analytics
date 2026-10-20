import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# LLM provider - any OpenAI-compatible API works (Groq, Google Gemini, GitHub Models, OpenRouter ...).
# Set these in .env to switch provider without touching code. Defaults keep the old Groq behaviour.
LLM_API_KEY    = os.getenv("LLM_API_KEY") or GROQ_API_KEY
LLM_BASE_URL   = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_MODEL      = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 2048))
DB_HOST      = os.getenv("DB_HOST", "localhost")
DB_PORT      = int(os.getenv("DB_PORT", 5432))
DB_NAME      = os.getenv("DB_NAME", "cricket_analytics_db")
DB_USER      = os.getenv("DB_USER", "postgres")
DB_PASSWORD  = os.getenv("DB_PASSWORD")

def validate():
    missing = []
    if not LLM_API_KEY:
        missing.append("LLM_API_KEY (or GROQ_API_KEY)")
    if not DB_PASSWORD:
        missing.append("DB_PASSWORD")
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Please check your .env file."
        )
