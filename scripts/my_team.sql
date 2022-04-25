WITH GWTEAM AS (
  SELECT player_id,
    gameweek
  FROM manager_gws
    INNER JOIN players ON manager_gws.player_id = players.fpl_id
  WHERE manager_id = 505657
    AND gameweek >= {}
    AND gameweek <= {}
  ORDER BY position
),
predicted_points AS (
  SELECT fpl_id,
    players.fpl_name AS player_name,
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
    INNER JOIN players ON player_gws.player_id = players.fpl_id
    INNER JOIN player_gws_predicted ON player_gws.player_id = player_gws_predicted.player_id
    AND player_gws.fixture_id = player_gws_predicted.fixture_id
  WHERE fpl_id != 248
  GROUP BY fpl_id,
    player_name,
    position,
    gameweek,
    team
)
SELECT predicted_points.gameweek AS gameweek,
  player_name,
  position,
  opponent,
  total_points,
  xP
FROM GWTEAM
  INNER JOIN predicted_points ON GWTEAM.player_id = predicted_points.fpl_id
  AND GWTEAM.gameweek = predicted_points.gameweek
ORDER BY xP DESC