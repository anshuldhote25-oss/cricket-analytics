# Business Requirement Document

## Conversational AI for Cricket Analytics

*Democratizing Data-Driven Scouting in Indian Domestic Leagues*

**Proof of Concept**

| Aspect | Details |
|--------|---------|
| **Document Type** | Business Requirement Document (BRD) |
| **Project** | AI-Powered Cricket Scouting & Analytics Agent |
| **Prepared By** | Anshul Dhote |
| **Reviewed By** | Sujit Kane |
| **Version** | 2.1 |
| **Status** | Updated - Tech Stack Revised (Groq API) |
| **Date** | 2026-08-08 |

---

## 1. Purpose of Document

This Business Requirement Document (BRD) defines the business need, objectives, scope, and success criteria for the AI-Powered Cricket Scouting and Analytics Agent being built as a Proof of Concept (PoC). It is intended to align the business stakeholder and the development team on what is being built and why.

---

## 2. Background & Business Context

The Indian domestic cricket ecosystem is the largest talent pipeline in the world. The BCCI has scheduled an unprecedented volume of domestic matches across formats (Ranji Trophy, Syed Mushtaq Ali Trophy, Vijay Hazare Trophy, and age-group tournaments).

Player evaluation has shifted from basic career aggregates (total runs, total wickets) to hyper-specific, phase-level analysis — for example, strike rate in specific over ranges, boundary percentage, or dot-ball ratio in the powerplay. Selectors and franchises increasingly look for these performance profiles when shortlisting players.

While platforms like ESPNcricinfo capture granular, ball-by-ball data, it is locked behind rigid dashboards and static leaderboards. Extracting custom, multi-dimensional cuts currently requires SQL or Python skills that scouts, coaches, and selectors typically do not have.

---

## 3. Problem Statement

- **Rigid Dashboards & Siloed Data**: Existing platforms present data in static tables; users cannot cross-filter without manual spreadsheet work.
- **The Technical Bottleneck**: Scouts know what questions they want answered but cannot translate them into queries.
- **High Time-to-Insight**: Every custom request depends on a data engineer, creating bottlenecks in selection decisions.
- **Missed Talent**: Complex queries are hard to run, so scouts rely on season-level averages and miss high-impact players.
- **Over-Reliance on Subjective Scouting**: When data is inaccessible, decision-makers default to the "eye test," prone to bias.

---

## 4. Business Objectives

1. Enable selectors, coaches, and scouts to query player and match performance data using natural language, with no SQL knowledge.
2. Reduce time-to-insight for a custom scouting query from days to seconds.
3. Surface "hidden gem" players by making granular data cuts as accessible as season averages.
4. Provide a consistent, auditable, repeatable analytical process, reducing reliance on subjective scouting.

---

## 5. Scope

### 5.1 In Scope (Proof of Concept)

- Domestic tournaments: Ranji Trophy, Syed Mushtaq Ali Trophy (T20), Vijay Hazare Trophy (ODI), First Class formats
- Male and female players across age groups: Senior, U25, U19, U16
- Ball-by-ball delivery-level data supporting phase-wise analysis (powerplay / middle / death overs)
- Fielding statistics (catches, stumpings, run outs) and extras tracking (wides, no balls, byes, leg byes)
- Conversational interface where users type questions in plain English and receive data-backed answers
- Representative, statistically realistic synthetic dataset for the PoC stage
- Python CLI prototype (Phase 1, complete) + web-based chat interface (Phase 2, in progress)

### 5.2 Out of Scope (For This PoC)

- Live/real-time match data ingestion
- Integration with paid third-party data providers
- Video or visual scouting tools
- Mobile app delivery
- Multi-association deployment (architecture allows it, but not included in this phase)

---

## 6. Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI (Python) + PostgreSQL 18 |
| **LLM Provider** | Groq API — Llama 3.3 70B (free tier) |
| **LLM Config** | Temperature 0.0 (deterministic), max_tokens 1024, JSON response format |
| **Frontend** | React 18 + Vite 6 (dark cricket theme, amber/teal/purple accents) |
| **Web Server** | Nginx with self-signed SSL (TLS 1.2/1.3) |
| **Public Access** | ngrok (free tier for PoC; production uses custom domain) |
| **SQL Validation** | sqlglot (SELECT-only enforcement) |
| **Database Manager** | TablePlus |
| **Version Control** | GitHub |

---

## 7. Key Changes from Previous Version (v2.0 → v2.1)

### LLM Migration: OpenAI → Groq
- **Previous**: GPT-4o Mini (OpenAI API)
- **Current**: Llama 3.3 70B via Groq API
- **Rationale**: Groq delivers deterministic SQL generation (temperature 0.0), no hallucination, free tier without credit card requirement, and superior performance for structured output (JSON).

### Database Management
- Simplified from EDB installer workflow to TablePlus for direct PostgreSQL management
- PostgreSQL 18 running locally on macOS (Apple Silicon M-series)

### Data
- Synthetic dataset: 235 players, 88 matches, ~19.5K ball-by-ball deliveries
- 11 domestic tournaments (2024-25 season)
- Calibrated to real domestic cricket benchmarks (strike rates, economy rates, dismissal patterns)

### Views & Analytics
Seven pre-built SQL views for instant aggregations:
- `batting_summary` — batting stats per player/tournament
- `bowling_summary` — bowling stats per player/tournament
- `phase_batting` — batting by phase (powerplay/middle/death)
- `phase_bowling` — bowling by phase
- `fielding_summary` — catches, stumpings, run outs
- `extras_summary` — wides, no balls, byes, leg byes
- `bowler_discipline` — indiscipline metrics (wides + no balls)

---

## 8. Success Criteria

1. Natural language queries are translated to correct SQL with >95% accuracy (validated by Sujit Kane)
2. All analytics views return correct aggregates for representative test cases
3. Web interface is responsive and accessible across browsers (Chrome, Safari, Firefox) on desktop and tablet
4. Groq API usage remains within free tier limits (1,000 requests/day, 30 requests/minute)
5. Query latency is <3 seconds for typical scouting queries (including API call + DB execution)
6. No sensitive data leakage; read-only connection enforced at the database level

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| **Groq API Rate Limits** | Free tier has 1,000 req/day and 30 req/min limits. Monitor usage; upgrade to paid tier if exceeded. |
| **LLM Hallucination** | Deterministic SQL (temp 0.0) + sqlglot validation enforce only SELECT queries on real tables. Intent classifier rejects out-of-scope questions. |
| **Data Quality** | Synthetic data is calibrated to real domestic cricket. Plan to replace with real, licensed data in Phase 2. |
| **Deployment** | ngrok is temporary. Production deployment requires custom domain, Let's Encrypt SSL, and cloud hosting (architecture agnostic). |
| **Schema Evolution** | Views are versioned. Schema changes are backward-compatible with existing queries. |

---

## 10. Constraints & Assumptions

- **Synthetic Dataset**: Real match data from ESPNcricinfo is not available due to ToS restrictions. Synthetic data is used for PoC validation.
- **Groq Free Tier**: Requires monitoring to stay within rate limits. Production uses paid tier or alternative LLM.
- **No Direct Scraping**: ESPNcricinfo data is not scraped; only synthetic data is used.
- **PoC Deployment**: ngrok provides temporary public access. Production requires a real domain and Let's Encrypt SSL.
- **Single-Association PoC**: Architecture allows multi-association rollout, but this phase targets one association only.

---

## 11. Stakeholders

| Stakeholder | Role |
|------------|------|
| **Sujit Kane** | Business Owner & Domain Expert (Cricket) — validates accuracy, defines success criteria |
| **Anshul Dhote** | Developer — builds and maintains the system |
| **Sarang** | Colleague — provided platform evaluation input (Azure vs. GCP) |
| **Cricket Association** | End-User Organization — provides feedback at each milestone |

---

## 12. Document Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Prepared By** | Anshul Dhote | | 2026-08-08 |
| **Reviewed By** | Sujit Kane | | ______ |

---

**Version History**
- v2.0 (2026-07-21): Initial BRD with GPT-4o Mini
- v2.1 (2026-08-08): Updated tech stack — Groq API, TablePlus, synthetic data specs
