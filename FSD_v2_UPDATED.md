# Functional Specification Document

## Conversational AI for Cricket Analytics

*Democratizing Data-Driven Scouting in Indian Domestic Leagues*

**Proof of Concept**

| Aspect | Details |
|--------|---------|
| **Document Type** | Functional Specification Document (FSD) |
| **Project** | AI-Powered Cricket Scouting & Analytics Agent |
| **Related Document** | Business Requirement Document v2.1 |
| **Prepared By** | Anshul Dhote |
| **Reviewed By** | Sujit Kane |
| **Version** | 2.1 |
| **Status** | Updated - Tech Stack Revised (Groq API) |
| **Date** | 2026-08-08 |

---

## 1. Purpose of Document

This Functional Specification Document (FSD) describes how the AI-Powered Cricket Scouting and Analytics Agent behaves from a user's perspective. It translates the business objectives in the BRD into specific functional requirements, input/output behavior, and business rules, across both delivery phases: the Python CLI prototype (Phase 1, complete) and the web-based chat interface (Phase 2, in progress).

---

## 2. Scope of This Document

This document covers functional behavior only — what the system does and how it responds to user input. Non-functional aspects (technology stack, infrastructure, data flow, security) are covered in the Architecture Document.

**Two Delivery Phases:**
- **Phase 1**: Python CLI Prototype (complete) — command-line interface that validates natural language-to-SQL translation and answers from the database
- **Phase 2**: Web Chat Interface (in progress) — browser-based conversational UI deployed via FastAPI and Nginx, accessible over the network without requiring local Python setup

---

## 3. User Roles

| Role | Description |
|------|-------------|
| **Scout / Analyst (Phase 1)** | Technical or semi-technical user who runs the Python prototype directly, reviews raw query output, and validates accuracy against known data |
| **Selector / Coach (Phase 2)** | Non-technical end user who interacts only through the web chat interface; types questions in plain English and reads results, leaderboards, or summaries |
| **Administrator** | Responsible for refreshing the dataset, monitoring query logs, and managing system configuration (Groq API keys, database credentials) |

---

## 4. Functional Requirements Overview

Functional requirements are grouped into five areas:

1. **Natural Language Query Input** — accepting freeform questions
2. **Query Translation (NL → SQL)** — LLM-powered SQL generation
3. **Query Execution & Validation** — safe, read-only execution
4. **Results Presentation** — returning data in decision-ready format
5. **Conversation Context & History** — maintaining state across queries (Phase 2)

---

## 5. FR-1: Natural Language Query Input

### 5.1 Description

The system accepts questions typed in plain English (or Hinglish-influenced phrasing common in Indian cricket conversation) describing the player performance data the user wants to see.

### 5.2 Functional Rules

- The system shall accept free-text input with no required syntax, keywords, or query language.
- The system shall support questions that combine multiple filtering dimensions: format, gender, age group, tournament, match phase, bowling type, batting position, statistical thresholds, fielding stats (catches, stumpings, run outs), and bowling discipline (wides, no balls).
- The system shall support both specific player lookups ("show me [player]'s stats in the powerplay") and open-ended leaderboard-style queries ("top 10 batters by strike rate in the death overs").
- **Phase 1**: input via Python script prompt or notebook cell.
- **Phase 2**: input via chat text box in the web interface.
- The system shall display example questions to non-technical users, reducing cognitive load.

---

## 6. FR-2: Query Translation (Natural Language → SQL)

### 6.1 Description

The system uses a Large Language Model (LLM) — Groq's Llama 3.3 70B — to convert the user's natural language question into a syntactically correct, schema-aware SQL query against the cricket analytics database.

### 6.2 Functional Rules

- The LLM shall be provided with the full database schema (tables, columns, views, aliases) as context, ensuring generated SQL references only valid entities.
- The system shall prefer querying pre-built analytics views (`batting_summary`, `bowling_summary`, `phase_batting`, `phase_bowling`, `fielding_summary`, `extras_summary`, `bowler_discipline`) for aggregated stats, ensuring consistent and pre-validated logic.
- The system shall correctly map cricket terminology to schema fields:
  - "powerplay" → `phase = 'powerplay'`
  - "left-arm orthodox" → `bowler_type = 'left-arm orthodox'`
  - "SMAT" or "Syed Mushtaq Ali" → `tournament_name LIKE '%Mushtaq%'`
  - "Ranji Trophy" → `tournament_name LIKE '%Ranji%'`
  - "Vijay Hazare Trophy" or "VHT" → `tournament_name LIKE '%Hazare%'`
  - "top order" → `batter_position <= 3`
  - "middle order" → `batter_position BETWEEN 4 AND 6`
  - "lower order" → `batter_position >= 7`
  - "death overs" → `phase = 'death'`
  - "first class" or "FC" → `format = 'FirstClass'`
- The system shall handle ambiguous or under-specified questions by applying sensible defaults (e.g., defaulting to the most recent season: `season = '2024-25'`) and shall state any assumptions made in its response.
- The system shall reject or safely decline to translate questions falling outside the schema scope (e.g., requests unrelated to cricket data) rather than generating invalid or unrelated queries.
- **LLM Configuration**: Llama 3.3 70B via Groq API with temperature 0.0 (deterministic), max_tokens 1024, response_format JSON.
- The system shall return JSON in this exact format:
  ```json
  {
    "sql": "SELECT ... FROM ... WHERE ... ORDER BY ... LIMIT ...",
    "explanation": "Brief plain-English explanation of what the query does",
    "assumptions": "Any assumptions made (e.g., 'defaulted to T20 format, minimum 30 balls faced')"
  }
  ```
- If a question cannot be answered from the schema, return:
  ```json
  {
    "sql": null,
    "explanation": "Cannot answer: <reason>",
    "assumptions": null
  }
  ```

---

## 7. FR-3: Query Execution & Validation

### 7.1 Description

Once SQL is generated, the system executes it against the PostgreSQL database in a controlled, read-only manner and validates the result before presenting it to the user.

### 7.2 Functional Rules

- The system shall execute only read (SELECT) operations. No natural language input shall trigger INSERT, UPDATE, DELETE, or DDL statements.
- The system shall validate that generated SQL references only existing tables/columns using `sqlglot` library (SELECT-only enforcement) before execution.
- The system shall handle and report query errors gracefully with user-friendly messages rather than crashing or returning blank results.
- The system shall apply reasonable row-limit safeguards on exploratory queries (default LIMIT 10 unless user specifies otherwise).
- The system shall log each natural language question, the SQL generated, the explanation, assumptions, and execution outcome to a local log file or database, supporting accuracy review and debugging during PoC validation.
- Database connection is read-only at the PostgreSQL level (`default_transaction_read_only=on`), providing defense-in-depth against accidental or malicious writes.

---

## 8. FR-4: Results Presentation

### 8.1 Description

Query results are returned to the user in a clear, decision-ready format appropriate to the question asked.

### 8.2 Functional Rules

- **Phase 1 (complete)**: Results presented as formatted tabular output in the Python CLI — player names, stats, and rankings in a clean ASCII table.
- **Phase 2 (in progress)**: Results presented within the browser chat interface as:
  - A natural-language summary of the findings
  - A formatted data table with sortable columns
  - Leaderboard visualizations with 🥇🥈🥉 medals for top 3 rows
  - A "Show SQL" toggle to display the underlying query
  - A "Download CSV" option for further analysis
- Where a query produces no matching results, the system shall state this clearly and suggest a possible reason (e.g., "No players matched this filter combination in the current dataset. Try adjusting: tournament, format, or minimum statistics threshold").
- The system shall display the Groq LLM explanation and any assumptions stated by the AI, building user confidence in the result.

---

## 9. FR-5: Conversation Context & History

### 9.1 Description (Phase 2)

The web chat interface maintains a conversation history and context across multiple queries, allowing users to refine results interactively.

### 9.2 Functional Rules

- The chat interface shall display all prior queries and results in a scrollable conversation view.
- Users shall be able to ask follow-up questions that refine or build on prior queries (e.g., "show me the same stats but for U19 players only").
- The system shall store session history in the browser (localStorage) for the current session only; no persistent server-side history is maintained in PoC.
- Users shall be able to clear the conversation history and start fresh.
- Example questions shall appear in a collapsible drawer, accessible at any time.

---

## 10. FR-6: Browse Data (Direct View Access)

### 10.1 Description

A "Browse Data" modal allows users to directly query analytics views without using natural language, bypassing the AI entirely.

### 10.2 Functional Rules

- Users shall be able to select a view (batting_summary, bowling_summary, phase_batting, phase_bowling, fielding_summary, extras_summary, bowler_discipline) from a dropdown.
- The system shall display all rows from the selected view in a paginated, sortable, and filterable table.
- This feature is for power users and administrators who want to inspect raw aggregated data without relying on the LLM.

---

## 11. Explicit Non-Goals (Functional)

- The system does not support DELETE, UPDATE, or INSERT operations via natural language or direct query.
- The system does not support multi-turn context where a previous result is automatically fed into the next query (manual refinement only).
- The system does not support charting or visualization beyond simple leaderboards in Phase 2.
- The system does not support voice input or voice output.
- The system does not support multi-language queries (English/Hinglish only).

---

## 12. Acceptance Criteria

1. ✅ Natural language queries are correctly translated to SQL with >95% accuracy (validated by Sujit Kane on representative test cases).
2. ✅ All seven analytics views (`batting_summary`, `bowling_summary`, `phase_batting`, `phase_bowling`, `fielding_summary`, `extras_summary`, `bowler_discipline`) return correct aggregates for sample queries.
3. ✅ Web interface is responsive and usable on desktop and tablet (Chrome, Safari, Firefox).
4. ✅ Query execution completes in <3 seconds for typical scouting questions (including Groq API latency + PostgreSQL query time).
5. ✅ Groq API usage stays within free tier limits (1,000 requests/day, 30 requests/minute).
6. ✅ Read-only enforcement is active; any attempt to modify data is rejected at the database level.
7. ✅ Error messages are clear and actionable for end users.
8. ✅ Conversation history and example questions are functional in Phase 2.

---

## 13. API Endpoints (Phase 2 — FastAPI)

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | `/api/query` | Send a natural language question, receive SQL, explanation, and results | None (PoC) |
| GET | `/api/health` | Check database connection status | None |
| GET | `/api/browse/{view_name}` | Direct view query (bypass AI) | None |
| GET | `/api/examples` | Return example questions for UI | None |
| GET | `/` | Serve React frontend (static files) | None |

---

## 14. Data Specifications

### Datasets Included

- **Players**: 235 players (male + female, Senior/U25/U19/U16)
- **Tournaments**: 11 domestic tournaments (Ranji, SMAT, VHT, U19, U16, Women's)
- **Matches**: 88 matches across all formats (T20, ODI, FirstClass)
- **Deliveries**: ~19,500 ball-by-ball records
- **Season**: 2024-25
- **Data Type**: Synthetic, calibrated to real domestic cricket benchmarks

### Example Queries (Non-Exhaustive)

- "Top 10 T20 batters by strike rate"
- "Left-arm orthodox bowlers with economy rate under 7 in Ranji Trophy"
- "Best fielders in SMAT tournament"
- "Powerplay batting stats for U19 female players"
- "Bowlers with most indiscipline (wides + no balls) in death overs"
- "Catches taken by district (Nagpur, Amravati, etc.)"

---

## 15. Document Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Prepared By** | Anshul Dhote | | 2026-08-08 |
| **Reviewed By** | Sujit Kane | | ______ |

---

**Version History**
- v2.0 (2026-07-21): Initial FSD with GPT-4o Mini, Phase 1 & 2 design
- v2.1 (2026-08-08): Updated LLM to Groq (Llama 3.3 70B), refined accuracy criteria, added direct view browsing, finalized API endpoints
