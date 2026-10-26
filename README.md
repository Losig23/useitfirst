# UseItFirst v0.1

A use-it-first fridge planner. Meal planners tell you what to cook;
UseItFirst tracks what is already in your fridge over time and tells you
what to use first: "those mushrooms die Thursday -- cook them before the
chicken you just bought."

## Safety, plainly

**This is a reminder and planning tool, not food-safety advice.**
The main screen says so, and so does this README.

- **When in doubt, throw it out.** Smell and appearance do not prove safety.
- An item past its window is labelled **"past window"** -- never "probably fine."
- Never override an earlier package "use by" date with the table below.

## What it does

- Add fridge / freezer / pantry items: name, category, date bought / cooked /
  opened, quantity, storage location, optional package date.
- Each item gets a countdown from a shelf-life table stored as data
  (`data/shelf_life.json`), not hardcoded if-statements.
- Statuses, purely by countdown from the deadline:
  - `fresh` -- deadline 4+ days away
  - `use soon` -- deadline in 2-3 days (or 1 day away in freezer/pantry)
  - `freeze today` -- deadline tomorrow, item in the fridge
  - `use today` -- deadline is today
  - `past window` -- deadline has passed
- A morning list: "past window" + "use today" + "freeze today", most urgent first.
- Simple meal-use suggestions from a small built-in template list
  (`data/meals.json`), e.g. mushrooms -> pasta, stir-fry, omelet.
  The point is to use the urgent item, not gourmet recipes.
- Log each item's outcome: `used` / `frozen` / `thrown away`.
  That log is the data for v0.2's personal waste model.

## What it does NOT do

- No OCR, no receipt scanning, no barcode lookup. Manual entry is a feature
  here: it is fast, private, and it works.
- No external recipe API.
- No food-safety verdicts. It counts days; it does not inspect your food.
- No personal waste model yet -- that is v0.2, once outcome logs exist.

## Shelf-life source

Starting values are from USDA FoodKeeper / USDA Food Safety and Inspection
Service (FSIS) storage guidance, fridge at or below 40°F, using the
**conservative (short) end** of each published range for safety-critical foods:

- Cooked leftovers / cooked meat, poultry, fish: 3-4 days -> **3 used**
- Raw chicken / ground meat: 1-2 days -> **1 used**
- Milk (opened): within **7 days**
- Leafy greens: 3-5 days -> **3 used**
- Cut fruit: 3-4 days -> **3 used**

The full table, including freezer and pantry columns, lives in
`data/shelf_life.json` with its source note. A package "use by" date, when
earlier, always wins; a later package date never extends the table deadline.

## Stack, and why

Python, Flask + SQLite -- the same conventions as the author's other
portfolio projects (Flask + SQLite, REST-style forms, pytest). A CLI + JSON
store would also have worked, but Flask gives a phone-friendly morning list
with no extra tooling, and SQLite keeps the outcome log queryable for v0.2.
Code is kept Python 3.9-compatible (no 3.10+ only syntax).

## Run it

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python demo/seed_fridge.py   # optional: 12-item demo fridge
.venv/bin/python run.py                # http://127.0.0.1:5000
```

## Tests

```bash
.venv/bin/python -m pytest -q
```

Tests cover every shelf-life calculation in the table's conservative ends,
the package-date override rule, and every status transition
(past window / use today / freeze today / use soon / fresh), plus the Flask
routes for adding items, morning-list ordering, and outcome logging.

## Demo

`demo/seed_fridge.py` seeds a fridge with 12 items across all five statuses
and prints the morning list. The seeded database is `demo.db` (gitignored;
re-run the script to regenerate it relative to today).

## Limitations

- Shelf lives are starting-point averages, not guarantees for a specific
  item, brand, or fridge temperature. Your fridge thermometer and the package
  date matter more than this table.
- Categories are coarse: "cooked leftovers" covers many foods with different
  real storage behaviour. When the table and the package disagree, the package
  wins; when in doubt, throw it out.
- The v0.1 status is a countdown only. It does not know how the item was
  stored, whether it was left out, or whether it was reheated.
- Meal suggestions are templates, not recipes and not nutrition advice.
- v0.2 plan (not built yet): a personal waste model from the user's own
  outcome logs -- logistic regression first, so the user can see why a
  warning moved earlier -- evaluated on a time-based split.

## Layout

```
app/                 Flask app, shelf-life math, meal templates
data/shelf_life.json shelf-life table (data, not code)
data/meals.json      meal-use templates
demo/seed_fridge.py  12-item seeded demo fridge
templates/           HTML pages
tests/               pytest suite
```
