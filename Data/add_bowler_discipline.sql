-- Bowler discipline view
-- Shows wides, no balls and extras per bowler
CREATE OR REPLACE VIEW bowler_discipline AS
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
    COUNT(DISTINCT d.match_id)       AS matches_played,
    COUNT(*)                          AS balls_bowled,
    SUM(d.is_wide::INT)              AS wides,
    SUM(d.is_noball::INT)            AS noballs,
    SUM(d.is_wide::INT) +
    SUM(d.is_noball::INT)            AS total_indiscipline,
    SUM(d.extras_runs)               AS total_extras_runs,
    ROUND((SUM(d.is_wide::INT) + SUM(d.is_noball::INT)) * 100.0 /
        NULLIF(COUNT(*), 0), 2)      AS indiscipline_rate
FROM deliveries d
JOIN players p ON d.bowler_id = p.player_id
GROUP BY
    d.bowler_id, d.bowler_name, d.bowler_type, p.district,
    d.tournament_name, d.format, d.gender, d.age_group, d.season;