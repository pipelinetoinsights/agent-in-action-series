# Agents in Action #7 — every primitive from the series, each earning its place.
# Run: python pipeline_monitor.py  (requires ANTHROPIC_API_KEY in your environment)
# First run seeds warehouse.db (via mcp_server.py) and records a baseline.
# Run simulate_drop.py, then run this again to see the agent catch it.
#
# Why each primitive is here, not just because it exists:
# - Tool + MCP: check_table needs an exact number, not a guess — and it now has
#   two independent consumers (this script, and the escalation skill an
#   engineer reaches for in Claude Code), which is Part 3's actual signal to
#   extract an MCP server instead of a private function. See mcp_server.py.
# - Sub-agents: three tables are independent work (Part 5's parallelism
#   signal), and keeping each table's reasoning in its own isolated context
#   avoids the cross-table mix-ups Part 5 warned about — one agent juggling
#   all three tables at once is exactly how a summary ends up attributing
#   the wrong table's numbers to the wrong table.
# - Memory: specifically episodic memory (Part 6's CoALA taxonomy) — kept as
#   an append-only SQLite log, not an overwritten JSON snapshot. A reader on
#   Part 6 pointed out that overwriting loses history: you can answer "did
#   this change since last time" but never "what was true last Tuesday."
#   Every run here INSERTs a new row instead of replacing the old one, so
#   that question stays answerable — see Part 6's own JSON-to-SQLite
#   graduation path ("when you need to query history, not just the last
#   snapshot").
# - Skill: deliberately NOT called from this script. The escalation runbook
#   is procedural memory a human follows, not a step this automation should
#   take unsupervised — see .claude/skills/pipeline-incident-escalation/.

import asyncio
import sqlite3
from concurrent.futures import ThreadPoolExecutor

from anthropic import Anthropic
from fastmcp import Client

client = Anthropic()  # reads ANTHROPIC_API_KEY from your environment

MODEL = "claude-haiku-4-5"  # workers are narrow, single-purpose calls — a small model is enough
MEMORY_DB = "episodic_memory.db"
MCP_SERVER = "mcp_server.py"
TABLES_TO_MONITOR = ["orders", "customers", "payments"]  # swap in your own table names
THRESHOLD_PCT = 10  # flag a row-count drop bigger than this, in percent

SUMMARY_ROLE = """You are a reporting worker for a data pipeline monitor.
Given a table's classification (ANOMALY, OK, or BASELINE) and its row counts,
write a single sentence an on-call data engineer could read in a Slack alert.
Be calm and specific. Lead with the table name. If the classification is
ANOMALY, briefly suggest one or two likely causes (e.g. failed ingestion,
an upstream schema change, an unexpected delete)."""


def classify_anomaly(table_name: str, current_row_count: int, previous: dict) -> str:
    """Deterministic, not an LLM call: comparing a number against a fixed
    threshold is a rule, not a judgement call requiring interpretation — so
    it doesn't belong to a model. See Part 2's own test for when a tool is
    the wrong choice: 'if a task runs the same way every time, with no
    decision about whether or which step to take, you don't need an agent.'"""
    if table_name not in previous:
        return "BASELINE"
    previous_count = previous[table_name]["row_count"]
    if previous_count == 0:
        return "OK"  # nothing to compute a percentage drop against
    drop_pct = (previous_count - current_row_count) / previous_count * 100
    return "ANOMALY" if drop_pct > THRESHOLD_PCT else "OK"


async def gather_table_stats(tables: list[str]) -> dict[str, dict]:
    """Tool calls over MCP: one client session, one real query per table.
    Sequential on purpose — these are fast local queries, and mixing an
    asyncio MCP client with the thread-based sub-agent fan-out below isn't
    worth it for three queries. Parallelising this is a fine later upgrade
    if you point it at a slower warehouse."""
    async with Client(MCP_SERVER) as mcp_client:
        return {
            table: (await mcp_client.call_tool("check_table", {"table_name": table})).data
            for table in tables
        }


def init_memory_db() -> None:
    """Create the append-only readings log on first run. Every check ever
    made lives here as its own row — nothing is ever updated or deleted."""
    conn = sqlite3.connect(MEMORY_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            table_name TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            checked_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def load_memory() -> dict:
    """Return each table's single most recent reading — the only thing
    classify_anomaly needs. The full history stays in the readings table,
    queryable later; this just isn't the query that needs it."""
    conn = sqlite3.connect(MEMORY_DB)
    rows = conn.execute("""
        SELECT table_name, row_count, checked_at FROM readings
        WHERE (table_name, checked_at) IN (
            SELECT table_name, MAX(checked_at) FROM readings GROUP BY table_name
        )
    """).fetchall()
    conn.close()
    return {table_name: {"row_count": row_count, "checked_at": checked_at} for table_name, row_count, checked_at in rows}


def save_memory(memory: dict) -> None:
    """Append this run's readings. Never overwrites a previous row — that's
    the whole fix: an overwritten JSON file can answer 'did this change
    since last time' but never 'what was true last Tuesday.' An append-only
    log can answer both."""
    conn = sqlite3.connect(MEMORY_DB)
    conn.executemany(
        "INSERT INTO readings (table_name, row_count, checked_at) VALUES (?, ?, ?)",
        [(table, data["row_count"], data["checked_at"]) for table, data in memory.items()],
    )
    conn.commit()
    conn.close()


def run_subagent(role_prompt: str, task: str) -> str:
    """Run one focused sub-agent: a Claude call with its own system prompt."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=role_prompt,
        messages=[{"role": "user", "content": task}],
    )
    return response.content[0].text


def check_and_report(current: dict, previous: dict) -> tuple[dict, str]:
    """One worker's reasoning for one table: classify the already-fetched
    reading with a plain rule, then have the sub-agent write it up. The row
    count itself came from gather_table_stats — this worker never touches
    the database directly, and it never decides ANOMALY vs. OK either."""
    table_name = current["table"]
    classification = classify_anomaly(table_name, current["row_count"], previous)  # deterministic, not a model call

    if table_name in previous:
        task = (
            f"Table: {table_name}\n"
            f"Classification: {classification}\n"
            f"Previous row count: {previous[table_name]['row_count']}\n"
            f"Current row count: {current['row_count']}"
        )
    else:
        task = f"Table: {table_name}\nClassification: {classification}\nCurrent row count: {current['row_count']}\nNo previous run available."

    summary = run_subagent(SUMMARY_ROLE, task)  # the one Claude call this worker makes
    return current, summary


def run_health_check(tables: list[str]) -> None:
    init_memory_db()
    memory = load_memory()  # episodic memory: the most recent reading per table

    current_stats = asyncio.run(gather_table_stats(tables))  # tool, via MCP

    # sub-agents: one worker per table, fanned out in parallel
    with ThreadPoolExecutor(max_workers=len(tables)) as pool:
        futures = [pool.submit(check_and_report, current_stats[table], memory) for table in tables]
        results = [future.result() for future in futures]

    new_memory = {}
    for current, summary in results:
        print(f"\n=== {current['table']} ===\n{summary}")
        new_memory[current["table"]] = {
            "row_count": current["row_count"],
            "checked_at": current["checked_at"],
        }

    save_memory(new_memory)  # episodic memory: appended as new rows, past readings untouched


if __name__ == "__main__":
    run_health_check(TABLES_TO_MONITOR)
