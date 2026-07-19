"""
Part 4 — Skills: upload the custom data-quality-runbook Skill once.

Creates the Skill via the Skills API and prints the returned skill_id,
which you then paste into api_example.py (SKILL_ID).

    pip install anthropic
    export ANTHROPIC_API_KEY="sk-ant-..."
    python upload_skill.py

You do NOT need this for the Claude Code path in the README — Claude Code
loads the Skill straight from the folder, no upload required.

Docs: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/quickstart
"""

from pathlib import Path

import anthropic
from anthropic.lib import files_from_dir  # SDK helper: loads a Skill folder

# The Skills API is beta — set the header at client init.
client = anthropic.Anthropic(
    default_headers={"anthropic-beta": "skills-2025-10-02"},
)

SKILL_DIR = Path(__file__).parent / "data-quality-runbook"

# files_from_dir walks the folder (SKILL.md, thresholds.md, scripts/...) and
# packages it for upload — no manual file handling needed.
skill = client.beta.skills.create(
    display_title="Data Quality Runbook",
    files=files_from_dir(str(SKILL_DIR)),
)

print(f"skill_id:       {skill.id}")
print(f"latest_version: {skill.latest_version}")
print("\nPaste skill_id into api_example.py (SKILL_ID).")
