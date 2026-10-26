"""Tests for every shelf-life calculation and status transition."""

from datetime import date

from app.shelf_life import deadline_for, evaluate, load_table, status_for

TABLE, _SOURCE = load_table()
TODAY = date(2026, 10, 26)


def test_cooked_leftovers_conservative_end():
    # USDA range 3-4 days; v0.1 uses 3.
    assert deadline_for(date(2026, 10, 24), "cooked_leftovers", "fridge", TABLE) == date(2026, 10, 27)


def test_raw_chicken_conservative_end():
    # USDA range 1-2 days; v0.1 uses 1.
    assert deadline_for(date(2026, 10, 25), "raw_chicken", "fridge", TABLE) == date(2026, 10, 26)


def test_ground_meat_conservative_end():
    assert deadline_for(date(2026, 10, 25), "ground_meat", "fridge", TABLE) == date(2026, 10, 26)


def test_milk_opened_seven_days():
    assert deadline_for(date(2026, 10, 20), "milk_opened", "fridge", TABLE) == date(2026, 10, 27)


def test_leafy_greens_conservative_end():
    assert deadline_for(date(2026, 10, 24), "leafy_greens", "fridge", TABLE) == date(2026, 10, 27)


def test_package_date_never_overridden_when_earlier():
    # Table would give 2026-10-29; package says 2026-10-27, so 27 wins.
    assert deadline_for(
        date(2026, 10, 26), "milk_opened", "fridge", TABLE, date(2026, 10, 27)
    ) == date(2026, 10, 27)


def test_package_date_later_than_table_does_not_extend():
    # Table gives 2026-10-27; a later package date must not extend it.
    assert deadline_for(
        date(2026, 10, 24), "cooked_leftovers", "fridge", TABLE, date(2026, 11, 15)
    ) == date(2026, 10, 27)


def test_freezer_uses_freezer_column():
    assert deadline_for(date(2026, 9, 26), "raw_chicken", "freezer", TABLE) == date(2027, 6, 23)


def test_status_transitions():
    assert status_for(-1, "fridge") == "past window"
    assert status_for(-5, "fridge") == "past window"
    assert status_for(0, "fridge") == "use today"
    assert status_for(1, "fridge") == "freeze today"
    assert status_for(1, "freezer") == "use soon"
    assert status_for(1, "pantry") == "use soon"
    assert status_for(2, "fridge") == "use soon"
    assert status_for(3, "fridge") == "use soon"
    assert status_for(4, "fridge") == "fresh"
    assert status_for(30, "fridge") == "fresh"


def test_evaluate_end_to_end():
    result = evaluate(date(2026, 10, 25), "raw_chicken", "fridge", TODAY, table=TABLE)
    assert result["deadline"] == date(2026, 10, 26)
    assert result["days_left"] == 0
    assert result["status"] == "use today"


def test_evaluate_past_window_is_never_probably_fine():
    result = evaluate(date(2026, 10, 20), "cooked_leftovers", "fridge", TODAY, table=TABLE)
    assert result["status"] == "past window"
    assert result["days_left"] < 0


def test_table_is_data_not_scattered_ifs():
    # Every category used in tests must come from the JSON table.
    assert "cooked_leftovers" in TABLE
    assert "raw_chicken" in TABLE
    assert "milk_opened" in TABLE
    assert "leafy_greens" in TABLE
    assert TABLE["cooked_leftovers"]["fridge_days"] == 3
    assert TABLE["raw_chicken"]["fridge_days"] == 1
