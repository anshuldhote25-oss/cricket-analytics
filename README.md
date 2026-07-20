# Cricket Analytics AI Agent 🏏

This tool lets cricket scouts and selectors ask questions about player performance in plain English and get instant answers — no SQL, no spreadsheets, no waiting for a data analyst.

---

## What you can ask

```
Top U19 female batters by total runs this season
Which bowlers have the best economy in the powerplay?
Best leg-spin bowlers in SMAT by wickets taken
Show me all-rounders with strike rate above 130 and economy below 8
Top-order batters with boundary percentage over 20 in T20
Who took the most catches this season?
Which bowlers gave the most wides and no balls?
```

It reads your question, turns it into a database query behind the scenes, and shows you a table of results.

---

## What you need before starting

Make sure these are installed on your computer:

- **Python 3.10+** — python.org/downloads
- **PostgreSQL 14+** — enterprisedb.com/downloads/postgres-postgresql-downloads
- **TablePlus** — tableplus.com (to manage the database)
- **VS Code** — code.visualstudio.com (to run the code)
- **Git** — git-scm.com/downloads

---

## Setting it up

### 1. Get the code

Open VS Code, go to Terminal → New Terminal, and run:

```bash
git clone https://github.com/anshuldhote25-oss/cricket-analytics.git
cd cricket-analytics
```

### 2. Install the Python packages

```bash
pip3 install -r requirements.txt
```

### 3. Set up the database

Open **TablePlus** and connect to PostgreSQL (host: localhost, port: 5432, user: postgres).

Create a new database:
```sql
CREATE DATABASE cricket_analytics_db;
```

Switch to it using the dropdown in the green bar at the top, then:

- Open `schema.sql`, copy everything, paste into a query tab, and click Run All
- You should see 5 tables appear in the sidebar: `players`, `tournaments`, `matches`, `innings`, `deliveries`

### 4. Load the data

Instead of manually importing CSVs, just run:

```bash
python3 load_data.py
```

This loads all tables in the correct order with proper data types. You should see:

```
[OK] tournaments  — 11 rows
[OK] players      — 235 rows
[OK] matches      — 88 rows
[OK] innings      — 176 rows
[OK] deliveries   — 19551 rows
All data loaded successfully!
```

### 5. Get a free API key

1. Go to **github.com/marketplace/models**
2. Sign in with your GitHub account
3. Click on GPT-4o-mini → Get API key
4. Copy the token (starts with `github_pat_...`)

No credit card needed — it's completely free.

### 6. Add your credentials

```bash
cp .env.example .env
```

Open `.env` in VS Code and fill in your details:

```
GITHUB_TOKEN=paste_your_token_here

DB_HOST=localhost
DB_PORT=5432
DB_NAME=cricket_analytics_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
```

Save the file. Never share this file with anyone.

### 7. Run it

**CLI mode (terminal):**
```bash
python3 main.py
```

**Web mode (browser):**
```bash
uvicorn web_app:app --host 0.0.0.0 --port 8000
```
Then open your browser and go to `http://localhost:8000`

---

## Commands (CLI mode)

| Type this | What happens |
|---|---|
| Any cricket question | Gets answered with a data table |
| `help` | Shows example questions |
| `sql` | Shows/hides the SQL query that was generated |
| `quit` | Exits |

---

## Project structure

```
cricket-analytics/
├── main.py                  ← CLI entry point
├── web_app.py               ← Web interface (FastAPI + browser UI)
├── agent.py                 ← AI layer — translates questions to SQL
├── database.py              ← PostgreSQL connection + schema context
├── validator.py             ← SQL safety validation
├── config.py                ← Environment variable loader
├── load_data.py             ← Loads all CSV data into the database
├── generate_data.py         ← Regenerates synthetic data if needed
├── requirements.txt         ← Python dependencies
├── schema.sql               ← Database schema (run once to set up)
├── .env.example             ← Template for your .env file
├── .gitignore               ← Keeps secrets out of Git
└── data/
    ├── tournaments.csv
    ├── players.csv
    ├── matches.csv
    ├── innings.csv
    └── deliveries.csv
```

---

## Production data

The data in the `data/` folder is **synthetic** — generated to match real-world domestic cricket statistical benchmarks for development and testing.

For a production deployment, replace it with real ball-by-ball data from:

- **ESPNcricinfo** — via a licensed data feed (not public scraping)
- **CricViz** — professional cricket analytics data provider
- **Association's own scoring system** — if the association uses a scoring app (CricHQ, PlayCricket, or similar), data can be exported directly into the same schema

No code changes are needed — just replace the CSV files in `data/` and re-run `python3 load_data.py`.

> **Note for administrators:** Arrange a real data refresh with your association's data manager before using this tool for actual selection decisions.

---

## Web deployment (Nginx + SSL)

See `DEPLOYMENT.md` for full instructions on deploying this application over the web with Nginx and SSL.

---

## Something not working?

**Can't connect to the database**
→ Open TablePlus and check if you can connect. If not, PostgreSQL might not be running.
→ Double-check `DB_NAME=cricket_analytics_db` in your `.env` file.

**401 Unauthorized error**
→ Your GitHub token has expired. Go to github.com/marketplace/models and generate a new one.

**No results showing up**
→ Try a simpler question first. Run `python3 load_data.py` again to confirm data loaded correctly.

**SQL validation error**
→ Just rephrase your question slightly and try again.

**load_data.py can't find CSV files**
→ Make sure all CSV files are inside the `data/` folder, not the root folder.

---

## About the data

The dataset covers the 2024-25 domestic season with 235 players, 88 matches, and ~19,500 ball-by-ball deliveries across Ranji Trophy, SMAT, VHT, and age-group tournaments for both men and women. It includes batting, bowling, fielding (catches, stumpings, run outs), and extras data.

---

## License

MIT — free to use, modify, and share. See `LICENSE` for details.

---

*PoC built for domestic cricket association scouting analytics. Designed to be extended with real match data and deployed on Google Cloud or Azure.*
