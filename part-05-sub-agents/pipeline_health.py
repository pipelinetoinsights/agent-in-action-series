# Agents in Action #5 — orchestrator + three focused workers, fanned out in parallel.
# Run: python pipeline_health.py  (requires ANTHROPIC_API_KEY in your environment)

from concurrent.futures import ThreadPoolExecutor

from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY from your environment

MODEL = "claude-haiku-4-5"  # workers are narrow, single-purpose calls — a small model is enough

METRICS_ROLE = """You are a metrics extraction worker for a data pipeline.
Given raw table stats, restate the key metrics clearly and concisely.
Report only the numbers. Do not validate or judge them."""

VALIDATION_ROLE = """You are a data validation worker.
Given table metrics and a set of rules, check each metric against its rule.
Flag any violation as an ANOMALY with a one-line reason.
Be strict. Report only pass/fail per rule."""

SUMMARY_ROLE = """You are a reporting worker.
Given validation findings, write a 2-3 sentence health summary for an
on-call data engineer. Lead with the most important issue. Be calm and clear."""

TABLE_STATS = {
    "orders": {"row_count": 8000, "hours_since_update": 2},
    "customers": {"row_count": 50000, "hours_since_update": 1},
    "payments": {"row_count": 0, "hours_since_update": 26},
}

RULES = """Rules:
- row_count must be greater than 0
- hours_since_update must be less than 24"""


def run_subagent(role_prompt: str, task: str, model: str = MODEL) -> str:
    """Run one focused sub-agent: a Claude call with its own system prompt."""
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=role_prompt,  # this is what makes it "focused"
        messages=[{"role": "user", "content": task}],
    )
    return response.content[0].text


def check_table(table_name: str, stats: dict) -> str:
    raw = f"Table: {table_name}\nStats: {stats}"

    # Worker 1: extract metrics
    metrics = run_subagent(METRICS_ROLE, raw)

    # Worker 2: validate against rules
    validation = run_subagent(VALIDATION_ROLE, f"{metrics}\n\n{RULES}")

    # Worker 3: summarise findings
    summary = run_subagent(SUMMARY_ROLE, f"Findings for {table_name}:\n{validation}")
    return summary


def run_health_check(table_stats: dict) -> dict:
    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(check_table, name, stats): name
            for name, stats in table_stats.items()
        }
        for future in futures:
            name = futures[future]
            results[name] = future.result()
    return results


if __name__ == "__main__":
    report = run_health_check(TABLE_STATS)
    for table, summary in report.items():
        print(f"\n=== {table} ===\n{summary}")
