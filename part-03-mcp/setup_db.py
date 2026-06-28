import sqlite3

DB_PATH = "warehouse.db"


def setup():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id          INTEGER PRIMARY KEY,
            region      TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            order_date  DATE    NOT NULL
        )
    """)
    rows = [
        (1,  "EMEA",  12400.00, "2024-01-15"),
        (2,  "APAC",   8750.50, "2024-01-18"),
        (3,  "AMER",  21300.75, "2024-01-20"),
        (4,  "EMEA",   9800.00, "2024-02-03"),
        (5,  "APAC",  14200.25, "2024-02-10"),
        (6,  "AMER",  18600.00, "2024-02-14"),
        (7,  "EMEA",  11050.50, "2024-03-01"),
        (8,  "APAC",   7320.00, "2024-03-08"),
        (9,  "AMER",  25100.00, "2024-03-22"),
        (10, "EMEA",  16400.75, "2024-04-05"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO sales (id, region, amount, order_date) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()
    print(f"warehouse.db ready — {len(rows)} sales rows loaded.")


if __name__ == "__main__":
    setup()
