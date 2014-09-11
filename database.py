import sqlite3

"""Helper function for database access."""


def connect(dbname):
    """Connect to the script server database."""
    return sqlite3.connect(dbname, detect_types=sqlite3.PARSE_COLNAMES)
