SELECT fpl_name
FROM manager_gws
  INNER JOIN players ON manager_gws.player_id = players.fpl_id
WHERE manager_id = 505657
  AND gameweek = {}
ORDER BY position
