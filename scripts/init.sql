USE fplcoachdb;

DROP TABLE IF EXISTS player_gws;
DROP TABLE IF EXISTS player_gws_extra;
DROP TABLE IF EXISTS team_gws;
DROP TABLE IF EXISTS manager_gws;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS managers;
DROP TABLE IF EXISTS fixtures;
DROP TABLE IF EXISTS teams;

CREATE TABLE IF NOT EXISTS teams(
  fpl_id INT NOT NULL,
  fpl_name VARCHAR(255) PRIMARY KEY,
  understat_name VARCHAR(255) NOT NULL,
  fte_name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS players(
  fpl_id INT PRIMARY KEY,
  understat_id INT NOT NULL,
  fpl_name VARCHAR(255) NOT NULL,
  position CHAR NOT NULL,
  team_name VARCHAR(255) NOT NULL,
  FOREIGN KEY (team_name) REFERENCES teams(fpl_name)
);

CREATE TABLE IF NOT EXISTS managers(
  id INT PRIMARY KEY,
  manager_name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS fixtures(
  fpl_id INT PRIMARY KEY,
  understat_id INT NOT NULL,
  gameweek INT,
  kickoff_date DATE,
  completed BOOLEAN,
  home_team VARCHAR(255) NOT NULL,
  away_team VARCHAR(255) NOT NULL,
  home_score INT,
  away_score INT,
  home_proj_score FLOAT(6, 3),
  away_proj_score FLOAT(6, 3),
  home_xG FLOAT(6, 3),
  away_xG FLOAT(6, 3),
  FOREIGN KEY (home_team) REFERENCES teams(fpl_name),
  FOREIGN KEY (away_team) REFERENCES teams(fpl_name)
);

CREATE TABLE IF NOT EXISTS team_gws(
  gameweek INT,
  kickoff_date DATE,
  fixture_id INT NOT NULL,
  completed BOOLEAN,
  team VARCHAR(255) NOT NULL,
  opponent VARCHAR(255) NOT NULL,
  home BOOLEAN NOT NULL,
  team_xG FLOAT(6, 3),
  team_xGA FLOAT(6, 3),
  proj_score FLOAT(6, 3),
  opponent_proj_score FLOAT(6, 3),
  avg_team_xG FLOAT(6, 3),
  avg_team_xGA FLOAT(6, 3),
  FOREIGN KEY (team) REFERENCES teams(fpl_name),
  FOREIGN KEY (opponent) REFERENCES teams(fpl_name),
  PRIMARY KEY (fixture_id, team)
);

CREATE TABLE IF NOT EXISTS player_gws(
  player_name VARCHAR(255) NOT NULL,
  fixture_id INT NOT NULL,
  team VARCHAR(255), -- not necessarily the same as team name from players table - players can move between EPL teams --
  minutes INT,
  npxG FLOAT(6, 3),
  xA FLOAT(6, 3),
  bonus INT,
  total_points INT,
  xP FLOAT(6, 3),
  price FLOAT(4, 1),
  FOREIGN KEY (fixture_id) REFERENCES fixtures(fpl_id),
  FOREIGN KEY (team) REFERENCES teams(fpl_name),
  PRIMARY KEY (player_name, fixture_id)
);

CREATE TABLE IF NOT EXISTS player_gws_extra(
  player_name VARCHAR(255) NOT NULL,
  fixture_id INT NOT NULL,
  goal_xP FLOAT(6, 3),
  assist_xP FLOAT(6, 3),
  bonus_xP FLOAT(6, 3),
  cs_xP FLOAT(6, 3),
  concede_xP FLOAT(6, 3),
  minutes_xP FLOAT(6, 3),
  xP FLOAT(6, 3),
  goal_points INT,
  assist_points INT,
  bonus_points INT,
  cs_points INT,
  concede_points INT,
  minutes_points INT,
  total_points INT,
  FOREIGN KEY (fixture_id) REFERENCES fixtures(fpl_id),
  PRIMARY KEY (player_name, fixture_id)
);

CREATE TABLE IF NOT EXISTS manager_gws(
  id INT AUTO_INCREMENT PRIMARY KEY,
  gameweek INT NOT NULL,
  manager_id INT,
  player_id INT,
  FOREIGN KEY (manager_id) REFERENCES managers(id),
  FOREIGN KEY (player_id) REFERENCES players(fpl_id)
);
