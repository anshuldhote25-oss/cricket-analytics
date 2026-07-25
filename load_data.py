"""
load_data.py — Cricket Analytics DB Data Loader
================================================
Loads all CSV files into PostgreSQL in the correct order,
handling data types properly. Run this once after schema.sql.

Usage:
    python3 load_data.py

Make sure your .env file is configured before running.
"""
import os
import csv
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "cricket_analytics_db"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
}

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def connect():
    return psycopg2.connect(**DB_CONFIG)

def to_int(v):
    if v is None or str(v).strip() == "": return None
    try: return int(float(str(v).strip()))
    except: return None

def to_float(v):
    if v is None or str(v).strip() == "": return None
    try: return float(str(v).strip())
    except: return None

def to_bool(v):
    if v is None or str(v).strip() == "": return False
    return str(v).strip().lower() in ("true", "1", "yes", "t")

def to_str(v):
    if v is None or str(v).strip() == "": return None
    return str(v).strip()

def to_date(v):
    if v is None or str(v).strip() == "": return None
    try: return datetime.strptime(str(v).strip(), "%Y-%m-%d").date()
    except: return None

def read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV not found: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def ok(msg): print(f"  [OK] {msg}")
def fail(msg): print(f"  [FAIL] {msg}")


def load_tournaments(conn):
    rows = read_csv("tournaments.csv")
    sql = """INSERT INTO tournaments (tournament_id, tournament_name, format, gender,
             age_group, overs_per_innings, season)
             VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tournament_id) DO NOTHING"""
    data = [(to_int(r["tournament_id"]), to_str(r["tournament_name"]), to_str(r["format"]),
             to_str(r["gender"]), to_str(r["age_group"]), to_int(r.get("overs_per_innings")),
             to_str(r["season"])) for r in rows]
    with conn.cursor() as cur: cur.executemany(sql, data)
    conn.commit()
    ok(f"tournaments  — {len(data)} rows")


def load_players(conn):
    rows = read_csv("players.csv")
    sql = """INSERT INTO players (player_id, name, gender, date_of_birth, batting_style,
             bowling_style, player_role, district, age_group, is_wicket_keeper)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (player_id) DO NOTHING"""
    data = [(to_int(r["player_id"]), to_str(r["name"]), to_str(r["gender"]),
             to_date(r["date_of_birth"]), to_str(r["batting_style"]),
             to_str(r.get("bowling_style")), to_str(r.get("player_role")),
             to_str(r.get("district")), to_str(r.get("age_group")),
             to_bool(r.get("is_wicket_keeper", False))) for r in rows]
    with conn.cursor() as cur: cur.executemany(sql, data)
    conn.commit()
    ok(f"players      — {len(data)} rows")


def load_matches(conn):
    rows = read_csv("matches.csv")
    sql = """INSERT INTO matches (match_id, tournament_id, tournament_name, format, gender,
             age_group, match_date, venue, city, team1, team2, toss_winner, toss_decision,
             match_winner, win_margin, win_type, season)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
             ON CONFLICT (match_id) DO NOTHING"""
    data = [(to_int(r["match_id"]), to_int(r.get("tournament_id")),
             to_str(r["tournament_name"]), to_str(r["format"]), to_str(r["gender"]),
             to_str(r["age_group"]), to_date(r["match_date"]), to_str(r.get("venue")),
             to_str(r.get("city")), to_str(r["team1"]), to_str(r["team2"]),
             to_str(r.get("toss_winner")), to_str(r.get("toss_decision")),
             to_str(r.get("match_winner")), to_int(r.get("win_margin")),
             to_str(r.get("win_type")), to_str(r["season"])) for r in rows]
    with conn.cursor() as cur: cur.executemany(sql, data)
    conn.commit()
    ok(f"matches      — {len(data)} rows")


def load_innings(conn):
    rows = read_csv("innings.csv")
    sql = """INSERT INTO innings (innings_id, match_id, innings_number, batting_team,
             bowling_team, total_runs, total_wickets, total_overs, extras)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (innings_id) DO NOTHING"""
    data = [(to_int(r["innings_id"]), to_int(r["match_id"]), to_int(r["innings_number"]),
             to_str(r["batting_team"]), to_str(r["bowling_team"]),
             to_int(r.get("total_runs", 0)), to_int(r.get("total_wickets", 0)),
             to_float(r.get("total_overs", 0)), to_int(r.get("extras", 0))) for r in rows]
    with conn.cursor() as cur: cur.executemany(sql, data)
    conn.commit()
    ok(f"innings      — {len(data)} rows")


def load_deliveries(conn):
    rows = read_csv("deliveries.csv")
    sql = """INSERT INTO deliveries (delivery_id, innings_id, match_id, over_number,
             ball_number, phase, batter_id, non_striker_id, bowler_id, batter_name,
             bowler_name, bowler_type, batter_position, runs_scored, extras_runs,
             total_runs, is_wide, is_noball, is_bye, is_legbye, is_four, is_six,
             is_dot, is_wicket, wicket_type, fielder_name, batting_team, bowling_team,
             match_date, tournament_name, format, gender, age_group, season)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                     %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
             ON CONFLICT (delivery_id) DO NOTHING"""
    data = [(to_int(r["delivery_id"]), to_int(r["innings_id"]), to_int(r["match_id"]),
             to_int(r["over_number"]), to_int(r["ball_number"]), to_str(r["phase"]),
             to_int(r.get("batter_id")), to_int(r.get("non_striker_id")),
             to_int(r.get("bowler_id")), to_str(r.get("batter_name")),
             to_str(r.get("bowler_name")), to_str(r.get("bowler_type")),
             to_int(r.get("batter_position")), to_int(r.get("runs_scored", 0)),
             to_int(r.get("extras_runs", 0)), to_int(r.get("total_runs", 0)),
             to_bool(r.get("is_wide")), to_bool(r.get("is_noball")),
             to_bool(r.get("is_bye")), to_bool(r.get("is_legbye")),
             to_bool(r.get("is_four")), to_bool(r.get("is_six")),
             to_bool(r.get("is_dot")), to_bool(r.get("is_wicket")),
             to_str(r.get("wicket_type")), to_str(r.get("fielder_name")),
             to_str(r.get("batting_team")), to_str(r.get("bowling_team")),
             to_date(r.get("match_date")), to_str(r.get("tournament_name")),
             to_str(r.get("format")), to_str(r.get("gender")),
             to_str(r.get("age_group")), to_str(r.get("season"))) for r in rows]
    total = len(data)
    with conn.cursor() as cur:
        for i in range(0, total, 1000):
            cur.executemany(sql, data[i:i+1000])
            conn.commit()
            pct = min(100, int((i+1000)/total*100))
            print(f"\r  ...  deliveries  — {pct}% ({min(i+1000,total)}/{total})", end="", flush=True)
    print(f"\r  [OK] deliveries  — {total} rows           ")


def main():
    print("\n" + "="*52)
    print("  Cricket Analytics DB — Data Loader")
    print("="*52)
    print(f"\n  Database : {DB_CONFIG['dbname']}")
    print(f"  Host     : {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"  Data dir : {DATA_DIR}\n")

    if not os.path.isdir(DATA_DIR):
        fail(f"Data directory not found: {DATA_DIR}")
        print("  Create a 'data/' folder and place your CSV files in it.")
        return

    print("  Connecting...", end=" ")
    try:
        conn = connect()
        print("connected\n")
    except Exception as e:
        fail(f"Connection failed: {e}")
        return

    print("  Clearing existing data...")
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE deliveries, innings, matches, players, tournaments RESTART IDENTITY CASCADE")
        conn.commit()
        ok("existing data cleared\n")
    except Exception as e:
        fail(f"Could not clear data: {e}")
        conn.close()
        return

    print("  Loading tables...")
    for name, loader in [
        ("tournaments", load_tournaments),
        ("players",     load_players),
        ("matches",     load_matches),
        ("innings",     load_innings),
        ("deliveries",  load_deliveries),
    ]:
        try:
            loader(conn)
        except FileNotFoundError as e:
            fail(str(e))
            conn.close()
            return
        except Exception as e:
            fail(f"Error loading {name}: {e}")
            conn.rollback()
            conn.close()
            return

    conn.close()
    print("\n" + "="*52)
    print("  All data loaded successfully!")
    print("="*52)
    print("\n  Run python3 main.py to start the agent.\n")


if __name__ == "__main__":
    main()
