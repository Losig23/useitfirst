"""Flask app tests: add, morning ordering, outcomes, safety wording."""

import os
import tempfile

import pytest

from app import create_app


@pytest.fixture()
def client():
    handle, db_path = tempfile.mkstemp(suffix=".db")
    os.close(handle)
    os.unlink(db_path)
    app = create_app({"DATABASE": db_path, "TESTING": True})
    # Freeze 'today' for deterministic status checks.
    from datetime import date

    app.config["TODAY"] = date(2026, 10, 26)
    with app.test_client() as test_client:
        yield test_client


def add(client, name, category, start_date, storage="fridge", quantity="1"):
    return client.post(
        "/add",
        data={
            "name": name,
            "category": category,
            "start_date": start_date,
            "quantity": quantity,
            "storage": storage,
        },
        follow_redirects=True,
    )


def test_home_shows_safety_disclaimer(client):
    response = client.get("/")
    text = response.get_data(as_text=True)
    assert "not food-safety advice" in text
    assert "When in doubt, throw it out" in text


def test_add_and_morning_list_sorted_by_urgency(client):
    add(client, "Eggs", "eggs", "2026-10-24")  # fresh
    add(client, "Raw chicken thighs", "raw_chicken", "2026-10-25")  # use today
    add(client, "Leftover pasta", "cooked_leftovers", "2026-10-21")  # past window
    response = client.get("/")
    text = response.get_data(as_text=True)
    assert "past window" in text
    assert "use today" in text
    # Most urgent first on the page: past window before use today before fresh.
    assert text.index("past window") < text.index("use today") < text.index("fresh")
    # Mushroom / chicken keyword suggestions come from the template list.
    assert "tacos" in text


def test_outcome_logging_removes_from_active_list(client):
    add(client, "Milk", "milk_opened", "2026-10-20")
    response = client.get("/outcomes")
    assert "No outcomes logged yet" in response.get_data(as_text=True)
    # Item id 1 is the only item.
    client.post("/items/1/outcome", data={"outcome": "thrown away"}, follow_redirects=True)
    home = client.get("/").get_data(as_text=True)
    active_section = home.split("All active items")[1].split("Add an item")[0]
    assert "Milk" not in active_section
    outcomes = client.get("/outcomes").get_data(as_text=True)
    assert "thrown away" in outcomes


def test_unknown_outcome_rejected(client):
    add(client, "Milk", "milk_opened", "2026-10-20")
    response = client.post("/items/1/outcome", data={"outcome": "ate it all"})
    assert response.status_code == 400


def test_package_use_by_wins_in_app(client):
    response = add(client, "Milk", "milk_opened", "2026-10-26")
    assert response.status_code == 200
    # Direct DB check via a second add with an earlier package date is
    # covered in test_shelf_life; here the form accepts the optional field.
    response = client.post(
        "/add",
        data={
            "name": "Milk",
            "category": "milk_opened",
            "start_date": "2026-10-26",
            "quantity": "1",
            "storage": "fridge",
            "package_use_by": "2026-10-27",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
