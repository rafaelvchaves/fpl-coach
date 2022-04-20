WITH Q1 AS (
  SELECT 
    player_gws.player_name AS player_name,
    position,
    gameweek,
    player_gws.team AS team,
    IF (
      COUNT(opponent) > 1,
      CONCAT('[', GROUP_CONCAT(opponent SEPARATOR ','), ']'),
      MIN(opponent)
    ) AS opponent,
    SUM(total_points) AS total_points,
    SUM(xP) as xP
    FROM player_gws
    INNER JOIN team_gws ON player_gws.fixture_id = team_gws.fixture_id
    AND player_gws.team = team_gws.team
    INNER JOIN players ON player_gws.player_name = players.fpl_name
    INNER JOIN player_gws_predicted ON player_gws.player_name = player_gws_predicted.player_name
    AND player_gws.fixture_id = player_gws_predicted.fixture_id
  GROUP BY player_name,
    position,
    gameweek,
    team
)
SELECT player_name AS name,
  IF (
    MIN(gameweek) = MAX(gameweek),
    MIN(gameweek),
    CONCAT(MIN(gameweek), "-", MAX(gameweek))
  ) AS gws,
  position,
  {}
FROM Q1
WHERE {}
GROUP BY {}