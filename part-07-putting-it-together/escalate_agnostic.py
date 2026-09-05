# Agents in Action #7 — the escalation skill, without Claude Code.
#
# Part 4 claimed that a Skill's *idea* — a runbook loaded only when a request
# matches, then followed — is universal, and that on another stack you'd
# build the same "load context on demand" behaviour yourself: a retrieval
# step, or a manual check, standing in for Claude Code's native discovery.
# This file proves that claim instead of just asserting it. No Claude Code,
# no .claude/skills/ folder convention — just SKILL.md read as a plain text
# file, and a hand-written version of the two things Claude Code normally
# does for you: deciding whether the skill applies, and loading its body
# only once it does.
#
# Run: python escalate_agnostic.py "An anomaly was flagged on the payments table. What should I do?"

import asyncio
import sqlite3
import sys
from pathlib import Path

from anthropic import Anthropic
from fastmcp import Client

client = Anthropic()  # swap for Ollama/OpenAI-compatible per Part 2 — nothing else here changes

MODEL = "claude-haiku-4-5"
MCP_SERVER = "mcp_server.py"
MEMORY_DB = "episodic_memory.db"  # the same append-only log pipeline_monitor.py writes
SKILL_FILE = Path(".claude/skills/pipeline-incident-escalation/SKILL.md")
TRIGGER_WORDS = {"anomaly", "row-count", "row count", "flagged", "incident", "okay"}


def load_skill() -> tuple[str, str]:
    """Split SKILL.md into its description and its body — the same two
    progressive-disclosure levels from Part 4. The description is small
    enough to always keep around (Level 1); the body only gets read once a
    request actually matches (Level 2)."""
    text = SKILL_FILE.read_text()
    _, frontmatter, body = text.split("---", 2)
    description = " ".join(frontmatter.split("description:", 1)[1].split())
    return description, body.strip()


def matches_skill(request: str) -> bool:
    """The DIY stand-in for Claude Code reading name+description and
    deciding to load a skill. This is a plain keyword check — a real
    implementation on another stack might use embeddings or a router LLM
    call instead. The point isn't that this exact method is best; it's that
    *something* has to do this matching on every stack, native feature or
    not."""
    request_lower = request.lower()
    return any(word in request_lower for word in TRIGGER_WORDS)


async def check_table_via_mcp(table_name: str) -> dict:
    """Same MCP server, same tool pipeline_monitor.py uses — MCP itself was
    never Claude-Code-specific (Part 3), so nothing changes here."""
    async with Client(MCP_SERVER) as mcp_client:
        return (await mcp_client.call_tool("check_table", {"table_name": table_name})).data


def load_last_baseline(table_name: str) -> int | None:
    """Read the reading the monitor had *before* the one that presumably
    triggered this alert — the same episodic memory log pipeline_monitor.py
    appends to. The most recent row is the anomalous reading itself; the
    row before it is the baseline it was compared against. Returns None if
    there's no prior reading to compare."""
    conn = sqlite3.connect(MEMORY_DB)
    row = conn.execute(
        "SELECT row_count FROM readings WHERE table_name = ? ORDER BY checked_at DESC LIMIT 1 OFFSET 1",
        (table_name,),
    ).fetchone()
    conn.close()
    return row[0] if row else None


def run_escalation(request: str, table_name: str) -> None:
    description, runbook = load_skill()

    if not matches_skill(request):
        print(f"No match against this skill's trigger ({description[:60]}...) — answering without the runbook.")
        return

    current = asyncio.run(check_table_via_mcp(table_name))  # Step 1 of the runbook, done for real
    baseline = load_last_baseline(table_name)  # the monitor's own memory, not a guess

    baseline_line = (
        f"Monitor's last recorded baseline for {table_name}: {baseline}"
        if baseline is not None
        else f"No prior baseline recorded for {table_name} — this is the only reading in memory so far."
    )
    task = f"{request}\n\nCurrent reading from check_table: {current}\n{baseline_line}"
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=runbook,  # the body only enters the prompt now — after the match, not before
        messages=[{"role": "user", "content": task}],
    )
    print(response.content[0].text)


if __name__ == "__main__":
    request = sys.argv[1] if len(sys.argv) > 1 else "An anomaly was flagged on the payments table. What should I do?"
    run_escalation(request, table_name="payments")
