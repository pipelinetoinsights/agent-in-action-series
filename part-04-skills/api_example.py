"""
Part 4 — Skills: run the data-quality-runbook Skill via the Claude API.

A custom Skill must be uploaded once via the Skills API before you can
reference it (see upload_skill.py). That upload returns a skill_id like
"skill_01JAbc..." — paste it into SKILL_ID below.

If you'd rather skip the upload entirely, use the Claude Code path in the
README — it needs no API wiring at all.

    pip install anthropic
    export ANTHROPIC_API_KEY="sk-ant-..."
    python api_example.py
"""

import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

SKILL_ID = "skill_abc123"  # <- from the one-time upload (see upload_skill.py)

response = client.beta.messages.create(
    model="claude-opus-4-8",
    max_tokens=2048,
    # One beta flag turns on Skills. The GA code-execution tool below is
    # generally available and needs no beta header of its own.
    betas=["skills-2025-10-02"],
    container={
        "skills": [
            {"type": "custom", "skill_id": SKILL_ID, "version": "latest"}
        ]
    },
    # The sandbox where the Skill reads SKILL.md and runs the bundled script.
    tools=[{"type": "code_execution_20260521", "name": "code_execution"}],
    messages=[
        {
            "role": "user",
            "content": "Quality-check the finance.daily_revenue table before we publish it.",
        }
    ],
)

# response.content is a list of blocks — pull out the text the agent wrote.
print("".join(b.text for b in response.content if b.type == "text"))
