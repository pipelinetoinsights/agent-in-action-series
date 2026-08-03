# Agents in Action #6 — read memory before reasoning, write memory after.
# Run: python memory_agent.py  (requires ANTHROPIC_API_KEY in your environment)
# First run seeds warehouse.db and records a baseline.
# Run simulate_drop.py, then run this again to see the agent notice the drop.

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY from your environment

MODEL = "claude-sonnet-4-6"
MEMORY_FILE = Path("agent_memory.json")
DB_PATH = "warehouse.db"

ALLOWED_TABLES = {"orders", "customers"}


def setup_demo_db() -> None:
    """Seed warehouse.db with 10,000 orders and 5,400 customers on first run."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, amount REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT)")
    conn.executemany("INSERT OR IGNORE INTO orders VALUES (?, ?)", [(i, i * 9.99) for i in range(1, 10001)])
    conn.executemany("INSERT OR IGNORE INTO customers VALUES (?, ?)", [(i, f"Customer {i}") for i in range(1, 5401)])
    conn.commit()
    conn.close()


def load_memory() -> dict:
    """Read prior findings. Returns empty dict on first ever run."""
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text())
    return {}


def save_memory(memory: dict) -> None:
    """Persist findings for the next run, without risking a corrupt file."""
    tmp_file = MEMORY_FILE.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(memory, indent=2, default=str))
    os.replace(tmp_file, MEMORY_FILE)


def check_table(table_name: str) -> dict:
    """Return the real current row count for a table in warehouse.db."""
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Unknown table: {table_name}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    conn.close()
    return {
        "table": table_name,
        "row_count": row_count,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def build_system_prompt(memory: dict) -> str:
    if not memory:
        return (
            "You are a pipeline health monitor. This is your first run, "
            "so you have no previous findings to compare against. "
            "Record a baseline for each table you check."
        )
    return (
        "You are a pipeline health monitor. Here is what you recorded on "
        f"your last run:\n\n{json.dumps(memory, indent=2)}\n\n"
        "Compare today's findings against this. Call out anything that "
        "changed significantly and explain why it might matter."
    )


def run_health_check(tables: list[str]) -> None:
    memory = load_memory()

    # Gather today's facts via our tool.
    current = {t: check_table(t) for t in tables}

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=build_system_prompt(memory),
        messages=[{
            "role": "user",
            "content": (
                "Today's table readings:\n"
                f"{json.dumps(current, indent=2)}\n\n"
                "Summarise pipeline health and flag any changes."
            ),
        }],
    )

    print(response.content[0].text)

    # Persist today's readings as tomorrow's baseline.
    new_memory = {
        t: {"row_count": current[t]["row_count"],
            "checked_at": current[t]["checked_at"]}
        for t in tables
    }
    save_memory(new_memory)


if __name__ == "__main__":
    if not Path(DB_PATH).exists():
        setup_demo_db()
    run_health_check(["orders", "customers"])
