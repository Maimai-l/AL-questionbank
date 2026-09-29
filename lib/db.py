"""Opening the bank.

Ten scripts each defaulted a `db` argument to the bare string "caie.db", which
only worked while the working directory happened to be the project root. They
now default to `None` and call `connect()`, which falls back to `paths.DB`.
"""
import sqlite3

from lib import paths


def connect(path=None, row_factory=True):
    con = sqlite3.connect(path or paths.DB)
    if row_factory:
        con.row_factory = sqlite3.Row
    return con


def has_column(con, table, column):
    return any(r[1] == column for r in con.execute(f"PRAGMA table_info({table})"))


def add_column(con, table, column, decl="TEXT"):
    """Idempotent ALTER TABLE — several pipeline steps bolt on their own column."""
    if not has_column(con, table, column):
        con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")
        return True
    return False
