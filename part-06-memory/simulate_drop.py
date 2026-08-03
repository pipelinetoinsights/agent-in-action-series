# Simulates a real incident: deletes 2,000 rows from orders in warehouse.db.
# Run this between two memory_agent.py runs to see the agent catch a real drop.

import sqlite3

DB_PATH = "warehouse.db"
ROWS_TO_DELETE = 2000


def simulate_drop() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"DELETE FROM orders WHERE id > (SELECT MAX(id) - {ROWS_TO_DELETE} FROM orders)")
    conn.commit()
    remaining = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()
    print(f"Deleted {ROWS_TO_DELETE} rows from orders. {remaining} rows remain.")


if __name__ == "__main__":
    simulate_drop()
