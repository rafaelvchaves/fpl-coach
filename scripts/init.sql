USE fplcoachdb;


DROP TABLE IF EXISTS player_gws;
DROP TABLE IF EXISTS team_gws;
DROP TABLE IF EXISTS manager_gws;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS managers;
DROP TABLE IF EXISTS fixtures;
DROP TABLE IF EXISTS teams;



CREATE TABLE IF NOT EXISTS teams(
  fpl_id INT NOT NULL,
  fpl_name VARCHAR(255) PRIMARY KEY,
  understat_name VARCHAR(255) NOT NULL
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
  id INT PRIMARY KEY,
  gameweek INT,
  kickoff_date DATETIME,
  home_team VARCHAR(255) NOT NULL,
  home_score INT,
  away_score INT,
  away_team VARCHAR(255) NOT NULL,
  home_xG FLOAT,
  away_xG FLOAT,
  FOREIGN KEY (home_team) REFERENCES teams(fpl_name),
  FOREIGN KEY (away_team) REFERENCES teams(fpl_name)
);

CREATE TABLE IF NOT EXISTS team_gws(
  gameweek INT,
  fixture_id INT NOT NULL,
  team VARCHAR(255) NOT NULL,
  opponent VARCHAR(255) NOT NULL,
  home BOOLEAN NOT NULL,
  team_xG FLOAT,
  team_xGA FLOAT,
  FOREIGN KEY (team) REFERENCES teams(fpl_name),
  FOREIGN KEY (opponent) REFERENCES teams(fpl_name),
  PRIMARY KEY (gameweek, team, opponent)
);

CREATE TABLE IF NOT EXISTS player_gws(
  player_id INT,
  fixture_id INT,
   -- not necessarily the same as team name from players table - players can move between EPL teams --
  team VARCHAR(255),
  minutes_played INT,
  npxG FLOAT,
  xA FLOAT,
  bonus INT,
  total_points INT,
  price FLOAT,
  FOREIGN KEY (player_id) REFERENCES players(fpl_id),
  FOREIGN KEY (fixture_id) REFERENCES fixtures(id),
  FOREIGN KEY (team) REFERENCES teams(fpl_name),
  PRIMARY KEY (player_id, fixture_id)
);

CREATE TABLE IF NOT EXISTS manager_gws(
  id INT AUTO_INCREMENT PRIMARY KEY,
  gameweek INT NOT NULL,
  manager_id INT,
  player_id INT,
  FOREIGN KEY (manager_id) REFERENCES managers(id),
  FOREIGN KEY (player_id) REFERENCES players(fpl_id)
);