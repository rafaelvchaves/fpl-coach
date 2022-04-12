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
  WHERE {}
)
SELECT player_name,
  CONCAT(MIN(gameweek), "-", MAX(gameweek)) AS gameweeks,
  MIN(position) AS position,
  GROUP_CONCAT(opponent SEPARATOR ', ') AS opponents,
  ROUND(SUM(xP), 3) AS xP
FROM Q1
GROUP BY player_name
ORDER BY xP DESC