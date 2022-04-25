A point prediction tool for Fantasy Premier League (FPL).

Files:
  - teams.py: Loads the 20 teams from the current season.
  - players.py: Loads all static player data from FPL, including player FPL id,
    Understat id, name, team, and position.
  - fixtures.py: Loads fixture data from FPL as well as team xG data
    from Understat and projected scores from FiveThirtyEight.
  - player_fpl_data.py: Loads individual gameweek stats for each player,
    including goals, assists, clean sheets, bonus points, and goals
    conceded.
  - player_understat_data.py: Loads data from Understat for every fixture
    this season; specifically, the npxG and xA stats for each player.
  - preprocess.py: Merges together team and player data and preprocesses
    the data to be put into the model.
  - model.py: Runs a point prediction model on the preprocessed data.
  - predict.py: Displays point predictions for different gameweeks.
  - managers.py: Loads in a FPL manager's complete team history.