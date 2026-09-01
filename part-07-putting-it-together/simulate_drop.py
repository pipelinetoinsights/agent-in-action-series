# Simulates a real incident: deletes 3,000 rows from payments in warehouse.db.
# Run this between two pipeline_monitor.py runs to see the agent catch a real drop.

import sqlite3

DB_PATH = "warehouse.db"
ROWS_TO_DELETE = 3000


def simulate_drop() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"DELETE FROM payments WHERE id > (SELECT MAX(id) - {ROWS_TO_DELETE} FROM payments)")
    conn.commit()
    remaining = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
    conn.close()
    print(f"Deleted {ROWS_TO_DELETE} rows from payments. {remaining} rows remain.")


if __name__ == "__main__":
    simulate_drop()
