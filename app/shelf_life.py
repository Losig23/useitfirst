"""Shelf-life math for UseItFirst.

The table lives in data/shelf_life.json, not in if-statements here.
This module only reads that data and does date arithmetic.

Rules, in plain terms:
- deadline = start date + shelf days for the item's storage location.
- If a package 'use by' date is present and earlier, it wins.
  Nothing here ever extends a package date.
- Status is purely a countdown from the deadline:
    past window : deadline already passed
    use today   : deadline is today
    freeze today: deadline is tomorrow and the item is in the fridge
                  (freezing today is still an option before it expires)
    use soon    : deadline in 2-3 days
    fresh       : deadline 4 or more days away
  A freezer or pantry item with 1 day left is 'use soon', not
  'freeze today' -- it is already frozen / shelf-stable, so freezing
  is not the action.
- This is a reminder and planning tool, not food-safety advice.
  'past window' never means 'probably fine'.
"""

import json
import os
from datetime import date, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load_table(path=None):
    if path is None:
        path = os.path.join(DATA_DIR, "shelf_life.json")
    with open(path, encoding="utf-8") as handle:
        raw = json.load(handle)
    table = {}
    for entry in raw["categories"]:
        table[entry["key"]] = entry
    return table, raw.get("source", "")


def shelf_days_for(category_key, storage, table):
    """Days for this category in this storage location, or None."""
    entry = table.get(category_key)
    if entry is None:
        entry = table.get("other")
    if entry is None:
        return None
    column = storage + "_days"
    return entry.get(column)


def deadline_for(start, category_key, storage, table, package_use_by=None):
    """Return the deadline date, or None if no shelf life is known."""
    days = shelf_days_for(category_key, storage, table)
    if days is None:
        # No table value: only a package date can set a deadline.
        return package_use_by
    deadline = start + timedelta(days=days)
    if package_use_by is not None and package_use_by < deadline:
        return package_use_by
    return deadline


def days_left(deadline, today):
    if deadline is None:
        return None
    return (deadline - today).days


def status_for(days_remaining, storage):
    if days_remaining is None:
        return "use soon"
    if days_remaining < 0:
        return "past window"
    if days_remaining == 0:
        return "use today"
    if days_remaining == 1 and storage == "fridge":
        return "freeze today"
    if days_remaining <= 3:
        return "use soon"
    return "fresh"


def evaluate(start, category_key, storage, today, package_use_by=None, table=None):
    """Full countdown for one item. Returns a dict, no side effects."""
    if table is None:
        table, _source = load_table()
    deadline = deadline_for(start, category_key, storage, table, package_use_by)
    remaining = days_left(deadline, today)
    return {
        "deadline": deadline,
        "days_left": remaining,
        "status": status_for(remaining, storage),
    }


def parse_date(text):
    if text is None or text == "":
        return None
    year, month, day = text.split("-")
    return date(int(year), int(month), int(day))


STATUS_ORDER = {
    "past window": 0,
    "use today": 1,
    "freeze today": 2,
    "use soon": 3,
    "fresh": 4,
}
