import os
import sqlite3
import argparse
import sys
from typing import List, Tuple

#!/usr/bin/env python3
# filepath: /path/to/nuna-edu-toolkit/snippets/db_read.py
"""
Simple SQLite inspector for runtime/data/db/app.sqlite

Usage examples:
    python db_read.py                 # list tables and row counts
    python db_read.py --table users   # show schema + first rows for table
    python db_read.py --db /path/to/db.sqlite --table audio_data --limit 50
"""

DEFAULT_DB = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "runtime", "data", "db", "app.sqlite")
)


def connect(db_path: str):
        if not os.path.exists(db_path):
                print(f"DB not found: {db_path}", file=sys.stderr)
                sys.exit(2)
        # open read-only to avoid accidental writes
        uri = f"file:{os.path.abspath(db_path)}?mode=ro"
        return sqlite3.connect(uri, uri=True)


def list_tables(conn) -> List[Tuple[str, str]]:
        cur = conn.cursor()
        cur.execute(
                "SELECT name, type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return cur.fetchall()


def table_count(conn, table: str) -> int:
        cur = conn.cursor()
        try:
                cur.execute(f"SELECT COUNT(*) FROM \"{table}\"")
                return cur.fetchone()[0]
        except Exception:
                return -1


def table_schema(conn, table: str) -> str:
        cur = conn.cursor()
        cur.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
        )
        row = cur.fetchone()
        return row[0] if row else ""


def fetch_rows(conn, table: str, limit: int):
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM \"{table}\" LIMIT {limit}")
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        return cols, rows


def pretty_print_table(cols: List[str], rows: List[Tuple], maxcol=40):
        if not cols:
                print("<no columns>")
                return
        # compute widths
        widths = [len(c) for c in cols]
        for r in rows:
                for i, v in enumerate(r):
                        s = "" if v is None else str(v)
                        widths[i] = max(widths[i], min(len(s), maxcol))
        # header
        hdr = " | ".join(c.ljust(widths[i]) for i, c in enumerate(cols))
        sep = "-+-".join("-" * widths[i] for i in range(len(cols)))
        print(hdr)
        print(sep)
        for r in rows:
                cells = []
                for i, v in enumerate(r):
                        s = "" if v is None else str(v)
                        if len(s) > maxcol:
                                s = s[: maxcol - 3] + "..."
                        cells.append(s.ljust(widths[i]))
                print(" | ".join(cells))


def main():
        p = argparse.ArgumentParser(description="Inspect runtime SQLite DB (app.sqlite)")
        p.add_argument("--db", default=DEFAULT_DB, help="path to sqlite db")
        p.add_argument("--table", help="show specific table (schema + rows)")
        p.add_argument("--limit", type=int, default=20, help="row limit when showing table")
        args = p.parse_args()

        conn = connect(args.db)

        if args.table:
                tbl = args.table
                schema = table_schema(conn, tbl)
                if not schema:
                        print(f"Table not found: {tbl}", file=sys.stderr)
                        sys.exit(3)
                print(f"Schema for table '{tbl}':\n{schema}\n")
                count = table_count(conn, tbl)
                print(f"Row count: {count}\n")
                cols, rows = fetch_rows(conn, tbl, args.limit)
                pretty_print_table(cols, rows)
                if count > args.limit:
                        print(f"\n... shown {len(rows)}/{count} rows (use --limit to increase)")
        else:
                tables = list_tables(conn)
                if not tables:
                        print("No tables found.")
                        return
                print("Tables and row counts:\n")
                for name, typ in tables:
                        cnt = table_count(conn, name)
                        cnts = str(cnt) if cnt >= 0 else "?"
                        print(f"- {name} ({typ}) : {cnts}")
                print("\nRun with --table TABLE to inspect a table in detail.")


if __name__ == "__main__":
        main()