# Cricket Analytics AI Agent — PoC v1.0

A conversational CLI that translates plain-English cricket scouting
questions into SQL queries against a PostgreSQL database.

## Setup (one-time)

### 1. Create your .env file
```bash
cp .env.example .env
```
Open `.env` in VS Code and fill in:
- `GEMINI_API_KEY` — your key from aistudio.google.com
- `DB_PASSWORD` — your PostgreSQL password

### 2. Install dependencies
```bash
pip3 install -r requirements.txt
```

### 3. Run the agent
```bash
python3 main.py
```

## Usage

Type any cricket analytics question at the prompt:
```
Ask > Show me the top 10 T20 batters by strike rate
Ask > Which bowlers have the best economy in the powerplay?
Ask > Top U19 female batters by total runs this season
Ask > sql        ← toggle SQL display on/off
Ask > help       ← show example questions
Ask > quit       ← exit
```

## Project Structure
```
cricket_agent/
├── .env              ← your credentials (never share this)
├── .env.example      ← template for .env
├── config.py         ← loads environment variables
├── database.py       ← PostgreSQL connection + schema context
├── validator.py      ← SQL safety validation
├── agent.py          ← Gemini AI + query translation
├── main.py           ← CLI entry point
└── requirements.txt  ← Python dependencies
```
