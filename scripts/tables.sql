USE fplcoach_db;

CREATE TABLE IF NOT EXISTS teams(
  id INT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  understat_name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS players(
  fpl_id INT PRIMARY KEY,
  understat_id INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  position CHAR NOT NULL,
  team_name INT,
  FOREIGN KEY (team_name) REFERENCES teams(name)
);

CREATE TABLE IF NOT EXISTS managers(
  id INT PRIMARY KEY,
  name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS fixtures(
  id INT PRIMARY KEY,
  gameweek INT,
  kickoff_date DATETIME,
  home_team VARCHAR(255),
  home_score INT,
  away_score INT,
  away_team VARCHAR(255),
  home_xg FLOAT,
  away_xg FLOAT,
  FOREIGN KEY home_team REFERENCES teams(name),
  FOREIGN KEY away_team REFERENCES teams(name)
);

-- CREATE TABLE IF NOT EXISTS team_gws(
--   id INT AUTO_INCREMENT PRIMARY KEY,
--   team_id INT,
--   gameweek INT NOT NULL,
--   offensive_rating FLOAT,
--   defensive_rating FLOAT,
--   FOREIGN KEY (team_id) REFERENCES teams(id)
-- );

CREATE TABLE IF NOT EXISTS player_gws(
  player_id INT,
  gameweek INT,
  fixture_id INT,
  team_id INT,
  opponent_id INT,
  minutes_played INT,
  npxg FLOAT,
  xa FLOAT,
  bonus_points INT,
  total_points INT,
  price FLOAT,
  FOREIGN KEY (player_id) REFERENCES players(id),
  FOREIGN KEY (fixture_id) REFERENCES fixtures(id),
  FOREIGN KEY (team_id) REFERENCES teams(id),
  FOREIGN KEY (opponent_id) REFERENCES teams(id),
  PRIMARY KEY (player_id, fixture_id)
);

-- CREATE TABLE IF NOT EXISTS manager_gws(
--   id INT AUTO_INCREMENT PRIMARY KEY,
--   gameweek INT NOT NULL,
--   manager_id INT,
--   player_id INT,
--   FOREIGN KEY (manager_id) REFERENCES managers(id),
--   FOREIGN KEY (player_id) REFERENCES players(id)
-- );
