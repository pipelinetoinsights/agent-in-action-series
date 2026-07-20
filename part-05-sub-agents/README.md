# Part 5 — Sub-agents: Delegating Work to Focused Workers

Code for [Agents in Action #5](https://pipeline2insights.substack.com/p/ai-agents-in-action-part-5-sub-agents-for-data-engineers) on [Pipeline to Insights](https://pipeline2insights.substack.com).

A pipeline health monitor that fans out to three focused sub-agents — **metrics**, **validation**, **summary** — one per table, run in parallel by an orchestrator. Each worker is just a Claude call with its own narrow system prompt; none of them shares context with the others.

## Run it

```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
python pipeline_health.py
```

The demo data deliberately makes `payments` empty and stale so you can see the anomaly path end to end — swap `TABLE_STATS` for a real warehouse query where noted.

## Files

| File | What it does |
|------|-------------|
| `pipeline_health.py` | The full orchestrator + three worker roles + parallel fan-out |

## Why Haiku

Each worker's job is narrow and single-purpose (extract, validate, summarize) — exactly the case for a smaller, cheaper model. Fanning out sub-agents multiplies your call count, so this is also the post's own "watch your token spend" lesson applied to the example itself.
