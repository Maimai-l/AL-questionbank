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


# ------------------------------------------------------------------ tags
# questions.tags: a JSON list of labels, NULL on rows that have none (every CAIE
# row). "精选" marks curated questions from outside the past papers (textbook
# exercises, pipeline/books/book_questions.py); a second tag names the source.
# The column is added on first use, so an older copy of the bank keeps working:
# readers select tags_column(con), which is NULL when the column is not there.

def ensure_tags(con):
    """Add questions.tags if it is missing (a migration; existing rows stay NULL)."""
    return add_column(con, "questions", "tags", "TEXT DEFAULT NULL")


def tags_column(con, alias="tags"):
    """`tags` for a SELECT list, or `NULL AS tags` on a bank without the column."""
    return "tags" if has_column(con, "questions", "tags") else f"NULL AS {alias}"


def tags_of(value):
    """The list a tags value holds ([] for NULL or anything unreadable)."""
    import json
    try:
        v = json.loads(value) if value else []
    except ValueError:
        return []
    return [str(t) for t in v] if isinstance(v, list) else []


def tag_clause(con, tag):
    """SQL condition and argument for "has this tag", or ("0", []) without the column."""
    if not has_column(con, "questions", "tags"):
        return "0", []
    return "EXISTS (SELECT 1 FROM json_each(questions.tags) WHERE json_each.value = ?)", [tag]
