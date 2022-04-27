SELECT 
  players.fpl_id AS player_id,
  players.fpl_name AS player_name,
  position,
  player_gws.fixture_id AS fixture_id,
  T1.gameweek,
  T1.kickoff_date,
  player_gws.team AS team,
  T1.opponent AS opponent,
  T1.completed,
  npxG,
  xA,
  goals_scored,
  assists,
  bonus,
  clean_sheets,
  goals_conceded,
  minutes,
  player_gws.total_points as total_points,
  T1.avg_team_xG AS avg_team_xG,
  T1.avg_team_xGA AS avg_team_xGA,
  T2.avg_team_xG AS avg_opponent_xG,
  T2.avg_team_xGA AS avg_opponent_xGA,
  T1.proj_score AS proj_score,
  T1.opponent_proj_score AS opponent_proj_score,
  goal_xP,
  assist_xP,
  cs_xP,
  bonus_xP,
  concede_xP,
  xP
FROM player_gws
  INNER JOIN team_gws AS T1 ON player_gws.fixture_id = T1.fixture_id
  AND player_gws.team = T1.team
  INNER JOIN player_gws_predicted ON player_gws.fixture_id = player_gws_predicted.fixture_id
  AND player_gws.player_id = player_gws_predicted.player_id
  INNER JOIN team_gws AS T2 ON T1.opponent = T2.team
  AND T1.fixture_id = T2.fixture_id
  INNER JOIN players ON player_gws.player_id = players.fpl_id
ORDER BY T1.kickoff_date, player_name