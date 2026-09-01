# Agents in Action #7 — the Part 2 tool, exposed over MCP (Part 3).
# Run standalone for testing: python mcp_server.py
# In normal use, pipeline_monitor.py launches this as a subprocess automatically.
#
# Why MCP here and not a plain function call (Part 2's version)? Because this
# capability now has two independent consumers: pipeline_monitor.py (the
# automated check) and an on-call engineer's Claude Code session investigating
# an alert (see the escalation skill). Per Part 3's rule — extract to MCP the
# moment a second client needs the same tool — that's exactly this situation.
# It also keeps the warehouse connection out of both clients' code.

import sqlite3
from datetime import datetime, timezone

from fastmcp import FastMCP

mcp = FastMCP("Warehouse")

DB_PATH = "warehouse.db"
ALLOWED_TABLES = {"orders", "customers", "payments"}


def setup_demo_db() -> None:
    """Seed warehouse.db with realistic row counts on first run."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, amount REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, amount REAL)")
    conn.executemany("INSERT OR IGNORE INTO orders VALUES (?, ?)", [(i, i * 9.99) for i in range(1, 10001)])
    conn.executemany("INSERT OR IGNORE INTO customers VALUES (?, ?)", [(i, f"Customer {i}") for i in range(1, 5401)])
    conn.executemany("INSERT OR IGNORE INTO payments VALUES (?, ?)", [(i, i * 19.99) for i in range(1, 9001)])
    conn.commit()
    conn.close()


@mcp.tool
def check_table(table_name: str) -> dict:
    """Return the real current row count for a table in the warehouse.
    Point DB_PATH at your real warehouse connection in production."""
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Table not allowed: {table_name}")
    conn = sqlite3.connect(DB_PATH)
    # table_name is restricted to ALLOWED_TABLES above, safe to interpolate
    row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    conn.close()
    return {
        "table": table_name,
        "row_count": row_count,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import os

    if not os.path.exists(DB_PATH):
        setup_demo_db()
    mcp.run()  # defaults to stdio transport — fine for one local script and one local Claude Code session
