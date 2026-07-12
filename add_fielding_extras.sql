DROP VIEW IF EXISTS fielding_summary;
DROP VIEW IF EXISTS extras_summary;
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

    -- Catches
    SUM(CASE
        WHEN d.wicket_type = 'caught'
         AND d.fielder_name IS NOT NULL
         AND d.fielder_name != d.bowler_name
        THEN 1 ELSE 0 END)                                  AS catches,

    -- Caught and bowled
    SUM(CASE
        WHEN d.wicket_type = 'caught'
         AND d.fielder_name = d.bowler_name
        THEN 1 ELSE 0 END)                                  AS caught_and_bowled,

    -- Stumpings
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

    SUM(d.is_wide::INT)                                     AS wides,
    SUM(d.is_noball::INT)                                   AS noballs,
    SUM(d.is_bye::INT)                                      AS byes,
    SUM(d.is_legbye::INT)                                   AS leg_byes,
    SUM(d.extras_runs)                                      AS total_extras,

    ROUND(
        SUM(d.extras_runs) * 100.0 /
        NULLIF(SUM(d.total_runs), 0),
    2)                                                      AS extras_percentage,

    COUNT(*)                                                AS balls_bowled,

    ROUND(
        (SUM(d.is_wide::INT) + SUM(d.is_noball::INT)) * 100.0 /
        NULLIF(COUNT(*), 0),
    2)                                                      AS indiscipline_rate

FROM deliveries d
GROUP BY
    d.bowling_team, d.batting_team, d.match_id, d.innings_id,
    d.tournament_name, d.format, d.gender, d.age_group, d.season;


SELECT fielder_name, catches, stumpings, run_outs, total_dismissals_effected
FROM fielding_summary
ORDER BY total_dismissals_effected DESC
LIMIT 10;

SELECT bowling_team, tournament_name, format,
       SUM(wides) as total_wides,
       SUM(noballs) as total_noballs,
       SUM(total_extras) as total_extras
FROM extras_summary
GROUP BY bowling_team, tournament_name, format
ORDER BY total_extras ASC
LIMIT 10;
