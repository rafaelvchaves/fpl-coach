mysql -p'password' -u root fplcoachdb < init.sql
source $(poetry env info --path)/bin/activate
cd ../src
python teams.py && python players.py && python fixtures.py && python player_fpl_data.py && python player_understat_data.py && python model.py