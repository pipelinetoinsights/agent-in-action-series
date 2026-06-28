import sqlite3
from fastmcp import FastMCP

mcp = FastMCP("Warehouse")

DB_PATH = "warehouse.db"


@mcp.tool
def query_sales(region: str) -> str:
    """Return total sales for a given region. Read-only.

    Args:
        region: Region name, e.g. 'EMEA', 'APAC', 'AMER'.
    """
    if not region or not region.strip():
        return "Error: region cannot be empty. Provide a name like 'EMEA' or 'APAC'."
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT SUM(amount) FROM sales WHERE region = ?",
            (region,),
        )
        total = cur.fetchone()[0]
        conn.close()
        if total is None:
            return f"No records found for region '{region}'. Check the spelling."
        return f"Total sales for {region}: {total:,.2f}"
    except sqlite3.Error as e:
        return f"Database error: {e}"


@mcp.resource("schema://sales")
def sales_schema() -> str:
    """The schema of the sales table."""
    return (
        "Table: sales\n"
        "Columns:\n"
        "  id          (INTEGER) primary key\n"
        "  region      (TEXT)    e.g. EMEA, APAC, AMER\n"
        "  amount      (REAL)    sale amount in USD\n"
        "  order_date  (DATE)    format YYYY-MM-DD"
    )


if __name__ == "__main__":
    # Default: stdio transport (for Claude Code and Claude Desktop).
    # For a shared/remote server, switch to:
    #   mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
    mcp.run()
