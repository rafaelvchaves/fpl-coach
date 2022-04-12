SELECT player_name,
  position,
  player_gws.fixture_id AS fixture_id,
  T1.gameweek,
  T1.kickoff_date,
  player_gws.team AS team,
  T1.opponent AS opponent,
  T1.completed,
  minutes,
  npxG,
  xA,
  bonus,
  total_points,
  price,
  T1.avg_team_xG AS avg_team_xG,
  T2.avg_team_xGA AS avg_team_xGA,
  T2.avg_team_xG AS avg_opponent_xG,
  T2.avg_team_xGA AS avg_opponent_xGA
FROM player_gws
  INNER JOIN team_gws AS T1 ON player_gws.fixture_id = T1.fixture_id
  AND player_gws.team = T1.team
  INNER JOIN team_gws AS T2 ON T1.opponent = T2.team
  AND T1.fixture_id = T2.fixture_id
  INNER JOIN players ON player_gws.player_name = players.fpl_name