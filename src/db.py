import math
import mysql.connector
import pandas as pd
from mysql.connector.locales.eng import client_error
from mysql.connector.errors import IntegrityError
from sqlalchemy import create_engine
from typing import Any, Dict, List, Optional, Tuple, Union


def isnan(s: Any) -> bool:
    """Checks if any value is nan."""
    try:
        return math.isnan(float(s))
    except:
        return False


def prepare_string(val: Any) -> str:
    """Converts a value into a string to be used in a SQL query.

    Args:
        val: The value to convert to a string.

    Returns:
        A string conversion of the value. For None values, the string "NULL" is
        retruned. Strings are wrapped in single quotes, and apostrophes are
        also escaped. For example,
        prepare_string("N'Golo Kante") yields "'N''Golo Kante'".
    """
    if val is None or isnan(val):
        return "NULL"
    elif isinstance(val, str):
        return "'{}'".format(val.replace("'", "''"))
    else:
        return str(val)


def get_update_sequence(row: Dict[str, Any], sep: str) -> str:
    """Returns a string of updates for a SQL query.

    Args:
        row: A dictionary mapping a column name to a value for that column.
        sep: A string separator to place between each clause.

    Returns:
        A string of clauses in the form "column_name = val", separated by sep.
        Strings are automatically escaped. For example,
        get_update_sequence({"a": 1, "b": "hello"}, ",") returns
        "a = 1,b = 'hello'".
    """
    return sep.join([col + " = " + prepare_string(val) for col, val in row.items()])


class MySQLManager:

    def __init__(self):
        self.cnx = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database="fplcoachdb",
        )
        self.eng = create_engine("mysql://root:password@localhost/fplcoachdb")

    def insert_rows(self, table_name: str, rows: List[Dict[str, Any]]) -> None:
        """Insert rows into specified table.

        Args:
            table_name: string, the name of the table to insert rows into.
            rows: A list of rows, each of which is represented by a dictionary
              mapping column names to values.
        """
        cursor = self.cnx.cursor()
        col_names = rows[0].keys()
        cols = ",".join(col_names)
        for row in rows:
            inserts = ",".join([prepare_string(val) for _, val in row.items()])
            updates = get_update_sequence(row, ",")
            cmd = "INSERT INTO {} ({}) VALUES ({}) ON DUPLICATE KEY UPDATE {}".format(
                table_name, cols, inserts, updates)
            cursor.execute(cmd)
        self.cnx.commit()

    def update_row(self, table_name: str, where_clause: dict, set_clause: dict) -> None:
        """Updates a row in the specified table.

        Args:
            table_name: The name of the table to update.
            where_clause: A dictionary representing the WHERE clause. For example,
              {"a": 1, "b": 2} represents the clause "WHERE a = 1 AND b = 2".
            set_clause: A dictionary mapping column names to values to set.
        """
        cursor = self.cnx.cursor()
        updated_vals = get_update_sequence(set_clause, ",")
        rows_affected = get_update_sequence(where_clause, " AND ")
        cmd = "UPDATE {} SET {} WHERE {}".format(
            table_name, updated_vals, rows_affected)
        cursor.execute(cmd)
        self.cnx.commit()

    def exec_query(self, query) -> List[tuple]:
        """Executes a SQL query and fetches results."""
        cursor = self.cnx.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def get_df(self, query: str) -> pd.DataFrame:
        """Returns results of SQL query as a pandas dataframe."""
        return pd.read_sql(query, self.eng)

    def get_fixtures(self, gameweeks: Optional[Union[int, Tuple]] = None) -> list:
        """Retrieves a list of fixtures in given gameweek.

        Args:
            gameweeks: Either a single integer representing the gameweek to
              filter by, or a tuple (start, end), which gets all gameweeks
              from start to end, inclusively. If this argument is not specified,
              all gameweeks will be retrieved.
        """
        cursor = self.cnx.cursor()
        query = "SELECT * FROM fixtures"
        if isinstance(gameweeks, tuple):
            lower = gameweeks[0] if gameweeks[0] is not None else 1
            upper = gameweeks[1] if gameweeks[1] is not None else 38
            query += " WHERE gameweek >= {} AND gameweek <= {}".format(
                lower, upper)
        elif isinstance(gameweeks, int):
            query += " WHERE gameweek = {}".format(gameweeks)
        query += " ORDER BY gameweek"
        cursor.execute(query)
        return cursor.fetchall()
