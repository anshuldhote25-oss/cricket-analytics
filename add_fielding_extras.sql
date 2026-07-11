-- ============================================================
-- FIELDING & EXTRAS EXTENSION
-- Run this in TablePlus against the circullence database
-- ============================================================

-- Drop views if they already exist (safe to re-run)
DROP VIEW IF EXISTS fielding_summary;
DROP VIEW IF EXISTS extras_summary;

-- ============================================================
-- FIELDING SUMMARY VIEW
-- One row per fielder per tournament
-- Covers: catches, stumpings, run outs
-- ============================================================
CREATE VIEW fielding_summary AS
SELECT
    d.fielder_name,
    p.player_id,
    p.district,
    p.gender,
    p.age_group,
    d.tournament_name,
    d.format,
    d.season,
    COUNT(DISTINCT d.match_id)                              AS matches_played,

    -- Catches (caught dismissals where fielder is not the bowler)
    SUM(CASE
        WHEN d.wicket_type = 'caught'
         AND d.fielder_name IS NOT NULL
         AND d.fielder_name != d.bowler_name
        THEN 1 ELSE 0 END)                                  AS catches,

    -- Caught and bowled (fielder = bowler)
    SUM(CASE
        WHEN d.wicket_type = 'caught'
         AND d.fielder_name = d.bowler_name
        THEN 1 ELSE 0 END)                                  AS caught_and_bowled,

    -- Stumpings (wicket-keeper only)
    SUM(CASE
        WHEN d.wicket_type = 'stumped'
        THEN 1 ELSE 0 END)                                  AS stumpings,

    -- Run outs
    SUM(CASE
        WHEN d.wicket_type = 'run out'
        THEN 1 ELSE 0 END)                                  AS run_outs,

    -- Total dismissals effected
    SUM(CASE
        WHEN d.wicket_type IN ('caught', 'stumped', 'run out')
         AND d.fielder_name IS NOT NULL
        THEN 1 ELSE 0 END)                                  AS total_dismissals_effected

FROM deliveries d
LEFT JOIN players p ON p.name = d.fielder_name
    AND p.gender = d.gender
    AND p.age_group = d.age_group
WHERE d.fielder_name IS NOT NULL
GROUP BY
    d.fielder_name, p.player_id, p.district,
    p.gender, p.age_group,
    d.tournament_name, d.format, d.season;


-- ============================================================
-- EXTRAS SUMMARY VIEW
-- One row per bowling team per innings
-- Covers: wides, no balls, byes, leg byes, total extras
-- ============================================================
CREATE VIEW extras_summary AS
SELECT
    d.bowling_team,
    d.batting_team,
    d.match_id,
    d.tournament_name,
    d.format,
    d.gender,
    d.age_group,
    d.season,
    d.innings_id,

    -- Extras breakdown
    SUM(d.is_wide::INT)                                     AS wides,
    SUM(d.is_noball::INT)                                   AS noballs,
    SUM(d.is_bye::INT)                                      AS byes,
    SUM(d.is_legbye::INT)                                   AS leg_byes,
    SUM(d.extras_runs)                                      AS total_extras,

    -- Runs from extras as % of total runs conceded
    ROUND(
        SUM(d.extras_runs) * 100.0 /
        NULLIF(SUM(d.total_runs), 0),
    2)                                                      AS extras_percentage,

    -- Total balls bowled in this innings by this team
    COUNT(*)                                                AS balls_bowled,

    -- Wide + noball rate (discipline metric)
    ROUND(
        (SUM(d.is_wide::INT) + SUM(d.is_noball::INT)) * 100.0 /
        NULLIF(COUNT(*), 0),
    2)                                                      AS indiscipline_rate

FROM deliveries d
GROUP BY
    d.bowling_team, d.batting_team, d.match_id, d.innings_id,
    d.tournament_name, d.format, d.gender, d.age_group, d.season;


-- ============================================================
-- VERIFICATION QUERIES — run these to confirm views work
-- ============================================================

-- Top fielders by total dismissals effected
SELECT fielder_name, catches, stumpings, run_outs, total_dismissals_effected
FROM fielding_summary
ORDER BY total_dismissals_effected DESC
LIMIT 10;

-- Most disciplined bowling teams (fewest extras per match)
SELECT bowling_team, tournament_name, format,
       SUM(wides) as total_wides,
       SUM(noballs) as total_noballs,
       SUM(total_extras) as total_extras
FROM extras_summary
GROUP BY bowling_team, tournament_name, format
ORDER BY total_extras ASC
LIMIT 10;
