from datetime import datetime
from os.path import join
from constants import BACKUP_DIR
from db import MySQLManager
from utils import to_json, get_current_gw


def main():
    """Writes db tables to csv files under data/backups."""
    tables = [
        "teams",
        "players",
        "fixtures",
        "team_gws",
        "player_gws",
        "player_gws_predicted",
        "managers",
        "manager_gws"
    ]
    db = MySQLManager()
    for table in tables:
        table_file = join(BACKUP_DIR, f"{table}.csv")
        db.get_df(f"SELECT * FROM {table}").to_csv(table_file, index=False)

    metadata = {
        "last_updated": datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
        "gameweek": get_current_gw()
    }
    to_json(join(BACKUP_DIR, "metadata.json"), metadata)


if __name__ == "__main__":
    main()
