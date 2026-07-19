# Part 4 — Skills: Teaching Your Agent Your Workflows

Code for [Agents in Action #4](https://pipeline2insights.substack.com) on [Pipeline to Insights](https://pipeline2insights.substack.com).

In Part 2 we built a **tool** (a function the agent calls) and in Part 3 we exposed it over **MCP**. Here we package a *procedure* — a data-quality runbook — as a **Skill**: a folder with a `SKILL.md` the agent loads only when it's relevant.

## The Skill

```
data-quality-runbook/
├── SKILL.md            (the runbook — instructions + trigger description)
├── thresholds.md       (per-schema thresholds — Level 3, loaded on demand)
└── scripts/
    └── run_checks.py    (deterministic validation — output only enters context)
```

The `run_checks.py` demo returns a deliberately failing `pk_unique` so you can see the FAIL path end to end. Swap in a real warehouse connection where noted.

## Run it two ways

### Option A — Claude Code (no upload, no API wiring)

Drop the Skill where Claude Code looks for it, then just ask:

```bash
mkdir -p .claude/skills
cp -r data-quality-runbook .claude/skills/
```

```
> Quality-check finance.daily_revenue before I publish it
```

Claude Code sees the Skill's metadata, matches the request, loads the runbook, runs `run_checks.py`, applies the thresholds, and reports PASS/FAIL. Commit `.claude/skills/` to share the runbook with your whole team.

> **Confirm it fired:** ask *"which skill did you use?"* — if the answer is "none," your description didn't match the request; tighten it.

### Option B — Claude API (custom Skill)

A custom Skill must be uploaded once, then referenced by its `skill_id`.

```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

python upload_skill.py          # prints a skill_id like skill_01JAbc...
# paste that id into SKILL_ID in api_example.py
python api_example.py
```

`api_example.py` uses the GA config: the `code_execution_20260521` tool (no code-execution beta header) plus the `skills-2025-10-02` beta.

## Files

| File | What it does |
|------|-------------|
| `data-quality-runbook/SKILL.md` | The runbook: trigger `description` + the procedure |
| `data-quality-runbook/thresholds.md` | Per-schema freshness / null-rate thresholds |
| `data-quality-runbook/scripts/run_checks.py` | Deterministic checks (demo returns a failing PK check) |
| `upload_skill.py` | One-time upload of the custom Skill via the Skills API |
| `api_example.py` | Runs the Skill through the Messages API |

> **Heads up:** Skills and the Skills API are beta — flags and parameter names evolve. If something errors, check the current [Agent Skills docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/quickstart). The concept — a folder the agent loads on demand — is stable.

> **Security:** A Skill can run code and read files. Only install Skills from sources you trust, and read every bundled file before using a third-party Skill.
