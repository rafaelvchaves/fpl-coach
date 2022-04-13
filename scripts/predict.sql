WITH Q1 AS (
  SELECT player_name,
    position,
    gameweek,
    player_gws.team AS team,
    opponent AS opponent,
    completed,
    total_points,
    xP,
    price
  FROM player_gws
    INNER JOIN team_gws ON player_gws.fixture_id = team_gws.fixture_id
    AND player_gws.team = team_gws.team
    INNER JOIN players ON player_gws.player_name = players.fpl_name
)
SELECT player_name AS name,
  IF (
    MIN(gameweek) = MAX(gameweek),
    MIN(gameweek),
    CONCAT(MIN(gameweek), "-", MAX(gameweek))
  ) AS gws,
MIN(position) AS position,
{}
-- GROUP_CONCAT(opponent SEPARATOR ', ') AS opponents,
ROUND(SUM(xP), 3) AS xP,
SUM(total_points) AS points,
ROUND(ROUND(SUM(xP), 3) - SUM(total_points)) AS delta
FROM Q1
WHERE {}
GROUP BY player_name
ORDER BY xP DESC