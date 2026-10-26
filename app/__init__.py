"""UseItFirst v0.1: a use-it-first fridge planner.

Reminder and planning tool only -- NOT food-safety advice.
When in doubt, throw it out. Smell and appearance do not prove safety.
"""

import os
import sqlite3
from datetime import date

from flask import Flask, current_app, g, redirect, render_template, request, url_for

from .meals import load_meals, suggestions_for
from .shelf_life import STATUS_ORDER, evaluate, load_table, parse_date

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    start_date TEXT NOT NULL,
    quantity TEXT NOT NULL DEFAULT '1',
    storage TEXT NOT NULL DEFAULT 'fridge',
    package_use_by TEXT,
    outcome TEXT,
    outcome_at TEXT,
    created_at TEXT NOT NULL
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def today_for(app):
    forced = app.config.get("TODAY")
    if forced is not None:
        return forced
    return date.today()


def create_app(config=None):
    app = Flask(__name__, template_folder="../templates")
    app.config["DATABASE"] = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "useitfirst.db"
    )
    if config:
        app.config.update(config)
    app.teardown_appcontext(close_db)

    table, source = load_table()
    meals = load_meals()
    app.config["SHELF_TABLE"] = table
    app.config["SHELF_SOURCE"] = source

    with app.app_context():
        init_db(app.config["DATABASE"])

    def enrich(row):
        today = today_for(app)
        start = parse_date(row["start_date"])
        package = parse_date(row["package_use_by"]) if row["package_use_by"] else None
        result = evaluate(start, row["category"], row["storage"], today, package, table)
        item = dict(row)
        item["deadline"] = result["deadline"].isoformat() if result["deadline"] else None
        item["days_left"] = result["days_left"]
        item["status"] = result["status"]
        item["suggestions"] = suggestions_for(row["name"], row["category"], meals)
        item["category_label"] = table.get(row["category"], {}).get("label", row["category"])
        return item

    @app.route("/")
    def index():
        db = get_db()
        rows = db.execute(
            "SELECT * FROM items WHERE outcome IS NULL ORDER BY start_date"
        ).fetchall()
        items = [enrich(row) for row in rows]
        items.sort(key=lambda it: (STATUS_ORDER[it["status"]], it["deadline"] or "9999"))
        morning = [it for it in items if it["status"] in ("past window", "use today", "freeze today")]
        return render_template(
            "index.html",
            items=items,
            morning=morning,
            categories=table,
            today=today_for(app).isoformat(),
        )

    @app.route("/add", methods=["POST"])
    def add():
        db = get_db()
        db.execute(
            "INSERT INTO items (name, category, start_date, quantity, storage,"
            " package_use_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                request.form["name"].strip(),
                request.form["category"],
                request.form["start_date"],
                request.form.get("quantity", "1").strip() or "1",
                request.form["storage"],
                request.form.get("package_use_by") or None,
                date.today().isoformat(),
            ),
        )
        db.commit()
        return redirect(url_for("index"))

    @app.route("/items/<int:item_id>/outcome", methods=["POST"])
    def outcome(item_id):
        value = request.form["outcome"]
        if value not in ("used", "frozen", "thrown away"):
            return "Unknown outcome", 400
        db = get_db()
        db.execute(
            "UPDATE items SET outcome = ?, outcome_at = ? WHERE id = ?",
            (value, date.today().isoformat(), item_id),
        )
        db.commit()
        return redirect(url_for("index"))

    @app.route("/outcomes")
    def outcomes():
        db = get_db()
        rows = db.execute(
            "SELECT * FROM items WHERE outcome IS NOT NULL ORDER BY outcome_at DESC, id DESC"
        ).fetchall()
        return render_template("outcomes.html", items=[dict(row) for row in rows])

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
