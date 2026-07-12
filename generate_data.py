import random
import json
from datetime import date, timedelta
from dataclasses import dataclass, field
from typing import List, Optional
import csv
import os

random.seed(42)  # reproducible data


OUTPUT_DIR = "./output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# How many matches to generate per tournament (keep small for PoC)
MATCHES_PER_TOURNAMENT = 8

VCA_DISTRICTS = [
    "Nagpur", "Amravati", "Wardha", "Yavatmal",
    "Chandrapur", "Gadchiroli", "Washim", "Akola",
    "Bhandara", "Gondia", "Buldhana"
]


MALE_FIRST_NAMES = [
    "Akshay", "Rahul", "Sanjay", "Vikas", "Rohit", "Amit",
    "Ganesh", "Nikhil", "Aditya", "Pratik", "Suraj", "Kiran",
    "Mayur", "Vaibhav", "Aniket", "Tushar", "Shubham", "Yash",
    "Pranav", "Siddhesh", "Rushikesh", "Omkar", "Atharva", "Harsh",
    "Devraj", "Samarth", "Lakshya", "Arjun", "Vedant", "Kunal"
]

FEMALE_FIRST_NAMES = [
    "Punam", "Anjali", "Priya", "Sneha", "Pooja", "Neha",
    "Shraddha", "Dipika", "Swati", "Manasi", "Rutuja", "Sonali",
    "Anushka", "Gauri", "Pallavi", "Vedika", "Tanvi", "Siddhi",
    "Komal", "Rasika", "Vaishnavi", "Pradnya", "Apurva", "Nikita"
]

SURNAMES = [
    "Wakhare", "Satish", "Raut", "Sarwate", "Jadhav", "Thakur",
    "Shende", "Bawne", "Khadse", "Meshram", "Nagpure", "Dhote",
    "Kolhe", "Gawai", "Ingle", "Borkar", "Chaudhari", "Deshmukh",
    "Patil", "More", "Deshpande", "Kulkarni", "Joshi", "Nair",
    "Bhatt", "Sharma", "Verma", "Singh", "Kumar", "Rao"
]


TOURNAMENTS = [
    # Senior Male
    {"name": "Ranji Trophy",             "format": "FirstClass", "gender": "male",   "age_group": "senior", "overs": None},
    {"name": "Syed Mushtaq Ali Trophy",  "format": "T20",        "gender": "male",   "age_group": "senior", "overs": 20},
    {"name": "Vijay Hazare Trophy",      "format": "ODI",        "gender": "male",   "age_group": "senior", "overs": 50},

    # U25 Male
    {"name": "Col CK Nayudu Trophy",     "format": "FirstClass", "gender": "male",   "age_group": "U25",    "overs": None},

    # U19 Male
    {"name": "Vinoo Mankad Trophy",      "format": "ODI",        "gender": "male",   "age_group": "U19",    "overs": 50},
    {"name": "U19 Men T20",              "format": "T20",        "gender": "male",   "age_group": "U19",    "overs": 20},

    # U16 Male
    {"name": "Vijay Merchant Trophy",    "format": "FirstClass", "gender": "male",   "age_group": "U16",    "overs": None},

    # Senior Female
    {"name": "Senior Women T20",         "format": "T20",        "gender": "female", "age_group": "senior", "overs": 20},
    {"name": "Women One Day Trophy",     "format": "ODI",        "gender": "female", "age_group": "senior", "overs": 50},

    # U19 Female
    {"name": "U19 Women T20",            "format": "T20",        "gender": "female", "age_group": "U19",    "overs": 20},

    # U16 Female
    {"name": "U16 Women T20",            "format": "T20",        "gender": "female", "age_group": "U16",    "overs": 20},
]


BOWLING_STYLES = [
    "right-arm pace",
    "right-arm medium pace",
    "left-arm pace",
    "off-spin",
    "leg-spin",
    "left-arm orthodox",
    "left-arm wrist spin",
]

BOWLING_STYLE_WEIGHTS = [0.25, 0.20, 0.12, 0.18, 0.10, 0.10, 0.05]


VENUES = [
    ("VCA Stadium Jamtha", "Nagpur"),
    ("Vidarbha Cricket Association Ground", "Nagpur"),
    ("Amravati Cricket Ground", "Amravati"),
    ("Wardha District Ground", "Wardha"),
    ("Akola Cricket Ground", "Akola"),
    ("Chandrapur Sports Complex", "Chandrapur"),
]


VCA_TEAMS = [
    "Nagpur XI", "Amravati XI", "Wardha XI",
    "Yavatmal XI", "Chandrapur XI", "Akola XI",
    "Buldhana XI", "Bhandara XI", "Gondia XI"
]


@dataclass
class Player:
    player_id: int
    name: str
    gender: str
    date_of_birth: date
    batting_style: str
    bowling_style: Optional[str]
    player_role: str
    district: str
    age_group: str
    is_wicket_keeper: bool = False

@dataclass
class Match:
    match_id: int
    tournament_name: str
    format: str
    gender: str
    age_group: str
    match_date: date
    venue: str
    city: str
    team1: str
    team2: str
    toss_winner: str
    toss_decision: str
    match_winner: str
    win_margin: int
    win_type: str
    season: str = "2024-25"

@dataclass
class Innings:
    innings_id: int
    match_id: int
    innings_number: int
    batting_team: str
    bowling_team: str
    total_runs: int = 0
    total_wickets: int = 0
    total_overs: float = 0.0
    extras: int = 0

@dataclass
class Delivery:
    delivery_id: int
    innings_id: int
    match_id: int
    over_number: int
    ball_number: int
    phase: str
    batter_id: int
    non_striker_id: int
    bowler_id: int
    batter_name: str
    bowler_name: str
    bowler_type: str
    batter_position: int
    runs_scored: int
    extras_runs: int
    total_runs: int
    is_wide: bool
    is_noball: bool
    is_bye: bool
    is_legbye: bool
    is_four: bool
    is_six: bool
    is_dot: bool
    is_wicket: bool
    wicket_type: Optional[str]
    fielder_name: Optional[str]
    batting_team: str
    bowling_team: str
    match_date: date
    tournament_name: str
    format: str
    gender: str
    age_group: str
    season: str = "2024-25"

# ============================================================
# PLAYER GENERATION
# ============================================================

def get_dob_for_age_group(age_group: str, gender: str) -> date:
    """Generate realistic DOB based on age group"""
    today = date.today()
    if age_group == "senior":
        age = random.randint(20, 35)
    elif age_group == "U25":
        age = random.randint(18, 24)
    elif age_group == "U19":
        age = random.randint(15, 18)
    elif age_group == "U16":
        age = random.randint(13, 15)
    else:
        age = random.randint(18, 30)

    days = age * 365 + random.randint(0, 364)
    return today - timedelta(days=days)


def generate_players() -> List[Player]:
    players = []
    player_id = 1

    for gender in ["male", "female"]:
        first_names = MALE_FIRST_NAMES if gender == "male" else FEMALE_FIRST_NAMES

        for age_group in ["senior", "U25", "U19", "U16"]:
            # skip U25 for female (VCA doesn't have it)
            if gender == "female" and age_group == "U25":
                continue

            count = 40 if gender == "male" else 25

            for _ in range(count):
                name = f"{random.choice(first_names)} {random.choice(SURNAMES)}"
                dob = get_dob_for_age_group(age_group, gender)

                batting_style = random.choices(
                    ["right-hand", "left-hand"], weights=[0.70, 0.30]
                )[0]

                # Role distribution — realistic
                role = random.choices(
                    ["batter", "bowler", "all-rounder", "wicket-keeper"],
                    weights=[0.35, 0.30, 0.25, 0.10]
                )[0]

                # Bowlers and all-rounders get a bowling style
                if role in ["bowler", "all-rounder"]:
                    bowling_style = random.choices(
                        BOWLING_STYLES, weights=BOWLING_STYLE_WEIGHTS
                    )[0]
                elif role == "wicket-keeper":
                    bowling_style = None
                else:
                    # some batters can bowl a bit
                    bowling_style = random.choices(
                        BOWLING_STYLES + [None],
                        weights=[0.05, 0.05, 0.03, 0.05, 0.03, 0.03, 0.02, 0.74]
                    )[0]

                players.append(Player(
                    player_id=player_id,
                    name=name,
                    gender=gender,
                    date_of_birth=dob,
                    batting_style=batting_style,
                    bowling_style=bowling_style,
                    player_role=role,
                    district=random.choice(VCA_DISTRICTS),
                    age_group=age_group,
                    is_wicket_keeper=(role == "wicket-keeper")
                ))
                player_id += 1

    print(f"  Generated {len(players)} players")
    return players


def get_phase(over_number: int, fmt: str) -> str:
    """
    over_number is 0-indexed
    T20:  0-5 = powerplay, 6-14 = middle, 15-19 = death
    ODI:  0-9 = powerplay, 10-39 = middle, 40-49 = death
    FC:   no phases — just 'play'
    """
    if fmt == "T20":
        if over_number <= 5:
            return "powerplay"
        elif over_number <= 14:
            return "middle"
        else:
            return "death"
    elif fmt == "ODI":
        if over_number <= 9:
            return "powerplay"
        elif over_number <= 39:
            return "middle"
        else:
            return "death"
    else:
        return "play"  


def get_player_skill_level(age_group: str) -> float:
    """
    Senior players are more consistent.
    Younger age groups have higher variance.
    Returns a multiplier for run-scoring ability.
    """
    return {
        "senior": 1.0,
        "U25":    0.9,
        "U19":    0.80,
        "U16":    0.70,
    }.get(age_group, 0.85)


def simulate_delivery(
    over: int,
    ball: int,
    fmt: str,
    batter_skill: float,
    phase: str,
    wickets_fallen: int,
    bowler_type: str,
    fielding_pool: list = None,
) -> dict:
    """
    Simulate a single delivery with realistic probabilities.
    Returns a dict of delivery outcomes.
    """

    # Base probabilities — vary by phase and format
    phase_aggression = {
        "powerplay": 1.2,
        "middle":    1.0,
        "death":     1.35,
        "play":      0.9,   # FC - conservative
    }.get(phase, 1.0)

    # Bowling style effectiveness (how hard it is to score against)
    bowling_difficulty = {
        "right-arm pace":        1.0,
        "right-arm medium pace": 0.95,
        "left-arm pace":         1.05,  # slightly harder (angle)
        "off-spin":              0.90,
        "leg-spin":              1.0,
        "left-arm orthodox":     0.92,
        "left-arm wrist spin":   1.05,
    }.get(bowler_type, 1.0)

    # Wickets pressure — tail-enders score slower
    wicket_pressure = max(0.5, 1.0 - (wickets_fallen * 0.04))

    effective_skill = batter_skill * phase_aggression * wicket_pressure / bowling_difficulty

    # Extras
    is_wide   = random.random() < 0.04
    is_noball = random.random() < 0.01

    if is_wide:
        return {
            "runs_scored": 0, "extras_runs": 1, "total_runs": 1,
            "is_wide": True, "is_noball": False, "is_bye": False, "is_legbye": False,
            "is_four": False, "is_six": False, "is_dot": False,
            "is_wicket": False, "wicket_type": None, "fielder_name": None
        }

    # Wicket probability — higher for difficult bowlers
    wicket_prob = 0.055 / (effective_skill * 0.8)
    wicket_prob = min(wicket_prob, 0.15)  # cap at 15%

    if not is_noball and random.random() < wicket_prob:
        wicket_types = ["caught", "bowled", "lbw", "run out", "stumped"]
        wicket_weights = [0.45, 0.22, 0.18, 0.10, 0.05]
        # spinners get more stumped/lbw
        if "spin" in bowler_type or "orthodox" in bowler_type:
            wicket_weights = [0.38, 0.15, 0.25, 0.10, 0.12]
        wt = random.choices(wicket_types, weights=wicket_weights)[0]
        return {
            "runs_scored": 0, "extras_runs": 0, "total_runs": 0,
            "is_wide": False, "is_noball": is_noball, "is_bye": False, "is_legbye": False,
            "is_four": False, "is_six": False, "is_dot": False,
            "is_wicket": True, "wicket_type": wt,
            "fielder_name": (
                random.choice(fielding_pool).name
                if fielding_pool and wt in ["caught", "run out", "stumped"]
                else None
            )
        }

    # Run scoring
    run_options   = [0, 1, 2, 3, 4, 6]
    base_weights  = [0.35, 0.30, 0.10, 0.03, 0.14, 0.08]

    # Adjust for effective skill
    if effective_skill > 1.1:
        base_weights = [0.25, 0.28, 0.12, 0.04, 0.18, 0.13]
    elif effective_skill < 0.7:
        base_weights = [0.45, 0.32, 0.08, 0.02, 0.10, 0.03]

    runs = random.choices(run_options, weights=base_weights)[0]

    # No-ball adds 1 extra run
    extras = 1 if is_noball else 0

    return {
        "runs_scored":  runs,
        "extras_runs":  extras,
        "total_runs":   runs + extras,
        "is_wide":      False,
        "is_noball":    is_noball,
        "is_bye":       False,
        "is_legbye":    False,
        "is_four":      runs == 4,
        "is_six":       runs == 6,
        "is_dot":       runs == 0 and not is_noball,
        "is_wicket":    False,
        "wicket_type":  None,
        "fielder_name": None
    }


# ============================================================
# INNINGS SIMULATION
# ============================================================

def simulate_innings(
    innings_id: int,
    match_id: int,
    match_date: date,
    batting_players: List[Player],
    bowling_players: List[Player],
    batting_team: str,
    bowling_team: str,
    fmt: str,
    tournament_name: str,
    gender: str,
    age_group: str,
    season: str,
    delivery_id_start: int,
    target: Optional[int] = None  # for 2nd innings chases
) -> tuple:
    """
    Simulate a full innings ball by ball.
    Returns (innings_obj, deliveries_list, next_delivery_id)
    """

    max_overs = {"T20": 20, "ODI": 50, "FirstClass": 90}.get(fmt, 20)
    max_wickets = 10

    deliveries = []
    delivery_id = delivery_id_start

    # Set up batting order — top 3 are best batters
    batters = batting_players[:11]
    bowlers = [p for p in bowling_players if p.bowling_style is not None]
    if len(bowlers) < 4:
        bowlers = bowling_players[:5]

    current_batter_idx = 0
    non_striker_idx = 1
    batter_position = 1

    on_strike = batters[current_batter_idx]
    non_striker = batters[non_striker_idx]
    next_batter_idx = 2

    wickets = 0
    total_runs = 0
    total_extras = 0
    balls_bowled_legal = 0

    # T20/ODI skill multiplier — senior is best
    batter_skill_base = get_player_skill_level(age_group)

    for over_num in range(max_overs):
        if wickets >= max_wickets:
            break

        # Choose bowler for this over
        bowler = random.choice(bowlers)
        phase = get_phase(over_num, fmt)

        legal_balls = 0
        ball_num = 0

        while legal_balls < 6:
            ball_num += 1

            # Individual batter skill varies
            batter_skill = batter_skill_base * random.uniform(0.8, 1.2)
            # Opener bonus
            if batter_position <= 3:
                batter_skill *= 1.1

            bowler_type = bowler.bowling_style or "right-arm medium pace"

            result = simulate_delivery(
                over=over_num,
                ball=ball_num,
                fmt=fmt,
                batter_skill=batter_skill,
                phase=phase,
                wickets_fallen=wickets,
                bowler_type=bowler_type,
                fielding_pool=bowling_players
            )

            if not result["is_wide"] and not result["is_noball"]:
                legal_balls += 1
                balls_bowled_legal += 1

            total_runs += result["total_runs"]
            total_extras += result["extras_runs"]

            delivery = Delivery(
                delivery_id=delivery_id,
                innings_id=innings_id,
                match_id=match_id,
                over_number=over_num,
                ball_number=ball_num,
                phase=phase,
                batter_id=on_strike.player_id,
                non_striker_id=non_striker.player_id,
                bowler_id=bowler.player_id,
                batter_name=on_strike.name,
                bowler_name=bowler.name,
                bowler_type=bowler_type,
                batter_position=batter_position,
                runs_scored=result["runs_scored"],
                extras_runs=result["extras_runs"],
                total_runs=result["total_runs"],
                is_wide=result["is_wide"],
                is_noball=result["is_noball"],
                is_bye=result["is_bye"],
                is_legbye=result["is_legbye"],
                is_four=result["is_four"],
                is_six=result["is_six"],
                is_dot=result["is_dot"],
                is_wicket=result["is_wicket"],
                wicket_type=result["wicket_type"],
                fielder_name=result["fielder_name"],
                batting_team=batting_team,
                bowling_team=bowling_team,
                match_date=match_date,
                tournament_name=tournament_name,
                format=fmt,
                gender=gender,
                age_group=age_group,
                season=season
            )
            deliveries.append(delivery)
            delivery_id += 1

            # Handle wicket
            if result["is_wicket"]:
                wickets += 1
                if wickets >= max_wickets or next_batter_idx >= len(batters):
                    break
                # New batter comes in
                on_strike = batters[next_batter_idx]
                batter_position += 1
                next_batter_idx += 1

            # Rotate strike on odd runs
            if result["runs_scored"] % 2 == 1:
                on_strike, non_striker = non_striker, on_strike

            # Chase check
            if target and total_runs >= target:
                break

        # End of over — rotate strike
        on_strike, non_striker = non_striker, on_strike

        if target and total_runs >= target:
            break

    # Build innings object
    total_overs_completed = balls_bowled_legal / 6
    innings_obj = Innings(
        innings_id=innings_id,
        match_id=match_id,
        innings_number=0,  # set by caller
        batting_team=batting_team,
        bowling_team=bowling_team,
        total_runs=total_runs,
        total_wickets=wickets,
        total_overs=round(total_overs_completed, 1),
        extras=total_extras
    )

    return innings_obj, deliveries, delivery_id


# ============================================================
# MATCH SIMULATION
# ============================================================

def simulate_match(
    match_id: int,
    tournament: dict,
    all_players: List[Player],
    innings_id_start: int,
    delivery_id_start: int,
    match_date: date,
    season: str = "2024-25"
) -> tuple:
    """
    Simulate a full match (2 innings for T20/ODI, can extend for FC).
    Returns (match, innings_list, deliveries_list, next_innings_id, next_delivery_id)
    """

    gender = tournament["gender"]
    age_group = tournament["age_group"]
    fmt = tournament["format"]

    # Filter eligible players
    eligible = [p for p in all_players
                if p.gender == gender and p.age_group == age_group]

    if len(eligible) < 22:
        # Fall back to senior pool if not enough
        eligible = [p for p in all_players if p.gender == gender]

    # Pick two teams of 11
    random.shuffle(eligible)
    team1_players = eligible[:11]
    team2_players = eligible[11:22]

    team1 = random.choice(VCA_TEAMS)
    team2 = random.choice([t for t in VCA_TEAMS if t != team1])

    venue, city = random.choice(VENUES)

    toss_winner = random.choice([team1, team2])
    toss_decision = random.choice(["bat", "field"])

    match = Match(
        match_id=match_id,
        tournament_name=tournament["name"],
        format=fmt,
        gender=gender,
        age_group=age_group,
        match_date=match_date,
        venue=venue,
        city=city,
        team1=team1,
        team2=team2,
        toss_winner=toss_winner,
        toss_decision=toss_decision,
        match_winner="",  # fill after simulation
        win_margin=0,
        win_type="",
        season=season
    )

    all_innings = []
    all_deliveries = []
    innings_id = innings_id_start
    delivery_id = delivery_id_start

    # First innings — determine who bats first
    if toss_decision == "bat":
        bat_first_name = toss_winner
    else:
        bat_first_name = team2 if toss_winner == team1 else team1

    bowl_first_name = team2 if bat_first_name == team1 else team1
    bat_first_players  = team1_players if bat_first_name == team1 else team2_players
    bowl_first_players = team2_players if bat_first_name == team1 else team1_players

    # Innings 1
    inn1, deliveries1, delivery_id = simulate_innings(
        innings_id=innings_id,
        match_id=match_id,
        match_date=match_date,
        batting_players=bat_first_players,
        bowling_players=bowl_first_players,
        batting_team=bat_first_name,
        bowling_team=bowl_first_name,
        fmt=fmt,
        tournament_name=tournament["name"],
        gender=gender,
        age_group=age_group,
        season=season,
        delivery_id_start=delivery_id
    )
    inn1.innings_number = 1
    all_innings.append(inn1)
    all_deliveries.extend(deliveries1)
    innings_id += 1

    # Innings 2
    target = inn1.total_runs + 1
    inn2, deliveries2, delivery_id = simulate_innings(
        innings_id=innings_id,
        match_id=match_id,
        match_date=match_date,
        batting_players=bowl_first_players,
        bowling_players=bat_first_players,
        batting_team=bowl_first_name,
        bowling_team=bat_first_name,
        fmt=fmt,
        tournament_name=tournament["name"],
        gender=gender,
        age_group=age_group,
        season=season,
        delivery_id_start=delivery_id,
        target=target if fmt != "FirstClass" else None
    )
    inn2.innings_number = 2
    all_innings.append(inn2)
    all_deliveries.extend(deliveries2)
    innings_id += 1

    # Determine winner
    if fmt != "FirstClass":
        if inn2.total_runs >= inn1.total_runs:
            match.match_winner = bowl_first_name
            match.win_margin = 10 - inn2.total_wickets
            match.win_type = "wickets"
        else:
            match.match_winner = bat_first_name
            match.win_margin = inn1.total_runs - inn2.total_runs
            match.win_type = "runs"
    else:
        match.match_winner = random.choice([team1, team2, "draw"])
        match.win_margin = random.randint(10, 200)
        match.win_type = random.choice(["runs", "wickets", "innings"])

    return match, all_innings, all_deliveries, innings_id, delivery_id


# ============================================================
# MAIN DATA GENERATION
# ============================================================

def generate_all_data():
    print("=" * 60)
    print("VCA Cricket Analytics — Dummy Data Generator")
    print("=" * 60)

    print("\n[1/4] Generating players...")
    players = generate_players()

    print("\n[2/4] Simulating matches...")
    all_matches = []
    all_innings = []
    all_deliveries = []
    all_tournaments = []

    match_id = 1
    innings_id = 1
    delivery_id = 1
    tournament_id = 1

    season = "2024-25"
    start_date = date(2024, 10, 1)

    for t in TOURNAMENTS:
        print(f"   → {t['name']} ({t['gender']}, {t['age_group']}, {t['format']})")

        all_tournaments.append({
            "tournament_id":   tournament_id,
            "tournament_name": t["name"],
            "format":          t["format"],
            "gender":          t["gender"],
            "age_group":       t["age_group"],
            "overs_per_innings": t["overs"],
            "season":          season
        })
        tournament_id += 1

        for m in range(MATCHES_PER_TOURNAMENT):
            match_date = start_date + timedelta(days=(m * 3) + TOURNAMENTS.index(t) * 2)

            match, innings, deliveries, innings_id, delivery_id = simulate_match(
                match_id=match_id,
                tournament=t,
                all_players=players,
                innings_id_start=innings_id,
                delivery_id_start=delivery_id,
                match_date=match_date,
                season=season
            )

            all_matches.append(match)
            all_innings.extend(innings)
            all_deliveries.extend(deliveries)
            match_id += 1

    print(f"\n   Total matches    : {len(all_matches)}")
    print(f"   Total innings    : {len(all_innings)}")
    print(f"   Total deliveries : {len(all_deliveries)}")

    print("\n[3/4] Writing CSV files...")
    write_csvs(players, all_tournaments, all_matches, all_innings, all_deliveries)

    print("\n[4/4] Writing SQL insert file...")
    write_sql_inserts(players, all_tournaments, all_matches, all_innings, all_deliveries)

    print("\n✅ Done! Files saved to ./output/")
    print_sample_stats(all_deliveries, players)


# ============================================================
# CSV WRITERS
# ============================================================

def write_csvs(players, tournaments, matches, innings_list, deliveries):
    # Players
    with open(f"{OUTPUT_DIR}/players.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["player_id","name","gender","date_of_birth","batting_style",
                    "bowling_style","player_role","district","age_group","is_wicket_keeper"])
        for p in players:
            w.writerow([p.player_id, p.name, p.gender, p.date_of_birth,
                        p.batting_style, p.bowling_style, p.player_role,
                        p.district, p.age_group, p.is_wicket_keeper])

    # Tournaments
    with open(f"{OUTPUT_DIR}/tournaments.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tournament_id","tournament_name","format","gender",
                    "age_group","overs_per_innings","season"])
        for t in tournaments:
            w.writerow([t["tournament_id"], t["tournament_name"], t["format"],
                        t["gender"], t["age_group"], t["overs_per_innings"], t["season"]])

    # Matches
    with open(f"{OUTPUT_DIR}/matches.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["match_id","tournament_name","format","gender","age_group",
                    "match_date","venue","city","team1","team2","toss_winner",
                    "toss_decision","match_winner","win_margin","win_type","season"])
        for m in matches:
            w.writerow([m.match_id, m.tournament_name, m.format, m.gender,
                        m.age_group, m.match_date, m.venue, m.city,
                        m.team1, m.team2, m.toss_winner, m.toss_decision,
                        m.match_winner, m.win_margin, m.win_type, m.season])

    # Innings
    with open(f"{OUTPUT_DIR}/innings.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["innings_id","match_id","innings_number","batting_team",
                    "bowling_team","total_runs","total_wickets","total_overs","extras"])
        for i in innings_list:
            w.writerow([i.innings_id, i.match_id, i.innings_number, i.batting_team,
                        i.bowling_team, i.total_runs, i.total_wickets,
                        i.total_overs, i.extras])

    # Deliveries
    with open(f"{OUTPUT_DIR}/deliveries.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "delivery_id","innings_id","match_id","over_number","ball_number","phase",
            "batter_id","non_striker_id","bowler_id","batter_name","bowler_name",
            "bowler_type","batter_position","runs_scored","extras_runs","total_runs",
            "is_wide","is_noball","is_bye","is_legbye","is_four","is_six","is_dot",
            "is_wicket","wicket_type","fielder_name","batting_team","bowling_team",
            "match_date","tournament_name","format","gender","age_group","season"
        ])
        for d in deliveries:
            w.writerow([
                d.delivery_id, d.innings_id, d.match_id, d.over_number, d.ball_number,
                d.phase, d.batter_id, d.non_striker_id, d.bowler_id, d.batter_name,
                d.bowler_name, d.bowler_type, d.batter_position, d.runs_scored,
                d.extras_runs, d.total_runs, d.is_wide, d.is_noball, d.is_bye,
                d.is_legbye, d.is_four, d.is_six, d.is_dot, d.is_wicket,
                d.wicket_type, d.fielder_name, d.batting_team, d.bowling_team,
                d.match_date, d.tournament_name, d.format, d.gender, d.age_group, d.season
            ])

    print(f"   ✓ players.csv       ({len(players)} rows)")
    print(f"   ✓ tournaments.csv   ({len(tournaments)} rows)")
    print(f"   ✓ matches.csv       ({len(matches)} rows)")
    print(f"   ✓ innings.csv       ({len(innings_list)} rows)")
    print(f"   ✓ deliveries.csv    ({len(deliveries)} rows)")


# ============================================================
# SQL INSERT WRITER
# ============================================================

def write_sql_inserts(players, tournaments, matches, innings_list, deliveries):
    """Write a .sql file with all INSERT statements for PostgreSQL"""

    with open(f"{OUTPUT_DIR}/insert_data.sql", "w") as f:
        f.write("-- VCA Cricket Analytics — Generated Data Inserts\n")
        f.write("-- Run this AFTER running schema.sql\n\n")

        # Players
        f.write("-- PLAYERS\n")
        for p in players:
            bs = f"'{p.bowling_style}'" if p.bowling_style else "NULL"
            f.write(
                f"INSERT INTO players VALUES ({p.player_id}, '{p.name.replace(chr(39), chr(39)*2)}', "
                f"'{p.gender}', '{p.date_of_birth}', '{p.batting_style}', "
                f"{bs}, '{p.player_role}', '{p.district}', '{p.age_group}', "
                f"{'TRUE' if p.is_wicket_keeper else 'FALSE'}, NOW());\n"
            )

        # Tournaments
        f.write("\n-- TOURNAMENTS\n")
        for t in tournaments:
            overs = t["overs_per_innings"] if t["overs_per_innings"] else "NULL"
            f.write(
                f"INSERT INTO tournaments VALUES ({t['tournament_id']}, "
                f"'{t['tournament_name']}', '{t['format']}', '{t['gender']}', "
                f"'{t['age_group']}', {overs}, '{t['season']}');\n"
            )

        # Matches
        f.write("\n-- MATCHES\n")
        for m in matches:
            winner = f"'{m.match_winner}'" if m.match_winner else "NULL"
            f.write(
                f"INSERT INTO matches (match_id, tournament_name, format, gender, age_group, "
                f"match_date, venue, city, team1, team2, toss_winner, toss_decision, "
                f"match_winner, win_margin, win_type, season) VALUES "
                f"({m.match_id}, '{m.tournament_name}', '{m.format}', '{m.gender}', "
                f"'{m.age_group}', '{m.match_date}', '{m.venue}', '{m.city}', "
                f"'{m.team1}', '{m.team2}', '{m.toss_winner}', '{m.toss_decision}', "
                f"{winner}, {m.win_margin}, '{m.win_type}', '{m.season}');\n"
            )

        # Innings
        f.write("\n-- INNINGS\n")
        for i in innings_list:
            f.write(
                f"INSERT INTO innings VALUES ({i.innings_id}, {i.match_id}, "
                f"{i.innings_number}, '{i.batting_team}', '{i.bowling_team}', "
                f"{i.total_runs}, {i.total_wickets}, {i.total_overs}, {i.extras});\n"
            )

        # Deliveries — batch in chunks of 500 for performance
        f.write("\n-- DELIVERIES\n")
        for d in deliveries:
            wt = f"'{d.wicket_type}'" if d.wicket_type else "NULL"
            fn = f"'{d.fielder_name}'" if d.fielder_name else "NULL"
            f.write(
                f"INSERT INTO deliveries VALUES ("
                f"{d.delivery_id}, {d.innings_id}, {d.match_id}, "
                f"{d.over_number}, {d.ball_number}, '{d.phase}', "
                f"{d.batter_id}, {d.non_striker_id}, {d.bowler_id}, "
                f"'{d.batter_name.replace(chr(39), chr(39)*2)}', "
                f"'{d.bowler_name.replace(chr(39), chr(39)*2)}', "
                f"'{d.bowler_type}', {d.batter_position}, "
                f"{d.runs_scored}, {d.extras_runs}, {d.total_runs}, "
                f"{'TRUE' if d.is_wide else 'FALSE'}, {'TRUE' if d.is_noball else 'FALSE'}, "
                f"{'TRUE' if d.is_bye else 'FALSE'}, {'TRUE' if d.is_legbye else 'FALSE'}, "
                f"{'TRUE' if d.is_four else 'FALSE'}, {'TRUE' if d.is_six else 'FALSE'}, "
                f"{'TRUE' if d.is_dot else 'FALSE'}, {'TRUE' if d.is_wicket else 'FALSE'}, "
                f"{wt}, {fn}, "
                f"'{d.batting_team}', '{d.bowling_team}', "
                f"'{d.match_date}', '{d.tournament_name}', '{d.format}', "
                f"'{d.gender}', '{d.age_group}', '{d.season}'"
                f");\n"
            )

    print(f"   ✓ insert_data.sql  ({len(deliveries)} delivery rows)")


# ============================================================
# SAMPLE STATS — quick sanity check
# ============================================================

def print_sample_stats(deliveries, players):
    print("\n" + "=" * 60)
    print("SANITY CHECK — Sample Stats")
    print("=" * 60)

    total = len(deliveries)
    wickets = sum(1 for d in deliveries if d.is_wicket)
    fours   = sum(1 for d in deliveries if d.is_four)
    sixes   = sum(1 for d in deliveries if d.is_six)
    dots    = sum(1 for d in deliveries if d.is_dot)
    legal   = sum(1 for d in deliveries if not d.is_wide and not d.is_noball)
    runs    = sum(d.runs_scored for d in deliveries)

    print(f"  Total deliveries : {total:,}")
    print(f"  Legal balls      : {legal:,}")
    print(f"  Total runs       : {runs:,}")
    print(f"  Wickets          : {wickets:,}")
    print(f"  Fours            : {fours:,}")
    print(f"  Sixes            : {sixes:,}")
    print(f"  Dot balls        : {dots:,}")
    if legal > 0:
        print(f"  Overall SR       : {runs*100/legal:.1f}")
        print(f"  Wicket every N   : {legal/wickets:.0f} balls" if wickets > 0 else "")

    # By gender
    print("\n  By gender:")
    for g in ["male", "female"]:
        g_d = [d for d in deliveries if d.gender == g]
        g_r = sum(d.runs_scored for d in g_d)
        g_l = sum(1 for d in g_d if not d.is_wide and not d.is_noball)
        print(f"    {g:6}: {len(g_d):,} deliveries | {g_r:,} runs | SR {g_r*100/g_l:.1f}" if g_l > 0 else f"    {g}: 0 deliveries")

    # By format
    print("\n  By format:")
    for fmt in ["T20", "ODI", "FirstClass"]:
        f_d = [d for d in deliveries if d.format == fmt]
        f_r = sum(d.runs_scored for d in f_d)
        f_l = sum(1 for d in f_d if not d.is_wide and not d.is_noball)
        if f_l > 0:
            print(f"    {fmt:10}: {len(f_d):,} deliveries | SR {f_r*100/f_l:.1f}")


if __name__ == "__main__":
    generate_all_data()
