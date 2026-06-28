# Agents in Action

Code for the **Agents in Action** series on [Pipeline to Insights](https://pipeline2insights.substack.com) — an 8-part guide for data engineers going from "I use Claude in the browser" to "I can build this in my pipeline."

Each folder maps to one post. Start from Part 2 (Part 1 is concepts only, no code).

## Series

| Part | Topic | Post | Code |
|------|-------|------|------|
| 1 | What Is an AI Agent? | [Read](https://pipeline2insights.substack.com/p/agents-in-action-1-what-is-an-ai-for-data-engineers) | — no code — |
| 2 | Your First Tool — Function Calling | [Read](https://pipeline2insights.substack.com/p/agents-in-action-2-building-your-first-tool) | [part-02-function-calling](./part-02-function-calling/) |
| 3 | MCP — Model Context Protocol | [Read](https://pipeline2insights.substack.com) | [part-03-mcp](./part-03-mcp/) |
| 4 | Skills | coming soon | — |
| 5 | Sub-Agents | coming soon | — |
| 6 | Memory | coming soon | — |
| 7 | Putting It All Together | coming soon | — |
| 8 | Production-Ready Agents | coming soon | — |

## Requirements

```bash
pip install anthropic   # Parts 1–2
pip install fastmcp     # Part 3+
export ANTHROPIC_API_KEY="sk-ant-..."
```

Each part folder has its own `README.md` with setup instructions and a link to the post.
