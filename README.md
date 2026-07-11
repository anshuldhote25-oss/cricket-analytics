# Cricket Analytics

This tool lets cricket scouts and selectors ask questions about player performance in plain English and get instant answers with no SQL, no spreadsheets, no waiting for a data analyst.

---

## What you can ask

```
Top U19 female batters by total runs this season
Which bowlers have the best economy in the powerplay?
Best leg-spin bowlers in SMAT by wickets taken
Show me all-rounders with strike rate above 130 and economy below 8
Top-order batters with boundary percentage over 20 in T20
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
CREATE DATABASE circullence;
```

Switch to it using the dropdown in the green bar at the top, then:

- Open `schema.sql`, copy everything, paste into a query tab, and click Run All
- You should see 5 tables appear in the sidebar: `players`, `tournaments`, `matches`, `innings`, `deliveries`

Now import the data — do this in order or it will fail:

1. Right-click `tournaments` → Import → select `data/tournaments.csv`
2. Right-click `players` → Import → select `data/players.csv`
3. Right-click `matches` → Import → select `data/matches.csv` (if this fails, run `data/matches_insert.sql` instead)
4. Right-click `innings` → Import → select `data/innings.csv`
5. Right-click `deliveries` → Import → select `data/deliveries.csv`

Check it worked:
```sql
SELECT count(*) FROM players;      -- should be 235
SELECT count(*) FROM deliveries;   -- should be around 18100
```

### 4. Get a free API key

1. Go to **github.com/marketplace/models**
2. Sign in with your GitHub account
3. Click on GPT-4o-mini → Get API key
4. Copy the token (starts with `github_pat_...`)

No credit card needed — it's completely free.

### 5. Add your credentials

```bash
cp .env.example .env
```

Open `.env` in VS Code and fill in your details:

```
GITHUB_TOKEN=paste_your_token_here

DB_HOST=localhost
DB_PORT=5432
DB_NAME=circullence
DB_USER=postgres
DB_PASSWORD=your_postgres_password
```

Save the file. Never share this file with anyone.

### 6. Run it

```bash
python3 main.py
```

You'll see a prompt — just start typing your question.

---

## Commands

| Type this | What happens |
|---|---|
| Any cricket question | Gets answered with a data table |
| `help` | Shows example questions |
| `sql` | Shows/hides the SQL query that was generated |
| `quit` | Exits |

---

## Something not working?

**Can't connect to the database**
→ Open TablePlus and check if you can connect. If not, PostgreSQL might not be running.
→ Check your password in `.env` is correct.

**401 Unauthorized error**
→ Your GitHub token has expired. Go to github.com/marketplace/models and generate a new one.

**No results showing up**
→ Try a simpler question first. Check the data loaded correctly in TablePlus.

**SQL validation error**
→ Just rephrase your question slightly and try again.

---

## About the data

The dataset has 235 players, 88 matches, and around 18,100 ball-by-ball deliveries covering the 2024-25 domestic season across Ranji Trophy, SMAT, VHT, and age-group tournaments for both men and women.

The data is synthetic but built to match real cricket statistics — correct strike rates, economy rates, dot ball percentages, and boundary percentages for each format.

---

## License

MIT — free to use, modify, and share. See `LICENSE` for details.

---

*PoC built for domestic cricket association scouting analytics. Designed to be extended with real match data.*