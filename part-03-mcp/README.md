# Part 3 — MCP: Model Context Protocol for Data Engineers

Code for [Agents in Action #3](https://pipeline2insights.substack.com) on [Pipeline to Insights](https://pipeline2insights.substack.com).

In Part 2 we built `get_row_count` as a function-calling tool inside a single agent. Here we take the same pattern and expose it as an MCP server — reusable by Claude Code, Claude Desktop, Cursor, or any MCP-compatible client without changing a line of server code.

## Files

| File | What it does |
|------|-------------|
| `setup_db.py` | Creates `warehouse.db` with a `sales` table |
| `server.py` | FastMCP server — exposes `query_sales` tool and `schema://sales` resource |

## Setup

```bash
pip install fastmcp
python setup_db.py
```

## Connect to a Client

### Claude Code (fastest)

```bash
claude mcp add warehouse -- python /full/path/to/server.py
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "warehouse": {
      "command": "python",
      "args": ["/full/path/to/server.py"]
    }
  }
}
```

Same format works for **Cursor** (`.cursor/mcp.json`) and **VS Code**.

### Remote HTTP (shared / cloud deployment)

Change the last line of `server.py`:

```python
mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

Then connect clients by URL:

```bash
# Claude Code
claude mcp add warehouse --transport http http://your-server:8000/mcp
```

```json
// Claude Desktop
{ "mcpServers": { "warehouse": { "url": "http://your-server:8000/mcp" } } }
```

## Test Before Connecting

```bash
npx @modelcontextprotocol/inspector python server.py
```

Opens a browser UI to list and call tools manually — like Postman for MCP.

## Try It

Once connected, ask your client:

- *"What were total sales in EMEA?"*
- *"Compare APAC vs AMER total sales."*
- *"What columns does the sales table have?"*

The agent reads `schema://sales` first, then calls `query_sales` with the right region.
