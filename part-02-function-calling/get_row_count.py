import sqlite3
import json
from anthropic import Anthropic

client = Anthropic()


def setup_demo_db():
    conn = sqlite3.connect("warehouse.db")
    conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, amount REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT)")
    conn.executemany("INSERT OR IGNORE INTO orders VALUES (?, ?)", [(i, i * 9.99) for i in range(1, 51)])
    conn.executemany("INSERT OR IGNORE INTO customers VALUES (?, ?)", [(i, f"Customer {i}") for i in range(1, 21)])
    conn.commit()
    conn.close()


def get_row_count(table_name: str) -> int:
    allowed_tables = {"orders", "customers"}
    if table_name not in allowed_tables:
        raise ValueError(f"Unknown table: {table_name}")
    conn = sqlite3.connect("warehouse.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    conn.close()
    return count


tools = [
    {
        "name": "get_row_count",
        "description": (
            "Returns the number of rows in a database table. "
            "Use this whenever the user asks how many records exist, "
            "how large a table is, or whether a table has any data. "
            "Requires the exact table name as a string."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "The exact name of the table to count rows in.",
                }
            },
            "required": ["table_name"],
        },
    }
]


def run(question: str):
    messages = [{"role": "user", "content": question}]

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )

    while response.stop_reason == "tool_use":
        tool_use = next(b for b in response.content if b.type == "tool_use")
        print(f"  [tool call] {tool_use.name}({tool_use.input})")
        result = get_row_count(**tool_use.input)

        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": str(result),
            }],
        })

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

    print(response.content[0].text)


if __name__ == "__main__":
    setup_demo_db()

    questions = [
        "How many rows are in the orders table?",
        "How many customers do we have?",
        "What's a good name for a data pipeline project?",  # should NOT call the tool
    ]

    for q in questions:
        print(f"\nQ: {q}")
        run(q)
