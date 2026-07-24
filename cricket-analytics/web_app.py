"""
web_app.py — Cricket Analytics AI Agent
FastAPI backend serving the React chat UI.

Run with:
    uvicorn web_app:app --host 0.0.0.0 --port 8000

Or via Nginx (see DEPLOYMENT.md).
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import traceback

from config import validate, DB_NAME
from database import test_connection, run_query
from agent import CricketAgent

# ── App setup ─────────────────────────────────────────────────
app = FastAPI(
    title="Cricket Analytics AI Agent",
    description="Natural language cricket analytics powered by AI",
    version="1.0.0"
)

# Validate config on startup
try:
    validate()
except EnvironmentError as e:
    raise RuntimeError(f"Configuration error: {e}")

# Initialize agent once at startup
agent = CricketAgent()


# ── Request/Response models ───────────────────────────────────
class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    success: bool
    explanation: str = ""
    assumptions: str = ""
    sql: str = ""
    columns: list = []
    rows: list = []
    row_count: int = 0
    intent: str = ""
    error: str = ""


# ── API Routes ────────────────────────────────────────────────
@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    db_ok = test_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unavailable",
        "db_name": DB_NAME,
    }


@app.post("/api/query", response_model=QueryResponse)
def query(req: QueryRequest):
    """
    Main query endpoint.
    Accepts a natural language question, returns SQL results.
    """
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Step 1: AI translates question to SQL
    result = agent.ask(question)

    # Step 2: Handle non-proceed intents
    if result["intent"] in ("out_of_scope", "external", "unanswerable"):
        return QueryResponse(
            success=False,
            explanation=result["explanation"],
            intent=result["intent"],
        )

    if result["intent"] in ("error", "validation_error"):
        return QueryResponse(
            success=False,
            explanation="I couldn't generate a valid query for that question.",
            error=result.get("error") or result.get("explanation") or "",
            intent=result["intent"],
        )

    # Step 3: Execute the validated SQL
    try:
        rows, columns = run_query(result["sql"])
        # Convert any non-serializable types to strings
        clean_rows = []
        for row in rows:
            clean_row = {}
            for k, v in row.items():
                if v is None:
                    clean_row[k] = None
                elif isinstance(v, float):
                    clean_row[k] = round(v, 2)
                else:
                    clean_row[k] = str(v) if not isinstance(v, (int, bool)) else v
            clean_rows.append(clean_row)

        return QueryResponse(
            success=True,
            explanation=result["explanation"],
            assumptions=result.get("assumptions") or "",
            sql=result["sql"],
            columns=columns,
            rows=clean_rows,
            row_count=len(clean_rows),
            intent="proceed",
        )
    except Exception as e:
        return QueryResponse(
            success=False,
            explanation="The query ran into an error.",
            error=str(e),
            intent="error",
        )


@app.get("/api/examples")
def get_examples():
    """Returns example questions for the UI."""
    return {
        "examples": [
            "Top 10 T20 batters by strike rate this season",
            "Which bowlers have the best economy in the powerplay?",
            "Top U19 female batters by total runs",
            "Best leg-spin bowlers in SMAT by wickets taken",
            "Who took the most catches this season?",
            "Which bowling teams give the most wides and no balls?",
            "Top all-rounders by runs and wickets combined",
            "Best death-over bowlers by dot ball percentage",
            "Which districts produce the most players?",
            "Top-order batters with boundary percentage over 20 in T20",
        ]
    }


# ── Serve React frontend ──────────────────────────────────────
# Mount static files if the built frontend exists
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    @app.get("/{path:path}")
    def serve_spa(path: str):
        # Serve index.html for all non-API routes (React Router support)
        if path.startswith("api/"):
            raise HTTPException(status_code=404)
        index = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index):
            return FileResponse(index)
        raise HTTPException(status_code=404)
