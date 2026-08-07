"""
web_app.py — FastAPI backend for Cricket Analytics
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from config import validate, DB_NAME
from database import test_connection, run_query
from agent import CricketAgent

app = FastAPI(
    title="Cricket Analytics AI Agent",
    description="Natural language cricket analytics powered by AI",
    version="1.0.0"
)

try:
    validate()
except EnvironmentError as e:
    raise RuntimeError(f"Configuration error: {e}")

agent = CricketAgent()


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


def clean_rows(rows):
    result = []
    for row in rows:
        clean = {}
        for k, v in row.items():
            if v is None:
                clean[k] = None
            elif isinstance(v, float):
                clean[k] = round(v, 2)
            else:
                clean[k] = str(v) if not isinstance(v, (int, bool)) else v
        result.append(clean)
    return result


@app.get("/api/health")
def health_check():
    db_ok = test_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unavailable",
        "db_name": DB_NAME,
    }


@app.get("/api/browse/{view_name}")
def browse_view(view_name: str):
    allowed = [
        "batting_summary", "bowling_summary",
        "phase_batting", "phase_bowling",
        "fielding_summary", "extras_summary", "bowler_discipline"
    ]
    if view_name not in allowed:
        raise HTTPException(status_code=400, detail=f"View '{view_name}' not allowed.")
    try:
        rows, columns = run_query(f"SELECT * FROM {view_name} LIMIT 100")
        return {
            "success": True,
            "columns": columns,
            "rows": clean_rows(rows),
            "row_count": len(rows)
        }
    except Exception as e:
        return {"success": False, "columns": [], "rows": [], "error": str(e)}


@app.post("/api/query", response_model=QueryResponse)
def query(req: QueryRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    result = agent.ask(question)

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

    try:
        rows, columns = run_query(result["sql"])
        return QueryResponse(
            success=True,
            explanation=result["explanation"],
            assumptions=result.get("assumptions") or "",
            sql=result["sql"],
            columns=columns,
            rows=clean_rows(rows),
            row_count=len(rows),
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
    return {
        "examples": [
            "Top 10 T20 batters by strike rate this season",
            "Which bowlers have the best economy in the powerplay?",
            "Top U19 female batters by total runs",
            "Who took the most catches this season?",
            "Best leg-spin bowlers in SMAT by wickets taken",
            "Top all-rounders by runs and wickets combined",
            "Which teams give the most wides?",
            "Best death-over bowlers by dot ball percentage",
            "Which districts produce the most players?",
            "Top-order batters with boundary percentage over 20 in T20",
        ]
    }


# Serve React frontend
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    @app.get("/{path:path}")
    def serve_spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(status_code=404)
        index = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index):
            return FileResponse(index)
        raise HTTPException(status_code=404)
