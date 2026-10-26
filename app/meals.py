"""Small built-in meal-use templates. No external recipe API."""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load_meals(path=None):
    if path is None:
        path = os.path.join(DATA_DIR, "meals.json")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def suggestions_for(name, category_key, meals=None):
    """Match by keyword in the item name first, then category, then fallback.

    The point is to use the urgent item, not to suggest gourmet recipes.
    """
    if meals is None:
        meals = load_meals()
    lowered = (name or "").lower()
    for keyword, ideas in meals.get("by_keyword", {}).items():
        if keyword in lowered:
            return list(ideas)
    by_category = meals.get("by_category", {})
    if category_key in by_category:
        return list(by_category[category_key])
    return list(meals.get("fallback", []))
