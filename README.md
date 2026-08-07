# Cricket Analytics AI Agent

An AI-powered conversational interface for cricket scouting analytics. Query ball-by-ball match data in plain English and get instant answers — no SQL required.

**Status**: Proof of Concept (PoC) | **Phase 2**: Web interface in progress

---

## Overview

Selectors, coaches, and scouts can now ask complex scouting questions in plain English and receive data-backed answers instantly. No SQL knowledge required.

**Example questions:**
- "Top 10 T20 batters by strike rate"
- "Left-arm orthodox bowlers with economy rate under 7 in the powerplay"
- "Best fielders in SMAT tournament"
- "Catches taken per district in Ranji Trophy"
- "Bowlers with most indiscipline (wides + no balls) in death overs"

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI (Python) + PostgreSQL 18 |
| **LLM** | Groq API — Llama 3.3 70B (free tier) |
| **Frontend** | React 18 + Vite 6 (dark cricket theme) |
| **Web Server** | Nginx with self-signed SSL |
| **Public Access** | ngrok (PoC testing) |
| **SQL Validation** | sqlglot (SELECT-only enforcement) |
| **Database Manager** | TablePlus |

---

## Getting Started

### Prerequisites

- macOS (Apple Silicon) or Linux
- PostgreSQL 18 (running via TablePlus)
- Python 3.14+
- Node.js 18+
- Groq API key (free tier, no credit card required): [console.groq.com](https://console.groq.com)

### 1. Clone & Setup

```bash
cd ~/Downloads/Circullence/CricPy/cricket-analytics
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file (copy from `.env.example`):

```env
GROQ_API_KEY=gsk_...
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cricket_analytics_db
DB_USER=postgres
DB_PASSWORD=your_password
```

### 3. Initialize Database

**Via TablePlus:**
1. Open TablePlus and connect to your PostgreSQL database
2. Run `schema.sql`
3. Run `data/add_fielding_extras.sql`
4. Run `data/add_bowler_discipline.sql`

**Or via Python:**
```bash
python3 load_data.py
```

### 4. Run the Application

**Terminal Tab 1 — FastAPI Backend:**
```bash
uvicorn web_app:app --host 127.0.0.1 --port 8000
```

**Terminal Tab 2 — Nginx Web Server:**
```bash
sudo nginx
```

**Terminal Tab 3 — ngrok Public Tunnel (for testing):**
```bash
ngrok http 8000
```

Visit: `http://localhost` (local) or `https://<ngrok-url>` (public testing)

---

## Project Structure

```
cricket-analytics/
├── main.py                          # CLI entry point
├── web_app.py                       # FastAPI backend + static file serving
├── agent.py                         # Groq API call, NL→SQL translation
├── database.py                      # PostgreSQL connection, schema context
├── validator.py                     # SQL safety validation (sqlglot)
├── config.py                        # .env loader
├── load_data.py                     # CSV data loader
├── generate_data.py                 # Synthetic data generator
├── requirements.txt                 # Python dependencies
├── schema.sql                       # PostgreSQL schema + base views
├── nginx.conf                       # Nginx reverse proxy config
├── .env                             # Credentials (never commit)
├── .env.example                     # Template
├── .gitignore
├── frontend/                        # React UI
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx                  # Full React chat interface
│       └── main.jsx
├── static/                          # Built React files (git-committed)
└── data/
    ├── tournaments.csv
    ├── players.csv
    ├── matches.csv
    ├── innings.csv
    ├── deliveries.csv
    ├── add_fielding_extras.sql      # Creates fielding_summary + extras_summary views
    └── add_bowler_discipline.sql    # Creates bowler_discipline view
```

---

## Database Schema

### Tables (5)

- **players** — player_id, name, gender, date_of_birth, batting_style, bowling_style, player_role, district, age_group, is_wicket_keeper
- **tournaments** — tournament_id, tournament_name, format (T20/ODI/FirstClass), gender, age_group, overs_per_innings, season
- **matches** — match_id, tournament_id, tournament_name, match_date, venue, team1, team2, toss_winner, match_winner, win_margin
- **innings** — innings_id, match_id, innings_number, batting_team, bowling_team, total_runs, total_wickets, total_overs, extras
- **deliveries** — delivery_id, innings_id, over_number, ball_number, phase, batter_id, bowler_id, runs_scored, extras_runs, is_wicket, wicket_type, fielder_name, *[50+ columns for complete ball-by-ball analysis]*

### Views (7)

- **batting_summary** — batting stats per player/tournament (runs, strike rate, boundaries)
- **bowling_summary** — bowling stats per player/tournament (wickets, economy rate, average)
- **phase_batting** — batting by phase (powerplay/middle/death)
- **phase_bowling** — bowling by phase
- **fielding_summary** — catches, stumpings, run outs per fielder
- **extras_summary** — wides, no balls, byes, leg byes per innings
- **bowler_discipline** — indiscipline metrics (wides + no balls) per bowler

---

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/query` | Send NL question → receive SQL + results |
| GET | `/api/health` | Database connection status |
| GET | `/api/browse/{view_name}` | Direct view query (bypass AI) |
| GET | `/api/examples` | Example questions for UI |
| GET | `/` | Serve React frontend |

### Example Request

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "top 10 T20 batters by strike rate"}'
```

### Example Response

```json
{
  "sql": "SELECT batter_name, strike_rate FROM batting_summary WHERE format='T20' ORDER BY strike_rate DESC LIMIT 10",
  "explanation": "Returns the top 10 batters in T20 format, sorted by strike rate in descending order.",
  "assumptions": "Defaulted to T20 format. Minimum 20 balls faced applied.",
  "results": [
    {"batter_name": "Player A", "strike_rate": 185.5},
    {"batter_name": "Player B", "strike_rate": 162.3},
    ...
  ]
}
```

---

## Dataset

**Synthetic, statistically calibrated to real domestic cricket:**

- **235 players** (male + female, Senior/U25/U19/U16)
- **11 tournaments** (Ranji, SMAT, VHT, U19, U16, Women's)
- **88 matches** across T20, ODI, FirstClass formats
- **~19,500 ball-by-ball deliveries**
- **Season**: 2024-25
- **Benchmarks**: Strike rates, economy rates, dismissal patterns match real domestic cricket

---

## How It Works

1. **User types a question** in the web interface (or Python CLI): "Top left-arm spinners by economy in the powerplay"
2. **Intent classifier** validates the question is in-scope (cricket-related)
3. **Groq Llama 3.3 70B** (via Groq API) receives:
   - Full database schema (tables, columns, views, aliases)
   - The user's question
   - System prompt with cricket terminology mappings
4. **LLM generates SQL** (JSON format) with explanation + assumptions
5. **sqlglot validator** ensures:
   - Query is SELECT-only (no INSERT/UPDATE/DELETE)
   - References only real tables/columns
   - No SQL injection possible
6. **PostgreSQL** executes the query (read-only connection)
7. **Results** returned to user with:
   - Data table (sortable, paginated)
   - Leaderboard with 🥇🥈🥉 medals
   - Underlying SQL (toggle-able)
   - Groq's explanation + assumptions

---

## Configuration

### Groq API

Free tier limits: 1,000 requests/day, 30 requests/minute.

Monitor usage in console.groq.com. For production, upgrade to a paid tier.

**Model**: Llama 3.3 70B  
**Temperature**: 0.0 (deterministic SQL generation)  
**Max tokens**: 1024  
**Response format**: JSON

### Nginx

Config at: `/opt/homebrew/etc/nginx/nginx.conf` (macOS with Homebrew)

- Port 80 → redirects to HTTPS
- Port 443 → SSL with self-signed cert at `~/.ssl/cricket/`
- Security headers: X-Frame-Options, HSTS, X-Content-Type-Options
- Proxies all traffic to FastAPI (127.0.0.1:8000)

### PostgreSQL

- **Host**: localhost:5432
- **Database**: cricket_analytics_db
- **User**: postgres
- **Connection**: Read-only enforced (`default_transaction_read_only=on`)
- **Manager**: TablePlus

---

## Known Issues & Workarounds

### PostgreSQL Connection Failed

**Error**: `FATAL: password authentication failed for user "postgres"`

**Fix**: Ensure `DB_PASSWORD` in `.env` is correct. Verify in TablePlus connection settings.

### Views Show "No Rows"

**Error**: Browse data modal shows empty tables

**Fix**: Rerun `data/add_fielding_extras.sql` and `data/add_bowler_discipline.sql` in TablePlus after data reload.

### Groq Rate Limits

**Error**: `429 Too Many Requests`

**Fix**: Wait until midnight UTC for free tier reset, or upgrade to paid tier.

### ngrok URL Changes

**Issue**: Free ngrok URL changes every restart

**Fix**: For production, use a real domain and Let's Encrypt SSL (see DEPLOYMENT.md).

---

## Deployment

### Development (Current)

- Nginx + ngrok for testing
- Self-signed SSL
- TablePlus for database management

### Production (Documented in DEPLOYMENT.md)

- Real domain (DNS) + Let's Encrypt SSL
- Dedicated cloud server (AWS/GCP/Azure)
- Paid Groq API tier (or alternative LLM)
- Real, licensed match data
- Persistent session history + logging

---

## Documents

Updated documentation available in this folder:

- **BRD_v2_UPDATED.md** — Business requirements and objectives
- **FSD_v2_UPDATED.md** — Functional specifications and acceptance criteria
- **Architecture_v2_Cricket_Analytics_PoC.docx** — Technical architecture (in progress)
- **DEPLOYMENT.md** — Production deployment guide

---

## Contacts & Support

- **Business Owner**: Sujit Kane
- **Developer**: Anshul Dhote
- **Colleague**: Sarang (platform evaluation)
- **Organization**: Circullence

---

## License

Internal PoC. Not licensed for external distribution.

---

## FAQ

**Q: Can I use real ESPNcricinfo data?**  
A: Not without explicit permission. Terms of service prohibit scraping. Synthetic data is calibrated to real benchmarks for PoC validation.

**Q: What if I hit Groq API rate limits?**  
A: Free tier resets at midnight UTC (1,000 requests/day). For immediate needs, upgrade to paid tier or switch to another LLM provider (OpenAI, Anthropic, etc.).

**Q: How accurate is the LLM SQL generation?**  
A: >95% accuracy on representative test cases (validated by Sujit Kane). All queries are validated with sqlglot before execution.

**Q: Can coaches directly edit player data?**  
A: No. The system is read-only. Data updates require administrator access and direct database queries.

**Q: Is this production-ready?**  
A: No. This is a PoC. Production requires real data, paid LLM tier, proper SSL, persistent logging, and multi-association support.

---

**Last Updated**: 2026-08-08  
**Version**: 2.1 (Groq API)
