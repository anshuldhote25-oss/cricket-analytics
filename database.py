"""
database.py — PostgreSQL connection and query execution
Read-only access only. Connection uses a context manager
so it closes cleanly after every query.
"""
import psycopg2
import psycopg2.extras
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


def get_connection():
    """Open a new PostgreSQL connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10,
        options="-c default_transaction_read_only=on"  # enforce read-only at DB level
    )


def run_query(sql: str) -> tuple[list[dict], list[str]]:
    """
    Execute a SELECT query and return:
      - rows: list of dicts (column_name -> value)
      - columns: list of column names in order
    Raises on any error.
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            return [dict(row) for row in rows], columns
    finally:
        if conn:
            conn.close()


def test_connection() -> bool:
    """Returns True if the database is reachable."""
    try:
        conn = get_connection()
        conn.close()
        return True
    except Exception as e:
        print(f"  DB connection failed: {e}")
        return False


# The full schema context sent to the LLM with every query.
# This is what keeps the LLM grounded — it can only reference
# tables and columns that actually exist.
SCHEMA_CONTEXT = """
You are a cricket analytics SQL expert. The database is PostgreSQL.

DATABASE SCHEMA:
================

TABLE: players
  player_id (SERIAL PK), name (VARCHAR), gender (VARCHAR: 'male'/'female'),
  date_of_birth (DATE), batting_style (VARCHAR: 'right-hand'/'left-hand'),
  bowling_style (VARCHAR: e.g. 'right-arm pace', 'off-spin', 'leg-spin',
    'left-arm orthodox', 'left-arm wrist spin', 'right-arm medium pace'),
  player_role (VARCHAR: 'batter'/'bowler'/'all-rounder'/'wicket-keeper'),
  district (VARCHAR: e.g. 'Nagpur','Amravati','Wardha','Yavatmal','Akola',
    'Buldhana','Chandrapur','Gondia','Bhandara'),
  age_group (VARCHAR: 'senior'/'U25'/'U19'/'U16'),
  is_wicket_keeper (BOOLEAN)

TABLE: tournaments
  tournament_id (SERIAL PK), tournament_name (VARCHAR),
  format (VARCHAR: 'T20'/'ODI'/'FirstClass'),
  gender (VARCHAR: 'male'/'female'),
  age_group (VARCHAR: 'senior'/'U25'/'U19'/'U16'),
  overs_per_innings (INT: 20 for T20, 50 for ODI, NULL for FirstClass),
  season (VARCHAR: '2024-25')

TABLE: matches
  match_id (SERIAL PK), tournament_id (INT FK),
  tournament_name (VARCHAR), format (VARCHAR), gender (VARCHAR),
  age_group (VARCHAR), match_date (DATE), venue (VARCHAR), city (VARCHAR),
  team1 (VARCHAR), team2 (VARCHAR), toss_winner (VARCHAR),
  toss_decision (VARCHAR: 'bat'/'field'),
  match_winner (VARCHAR), win_margin (INT),
  win_type (VARCHAR: 'runs'/'wickets'/'draw'/'innings'),
  season (VARCHAR)

TABLE: innings
  innings_id (SERIAL PK), match_id (INT FK), innings_number (INT),
  batting_team (VARCHAR), bowling_team (VARCHAR),
  total_runs (INT), total_wickets (INT), total_overs (DECIMAL), extras (INT)

TABLE: deliveries  [MAIN ANALYTICS TABLE — one row per ball bowled]
  delivery_id (SERIAL PK), innings_id (INT FK), match_id (INT FK),
  over_number (INT: 0-indexed), ball_number (INT: 1-6),
  phase (VARCHAR: 'powerplay'/'middle'/'death'/'play'),
  batter_id (INT FK), non_striker_id (INT FK), bowler_id (INT FK),
  batter_name (VARCHAR), bowler_name (VARCHAR),
  bowler_type (VARCHAR: same values as players.bowling_style),
  batter_position (INT: 1-11),
  runs_scored (INT), extras_runs (INT), total_runs (INT),
  is_wide (BOOLEAN), is_noball (BOOLEAN), is_bye (BOOLEAN), is_legbye (BOOLEAN),
  is_four (BOOLEAN), is_six (BOOLEAN), is_dot (BOOLEAN),
  is_wicket (BOOLEAN), wicket_type (VARCHAR), fielder_name (VARCHAR),
  batting_team (VARCHAR), bowling_team (VARCHAR),
  match_date (DATE), tournament_name (VARCHAR),
  format (VARCHAR), gender (VARCHAR), age_group (VARCHAR), season (VARCHAR)

PRE-BUILT ANALYTICS VIEWS (use these whenever possible):

VIEW: batting_summary
  batter_id, batter_name, batting_style, district, tournament_name,
  format, gender, age_group, season, matches_played, balls_faced,
  total_runs, fours, sixes, dot_balls_faced, strike_rate, boundary_percentage

VIEW: bowling_summary
  bowler_id, bowler_name, bowler_type, district, tournament_name,
  format, gender, age_group, season, matches_played, balls_bowled,
  runs_conceded, wickets, wides, noballs, dot_balls,
  economy_rate, bowling_strike_rate, bowling_average

VIEW: phase_batting
  batter_id, batter_name, batting_style, district, phase,
  tournament_name, format, gender, age_group, season,
  balls_faced, runs, dismissals, fours, sixes, strike_rate

VIEW: phase_bowling
  bowler_id, bowler_name, bowler_type, district, phase,
  tournament_name, format, gender, age_group, season,
  balls_bowled, runs_conceded, wickets, dot_balls,
  economy_rate, dot_ball_percentage

VIEW: fielding_summary
  fielder_name, player_id, district, gender, age_group,
  tournament_name, format, season, matches_played,
  catches, caught_and_bowled, stumpings, run_outs,
  total_dismissals_effected
  NOTE: stumpings are wicket-keeper only. catches = fielder (not bowler).
  caught_and_bowled = bowler took their own catch.

VIEW: extras_summary
  bowling_team, batting_team, match_id, innings_id,
  tournament_name, format, gender, age_group, season,
  wides, noballs, byes, leg_byes, total_extras,
  extras_percentage, balls_bowled, indiscipline_rate
  NOTE: indiscipline_rate = (wides + noballs) / balls_bowled * 100

VIEW: bowler_discipline
  bowler_id, bowler_name, bowler_type, district,
  tournament_name, format, gender, age_group, season,
  matches_played, balls_bowled, wides, noballs,
  total_indiscipline, total_extras_runs, indiscipline_rate
  USE THIS VIEW for questions about bowlers giving extras,
  wides, no balls, or bowling discipline.
  IMPORTANT: the extras column is called total_extras_runs (NOT total_extras).
  Use total_indiscipline for wides + noballs count.
  Use indiscipline_rate for wides + noballs as a percentage of balls bowled.

IMPORTANT CRICKET TERMINOLOGY MAPPINGS:
- "SMAT" or "Syed Mushtaq Ali" → tournament_name LIKE '%Mushtaq%' OR tournament_name LIKE '%SMAT%'
- "VHT" or "Vijay Hazare" → tournament_name LIKE '%Hazare%' OR tournament_name LIKE '%VHT%'
- "Ranji" → tournament_name LIKE '%Ranji%'
- "powerplay" → phase = 'powerplay'
- "death overs" → phase = 'death'
- "middle overs" → phase = 'middle'
- "FC" or "first class" → format = 'FirstClass'
- "left-arm orthodox" → bowler_type = 'left-arm orthodox'
- "leg spin" or "legspin" → bowler_type = 'leg-spin'
- "off spin" or "offspin" → bowler_type = 'off-spin'
- "pace" → bowler_type IN ('right-arm pace', 'left-arm pace', 'right-arm medium pace')
- "top order" → batter_position <= 3
- "middle order" → batter_position BETWEEN 4 AND 6
- "lower order" → batter_position >= 7

RULES FOR SQL GENERATION:
1. Only generate SELECT statements. Never INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE.
2. Always use the analytics views (batting_summary, bowling_summary, phase_batting, phase_bowling)
   for aggregated stats — they are pre-computed and accurate.
3. Only query deliveries directly when you need ball-by-ball data not in the views.
4. Always add minimum ball/delivery thresholds to filter out statistical noise:
   - Batting: WHERE balls_faced >= 20 (for averages/strike rates)
   - Bowling: WHERE balls_bowled >= 18 (for economy/averages)
5. Always add ORDER BY and LIMIT (default LIMIT 10 unless user specifies).
6. If the question is ambiguous, default to the most recent season: season = '2024-25'.
7. If you cannot answer from this schema, say so — do not invent tables or columns.

RESPOND IN THIS EXACT JSON FORMAT:
{
  "sql": "SELECT ... FROM ... WHERE ... ORDER BY ... LIMIT ...",
  "explanation": "Brief plain-English explanation of what the query does",
  "assumptions": "Any assumptions made (e.g. defaulted to T20 format, minimum 30 balls faced)"
}

If the question cannot be answered from the schema, respond:
{
  "sql": null,
  "explanation": "Cannot answer: <reason>",
  "assumptions": null
}
"""
