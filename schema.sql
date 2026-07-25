DROP TABLE IF EXISTS deliveries CASCADE;
DROP TABLE IF EXISTS innings CASCADE;
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS players CASCADE;
DROP TABLE IF EXISTS tournaments CASCADE;

CREATE TABLE tournaments (
    tournament_id     SERIAL PRIMARY KEY,
    tournament_name   VARCHAR(100) NOT NULL,       -- "Ranji Trophy", "SMAT", "U19 Women T20"
    format            VARCHAR(20) NOT NULL,         -- T20 / ODI / FirstClass
    gender            VARCHAR(10) NOT NULL,         -- male / female
    age_group         VARCHAR(20) NOT NULL,         -- senior / U25 / U19 / U16
    overs_per_innings INT,                          -- 20 for T20, 50 for ODI, NULL for FC
    season            VARCHAR(10) NOT NULL          -- "2024-25"
);


CREATE TABLE players (
    player_id         SERIAL PRIMARY KEY,
    name              VARCHAR(100) NOT NULL,
    gender            VARCHAR(10) NOT NULL,         -- male / female
    date_of_birth     DATE NOT NULL,
    batting_style     VARCHAR(30) NOT NULL,         -- right-hand / left-hand
    bowling_style     VARCHAR(50),                  -- right-arm pace / leg-spin / off-spin etc.
    player_role       VARCHAR(30),                  -- batter / bowler / all-rounder / wicket-keeper
    district          VARCHAR(50),                  -- Nagpur / Amravati / Wardha / Yavatmal etc.
    age_group         VARCHAR(20),                  -- senior / U25 / U19 / U16
    is_wicket_keeper  BOOLEAN DEFAULT FALSE,
    created_at        TIMESTAMP DEFAULT NOW()
);


CREATE TABLE matches (
    match_id          SERIAL PRIMARY KEY,
    tournament_id     INT REFERENCES tournaments(tournament_id),
    tournament_name   VARCHAR(100),                 -- denormalized for easy querying
    format            VARCHAR(20) NOT NULL,         -- T20 / ODI / FirstClass
    gender            VARCHAR(10) NOT NULL,
    age_group         VARCHAR(20) NOT NULL,
    match_date        DATE NOT NULL,
    venue             VARCHAR(100),
    city              VARCHAR(50),
    team1             VARCHAR(100) NOT NULL,
    team2             VARCHAR(100) NOT NULL,
    toss_winner       VARCHAR(100),
    toss_decision     VARCHAR(10),                  -- bat / field
    match_winner      VARCHAR(100),
    win_margin        INT,
    win_type          VARCHAR(20),                  -- runs / wickets
    season            VARCHAR(10) NOT NULL
);


CREATE TABLE innings (
    innings_id        SERIAL PRIMARY KEY,
    match_id          INT REFERENCES matches(match_id),
    innings_number    INT NOT NULL,                 -- 1 or 2 (or 3,4 for FC)
    batting_team      VARCHAR(100) NOT NULL,
    bowling_team      VARCHAR(100) NOT NULL,
    total_runs        INT DEFAULT 0,
    total_wickets     INT DEFAULT 0,
    total_overs       DECIMAL(5,1) DEFAULT 0,
    extras            INT DEFAULT 0
);


CREATE TABLE deliveries (
    delivery_id       SERIAL PRIMARY KEY,
    innings_id        INT REFERENCES innings(innings_id),
    match_id          INT REFERENCES matches(match_id),

    -- Ball metadata
    over_number       INT NOT NULL,                 -- 0-indexed (over 1 = over_number 0)
    ball_number       INT NOT NULL,                 -- 1-6 (can go higher with extras)
    phase             VARCHAR(20) NOT NULL,         -- powerplay / middle / death

    -- Players
    batter_id         INT REFERENCES players(player_id),
    non_striker_id    INT REFERENCES players(player_id),
    bowler_id         INT REFERENCES players(player_id),
    batter_name       VARCHAR(100),                 -- denormalized for easy querying
    bowler_name       VARCHAR(100),
    bowler_type       VARCHAR(50),                  -- denormalized from players table

    -- Batting position
    batter_position   INT,                          -- 1-11

    -- Runs
    runs_scored       INT DEFAULT 0,                -- runs off the bat
    extras_runs       INT DEFAULT 0,
    total_runs        INT DEFAULT 0,                -- runs_scored + extras_runs

    -- Extras breakdown
    is_wide           BOOLEAN DEFAULT FALSE,
    is_noball         BOOLEAN DEFAULT FALSE,
    is_bye            BOOLEAN DEFAULT FALSE,
    is_legbye         BOOLEAN DEFAULT FALSE,

    -- Boundaries
    is_four           BOOLEAN DEFAULT FALSE,
    is_six            BOOLEAN DEFAULT FALSE,

    -- Dot ball (no run off bat, legal delivery)
    is_dot            BOOLEAN DEFAULT FALSE,

    -- Wicket
    is_wicket         BOOLEAN DEFAULT FALSE,
    wicket_type       VARCHAR(30),                  -- bowled/caught/lbw/run out/stumped etc.
    fielder_name      VARCHAR(100),                 -- who took the catch/effected run out

    -- Match context
    batting_team      VARCHAR(100),
    bowling_team      VARCHAR(100),
    match_date        DATE,
    tournament_name   VARCHAR(100),
    format            VARCHAR(20),
    gender            VARCHAR(10),
    age_group         VARCHAR(20),
    season            VARCHAR(10)
);


CREATE INDEX idx_deliveries_batter     ON deliveries(batter_id);
CREATE INDEX idx_deliveries_bowler     ON deliveries(bowler_id);
CREATE INDEX idx_deliveries_match      ON deliveries(match_id);
CREATE INDEX idx_deliveries_phase      ON deliveries(phase);
CREATE INDEX idx_deliveries_tournament ON deliveries(tournament_name);
CREATE INDEX idx_deliveries_gender     ON deliveries(gender);
CREATE INDEX idx_deliveries_age_group  ON deliveries(age_group);
CREATE INDEX idx_deliveries_format     ON deliveries(format);
CREATE INDEX idx_deliveries_season     ON deliveries(season);
CREATE INDEX idx_players_gender        ON players(gender);
CREATE INDEX idx_players_age_group     ON players(age_group);
CREATE INDEX idx_players_district      ON players(district);

-- ============================================================
-- VIEWS — pre-built common analytics queries
-- Selectors can query these directly or AI can reference them
-- ============================================================

-- Batting summary per player per tournament
CREATE VIEW batting_summary AS
SELECT
    d.batter_id,
    d.batter_name,
    p.batting_style,
    p.district,
    d.tournament_name,
    d.format,
    d.gender,
    d.age_group,
    d.season,
    COUNT(DISTINCT d.match_id)                          AS matches_played,
    SUM(CASE WHEN NOT d.is_wide AND NOT d.is_noball 
             THEN 1 ELSE 0 END)                         AS balls_faced,
    SUM(d.runs_scored)                                  AS total_runs,
    MAX(d.runs_scored)                                  AS highest_score,  -- NOTE: this is per ball, innings-level needs subquery
    SUM(d.is_four::INT)                                 AS fours,
    SUM(d.is_six::INT)                                  AS sixes,
    SUM(d.is_dot::INT)                                  AS dot_balls_faced,
    ROUND(
        SUM(d.runs_scored) * 100.0 /
        NULLIF(SUM(CASE WHEN NOT d.is_wide AND NOT d.is_noball THEN 1 ELSE 0 END), 0),
    2)                                                  AS strike_rate,
    ROUND(
        SUM(d.is_four::INT + d.is_six::INT) * 100.0 /
        NULLIF(SUM(CASE WHEN NOT d.is_wide AND NOT d.is_noball THEN 1 ELSE 0 END), 0),
    2)                                                  AS boundary_percentage
FROM deliveries d
JOIN players p ON d.batter_id = p.player_id
WHERE NOT d.is_wide AND NOT d.is_noball
GROUP BY
    d.batter_id, d.batter_name, p.batting_style, p.district,
    d.tournament_name, d.format, d.gender, d.age_group, d.season;


-- Bowling summary per player per tournament
CREATE VIEW bowling_summary AS
SELECT
    d.bowler_id,
    d.bowler_name,
    d.bowler_type,
    p.district,
    d.tournament_name,
    d.format,
    d.gender,
    d.age_group,
    d.season,
    COUNT(DISTINCT d.match_id)                          AS matches_played,
    COUNT(*)                                            AS balls_bowled,
    SUM(d.total_runs)                                   AS runs_conceded,
    SUM(d.is_wicket::INT)                               AS wickets,
    SUM(d.is_wide::INT)                                 AS wides,
    SUM(d.is_noball::INT)                               AS noballs,
    SUM(d.is_dot::INT)                                  AS dot_balls,
    ROUND(SUM(d.total_runs) * 6.0 / NULLIF(COUNT(*), 0), 2)   AS economy_rate,
    ROUND(COUNT(*) * 1.0 / NULLIF(SUM(d.is_wicket::INT), 0), 1) AS bowling_strike_rate,
    ROUND(SUM(d.total_runs) * 1.0 / NULLIF(SUM(d.is_wicket::INT), 0), 2) AS bowling_average
FROM deliveries d
JOIN players p ON d.bowler_id = p.player_id
GROUP BY
    d.bowler_id, d.bowler_name, d.bowler_type, p.district,
    d.tournament_name, d.format, d.gender, d.age_group, d.season;


-- Phase-wise batting (powerplay / middle / death)
CREATE VIEW phase_batting AS
SELECT
    d.batter_id,
    d.batter_name,
    p.batting_style,
    p.district,
    d.phase,
    d.tournament_name,
    d.format,
    d.gender,
    d.age_group,
    d.season,
    SUM(CASE WHEN NOT d.is_wide AND NOT d.is_noball THEN 1 ELSE 0 END) AS balls_faced,
    SUM(d.runs_scored)                                  AS runs,
    SUM(d.is_wicket::INT)                               AS dismissals,
    SUM(d.is_four::INT)                                 AS fours,
    SUM(d.is_six::INT)                                  AS sixes,
    ROUND(
        SUM(d.runs_scored) * 100.0 /
        NULLIF(SUM(CASE WHEN NOT d.is_wide AND NOT d.is_noball THEN 1 ELSE 0 END), 0),
    2)                                                  AS strike_rate
FROM deliveries d
JOIN players p ON d.batter_id = p.player_id
GROUP BY
    d.batter_id, d.batter_name, p.batting_style, p.district,
    d.phase, d.tournament_name, d.format, d.gender, d.age_group, d.season;


-- Phase-wise bowling
CREATE VIEW phase_bowling AS
SELECT
    d.bowler_id,
    d.bowler_name,
    d.bowler_type,
    p.district,
    d.phase,
    d.tournament_name,
    d.format,
    d.gender,
    d.age_group,
    d.season,
    COUNT(*)                                            AS balls_bowled,
    SUM(d.total_runs)                                   AS runs_conceded,
    SUM(d.is_wicket::INT)                               AS wickets,
    SUM(d.is_dot::INT)                                  AS dot_balls,
    ROUND(SUM(d.total_runs) * 6.0 / NULLIF(COUNT(*), 0), 2) AS economy_rate,
    ROUND(SUM(d.is_dot::INT) * 100.0 / NULLIF(COUNT(*), 0), 1) AS dot_ball_percentage
FROM deliveries d
JOIN players p ON d.bowler_id = p.player_id
GROUP BY
    d.bowler_id, d.bowler_name, d.bowler_type, p.district,
    d.phase, d.tournament_name, d.format, d.gender, d.age_group, d.season;
