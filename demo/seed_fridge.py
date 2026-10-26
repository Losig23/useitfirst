"""Seed a demo fridge with 12 items across all statuses, relative to today.

Run from the project root:  python demo/seed_fridge.py
Then run the app and open the morning list, or run with --print to see
the morning list here in the terminal.
"""

import os
import sqlite3
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import init_db  # noqa: E402
from app.meals import suggestions_for  # noqa: E402
from app.shelf_life import STATUS_ORDER, evaluate, load_table, parse_date  # noqa: E402

# (name, category, days_ago_started, quantity, storage, package_use_by_offset)
# package_use_by_offset is days from today, or None.
SEED = [
    ("Leftover roast chicken", "cooked_leftovers", 5, "1 box", "fridge", None),
    ("Ground beef", "ground_meat", 3, "1 lb", "fridge", None),
    ("Raw chicken thighs", "raw_chicken", 1, "2 lb", "fridge", None),
    ("Cut melon", "cut_fruit", 3, "1 box", "fridge", None),
    ("Leftover pasta", "cooked_leftovers", 2, "1 box", "fridge", None),
    ("Milk", "milk_opened", 5, "1 carton", "fridge", None),
    ("Beef steak", "raw_beef", 1, "2 steaks", "fridge", None),
    ("Mushrooms", "mushrooms", 1, "1 pack", "fridge", None),
    ("Eggs", "eggs", 2, "12", "fridge", None),
    ("Milk (new carton)", "milk_opened", 1, "1 carton", "fridge", None),
    ("Frozen chicken breasts", "raw_chicken", 30, "4 lb", "freezer", None),
    ("Canned beans", "other", 10, "3 cans", "pantry", None),
]


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(root, "demo.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db(db_path)
    table, _source = load_table()
    today = date.today()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    for name, category, ago, quantity, storage, pkg_offset in SEED:
        start = today - timedelta(days=ago)
        package = None
        if pkg_offset is not None:
            package = (today + timedelta(days=pkg_offset)).isoformat()
        conn.execute(
            "INSERT INTO items (name, category, start_date, quantity, storage,"
            " package_use_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, category, start.isoformat(), quantity, storage, package, today.isoformat()),
        )
    conn.commit()
    rows = conn.execute("SELECT * FROM items").fetchall()
    items = []
    for row in rows:
        result = evaluate(
            parse_date(row["start_date"]), row["category"], row["storage"], today, None, table
        )
        item = dict(row)
        item.update(result)
        item["suggestions"] = suggestions_for(row["name"], row["category"])
        items.append(item)
    items.sort(key=lambda it: (STATUS_ORDER[it["status"]], it["deadline"].isoformat()))
    print("Seeded demo fridge: %d items (demo.db)" % len(items))
    print("Morning list (past window / use today / freeze today), most urgent first:")
    for item in items:
        if item["status"] in ("past window", "use today", "freeze today"):
            print(
                "- %s: %s, deadline %s (%s day(s) left) -- %s"
                % (
                    item["status"],
                    item["name"],
                    item["deadline"],
                    item["days_left"],
                    ", ".join(item["suggestions"]),
                )
            )
    print("All statuses present: %s" % sorted(set(it["status"] for it in items)))
    conn.close()


if __name__ == "__main__":
    main()
