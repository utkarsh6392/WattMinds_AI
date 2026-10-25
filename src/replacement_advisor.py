"""
WattMinds - Replacement Advisor

Recommends which appliances are worth replacing, with what type of
appliance, and how much money and energy that saves.

IMPORTANT: every wattage and price in CATALOG is an INDICATIVE estimate
for the Indian market. They exist so the tool works out of the box.
Users should enter real quotes (replacement_watts / replacement_cost_rs)
for an accurate payback.

To add or change an appliance type, edit CATALOG below - nothing else in
this file needs to change.

Formulas (per appliance, using the USER'S entered watts as the old wattage):
    kwh_saved_per_day     = (old_w - new_w) * hours_per_day * quantity / 1000
    monthly_saving_rs     = kwh_saved_per_day * 30  * tariff
    yearly_saving_rs      = kwh_saved_per_day * 365 * tariff
    total_replacement_cost = replacement cost * quantity
    payback_months        = total_replacement_cost / monthly_saving_rs
    priority              = High (< 12 months), Medium (12-36), Low (> 36)
"""

from __future__ import annotations

import math
import re
from typing import Any


# =========================================================
# 1. REPLACEMENT CATALOG  (indicative estimates - edit freely)
# =========================================================
#
# type_key            unique id used by the API and the dropdown
# label               OLD appliance type shown to the user
# min_w / max_w       typical wattage range of the OLD appliance
# replacement         recommended replacement (lower-case, used mid-sentence)
# replacement_w       typical replacement wattage (average running power)
# replacement_cost_rs typical price of ONE replacement unit, in Rs
# lifespan_years      typical lifespan of the old type (used for age notes)
# notes               shown on the recommendation card
# keywords            words in the appliance NAME used when no type is chosen
# exclude_keywords    (optional) name words that rule this type out, e.g. an
#                     "exhaust fan" is not a ceiling fan

CATALOG: list[dict[str, Any]] = [
    {
        "type_key": "incandescent_bulb",
        "label": "Incandescent bulb",
        "min_w": 25, "max_w": 200,
        "replacement": "LED bulb",
        "replacement_w": 9,
        "replacement_cost_rs": 100,
        "lifespan_years": 1,
        "notes": (
            "A 9 W LED gives about the light of a 60 W incandescent bulb. "
            "For a 100 W bulb pick a 14 W LED and enter its price under Advanced."
        ),
        "keywords": ["incandescent", "filament", "tungsten", "bulb", "lamp"],
    },
    {
        "type_key": "cfl",
        "label": "CFL",
        "min_w": 10, "max_w": 30,
        "replacement": "LED bulb",
        "replacement_w": 9,
        "replacement_cost_rs": 100,
        "lifespan_years": 3,
        "notes": "LEDs also switch on instantly and contain no mercury.",
        "keywords": ["cfl", "compact fluorescent", "bulb", "lamp"],
    },
    {
        "type_key": "tube_light",
        "label": "Tube light (T12 / T8)",
        "min_w": 36, "max_w": 60,
        "replacement": "LED batten",
        "replacement_w": 20,
        "replacement_cost_rs": 450,
        "lifespan_years": 5,
        "notes": (
            "Old tubes use 36-55 W including the choke. A 20 W LED tube or "
            "batten gives similar light and needs no choke."
        ),
        "keywords": ["tube", "tubelight", "t12", "t8", "fluorescent"],
    },
    {
        "type_key": "ceiling_fan",
        "label": "Old ceiling fan",
        "min_w": 55, "max_w": 100,
        "replacement": "BLDC ceiling fan",
        "replacement_w": 30,
        "replacement_cost_rs": 3200,
        "lifespan_years": 10,
        "notes": "BLDC fans run on about 28-35 W against 70-80 W for a regular fan.",
        "keywords": ["fan"],
        "exclude_keywords": ["exhaust", "table", "pedestal", "cooler", "laptop"],
    },
    {
        "type_key": "air_conditioner",
        "label": "Old (non-inverter) air conditioner",
        "min_w": 1200, "max_w": 2500,
        "replacement": "5-star inverter air conditioner",
        "replacement_w": 950,
        "replacement_cost_rs": 42000,
        "lifespan_years": 10,
        "notes": (
            "Replacement wattage is the average running power of a 1.5-ton "
            "5-star inverter AC. For other capacities, enter your quote's "
            "wattage and price under Advanced."
        ),
        "keywords": ["air conditioner", "air conditioning", "ac", "a/c", "split ac", "window ac"],
    },
    {
        "type_key": "refrigerator",
        "label": "Old refrigerator",
        "min_w": 130, "max_w": 400,
        "replacement": "5-star inverter refrigerator",
        "replacement_w": 100,
        "replacement_cost_rs": 28000,
        "lifespan_years": 12,
        "notes": (
            "Compares running power at the same hours per day. A refrigerator "
            "should keep running all day, so the saving comes from the new "
            "model, not from using it less."
        ),
        "keywords": ["refrigerator", "fridge", "freezer"],
    },
    {
        "type_key": "crt_tv",
        "label": "CRT TV",
        "min_w": 60, "max_w": 180,
        "replacement": "LED TV",
        "replacement_w": 40,
        "replacement_cost_rs": 14000,
        "lifespan_years": 10,
        "notes": "Based on a 32-inch LED TV. Larger screens use more power.",
        "keywords": ["crt", "tv", "television"],
    },
    {
        "type_key": "desktop_pc",
        "label": "Old desktop computer (CPU)",
        "min_w": 100, "max_w": 400,
        "replacement": "energy-efficient laptop",
        "replacement_w": 45,
        "replacement_cost_rs": 45000,
        "lifespan_years": 6,
        "notes": (
            "Energy savings alone rarely justify a new computer, so treat this "
            "as a bonus when you were going to upgrade anyway."
        ),
        "keywords": ["desktop", "cpu", "pc", "computer"],
    },
    {
        "type_key": "crt_monitor",
        "label": "Old (CRT) monitor",
        "min_w": 50, "max_w": 150,
        "replacement": "LED monitor",
        "replacement_w": 20,
        "replacement_cost_rs": 7000,
        "lifespan_years": 8,
        "notes": "A 22-inch LED monitor typically draws 15-25 W.",
        "keywords": ["monitor", "crt monitor"],
    },
    {
        "type_key": "geyser",
        "label": "Electric water heater (geyser)",
        "min_w": 1500, "max_w": 3000,
        "replacement": "5-star geyser",
        "replacement_w": 1700,
        "replacement_cost_rs": 9000,
        "lifespan_years": 8,
        "notes": (
            "A 5-star geyser mainly cuts standby heat loss, so the saving is "
            "modest. A solar water heater or heat-pump geyser can cut "
            "water-heating electricity by roughly 60-75% but costs much more "
            "upfront - get a quote and enter it under Advanced to compare."
        ),
        "keywords": ["geyser", "water heater", "heater"],
        "exclude_keywords": ["room", "blower", "convector", "oil", "gas"],
    },
    {
        "type_key": "water_pump",
        "label": "Old water pump / motor",
        "min_w": 370, "max_w": 1500,
        "replacement": "energy-efficient pump",
        "replacement_w": 600,
        "replacement_cost_rs": 12000,
        "lifespan_years": 10,
        "notes": "Based on a 1 HP pump with a high-efficiency (IE3) motor.",
        "keywords": ["pump", "motor"],
    },
]

# Replacement wattage within this fraction of the old wattage means
# "already efficient" (the user's own wattage is never overwritten).
EFFICIENT_TOLERANCE = 0.10

# Input limits.
MAX_APPLIANCES = 50
MAX_WATTS = 50_000
MAX_QUANTITY = 100
MAX_COST_RS = 10_000_000
MAX_TARIFF = 1_000

ASSUMPTIONS = [
    "Your entered wattage is used as the old appliance's power draw and is never overwritten by catalog values.",
    "Savings use rated power for the hours per day you entered, a 30-day month, a 365-day year and a flat tariff.",
    "Replacement wattages and prices in the catalog are indicative Indian-market estimates. Enter real quotes for an accurate payback.",
    "Payback = total replacement cost / monthly saving. It ignores installation charges, resale value, subsidies and price changes.",
    "Priority: High = pays back in under 12 months, Medium = 12 to 36 months, Low = more than 36 months.",
    "An appliance is treated as already efficient when it uses no more than 10% above the replacement's wattage.",
]

_BY_KEY = {entry["type_key"]: entry for entry in CATALOG}


# =========================================================
# 2. PUBLIC HELPERS
# =========================================================

def list_replacement_types() -> list[dict[str, Any]]:
    """Catalog entries for the frontend dropdown (no internal fields)."""

    return [
        {
            "type_key": entry["type_key"],
            "label": entry["label"],
            "replacement": entry["replacement"],
            "typical_old_watts": [entry["min_w"], entry["max_w"]],
            "replacement_watts": entry["replacement_w"],
            "replacement_cost_rs": entry["replacement_cost_rs"],
        }
        for entry in CATALOG
    ]


# =========================================================
# 3. INPUT VALIDATION
# =========================================================

def _number(value: Any, label: str, low: float, high: float) -> float:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{label} must be a number.")

    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number.") from None

    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number.")

    if number < low or number > high:
        raise ValueError(f"{label} must be between {low:g} and {high:g}.")

    return number


def _optional_number(item: dict, key: str, label: str, low: float, high: float):
    value = item.get(key)

    if value is None or value == "":
        return None

    return _number(value, label, low, high)


def _clean_item(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"Appliance {index + 1} must be an object.")

    name = str(raw.get("name") or "").strip()

    if not name:
        raise ValueError(f"Appliance {index + 1} needs a name.")

    if len(name) > 80:
        raise ValueError(f"Appliance {index + 1}: name is too long (max 80 characters).")

    who = f"'{name}'"

    type_key = raw.get("type_key", raw.get("type"))
    type_key = str(type_key).strip().lower() if type_key not in (None, "") else None

    if type_key == "auto":
        type_key = None

    if type_key is not None and type_key not in _BY_KEY:
        raise ValueError(f"{who}: unknown appliance type '{type_key}'.")

    quantity = _number(raw.get("quantity", 1), f"{who} quantity", 1, MAX_QUANTITY)

    if quantity != int(quantity):
        raise ValueError(f"{who} quantity must be a whole number.")

    return {
        "name": name,
        "type_key": type_key,
        "watts": _number(raw.get("watts"), f"{who} watts", 0, MAX_WATTS),
        "hours": _number(
            raw.get("hours_per_day", raw.get("hours")),
            f"{who} hours per day", 0, 24,
        ),
        "quantity": int(quantity),
        "age_years": _optional_number(raw, "age_years", f"{who} age", 0, 100),
        "replacement_watts": _optional_number(
            raw, "replacement_watts", f"{who} replacement watts", 0, MAX_WATTS
        ),
        "replacement_cost_rs": _optional_number(
            raw, "replacement_cost_rs", f"{who} replacement cost", 0, MAX_COST_RS
        ),
    }


# =========================================================
# 4. TYPE DETECTION FROM THE APPLIANCE NAME
# =========================================================

def _keyword_hit(keyword: str, name: str) -> bool:
    # Short keywords ("ac", "tv", "pc") must be whole words; longer ones
    # may match the start of a word so "bulbs" matches "bulb".
    if len(keyword) <= 3:
        return re.search(rf"\b{re.escape(keyword)}s?\b", name) is not None

    return re.search(rf"\b{re.escape(keyword)}", name) is not None


def _name_signals_efficient(name: str) -> str | None:
    """Return a reason if the name itself says the appliance is already efficient."""

    if re.search(r"\bled\b", name):
        return "its name says it is already LED"

    if re.search(r"\bbldc\b", name):
        return "its name says it is already a BLDC model"

    if re.search(r"\b5[\s-]?star\b", name):
        return "its name says it is already 5-star rated"

    if re.search(r"\binverter\b", name) and not re.search(r"\bnon[\s-]?inverter\b", name):
        return "its name says it is already an inverter model"

    return None


def _detect_type(name: str, watts: float) -> dict[str, Any] | None:
    lowered = name.lower()

    candidates = [
        entry for entry in CATALOG
        if any(_keyword_hit(word, lowered) for word in entry["keywords"])
        and not any(_keyword_hit(word, lowered) for word in entry.get("exclude_keywords", []))
    ]

    if not candidates:
        return None

    # Several types can share a word (a "bulb" may be incandescent or CFL):
    # prefer the one whose typical wattage range contains the entered watts.
    for entry in candidates:
        if entry["min_w"] <= watts <= entry["max_w"]:
            return entry

    return candidates[0]


# =========================================================
# 5. FORMATTING HELPERS
# =========================================================

def _article(phrase: str) -> str:
    first = phrase[:1].lower()

    if first in "aeiou" or phrase.upper().startswith(("LED", "LCD")):
        return "an"

    return "a"


def _rupees(value: float) -> str:
    return f"₹{value:,.0f}"


def _payback_text(months: float | None) -> str:
    if months is None:
        return "no payback at this tariff"

    if months < 24:
        return f"{months:.1f} months"

    return f"{months / 12:.1f} years"


def _priority(months: float | None) -> str:
    if months is None:
        return "Low"

    if months < 12:
        return "High"

    if months <= 36:
        return "Medium"

    return "Low"


# =========================================================
# 6. MAIN FUNCTION
# =========================================================

def recommend_replacements(appliances: list[dict], tariff_per_kwh: float = 8.0) -> dict[str, Any]:
    """
    Recommend replacements for a list of appliances.

    Each appliance is a dict with: name, type_key (optional - falls back to
    keyword matching on the name), watts, hours_per_day, quantity, and
    optionally age_years, replacement_watts, replacement_cost_rs.

    Returns {"recommendations", "already_efficient", "not_assessed",
    "summary", "assumptions"}. Recommendations are sorted by yearly saving,
    largest first. Raises ValueError with a clear message on bad input.
    """

    tariff = _number(tariff_per_kwh, "Tariff", 0, MAX_TARIFF)

    if not isinstance(appliances, (list, tuple)) or not appliances:
        raise ValueError("Add at least one appliance.")

    if len(appliances) > MAX_APPLIANCES:
        raise ValueError(f"Please enter at most {MAX_APPLIANCES} appliances.")

    items = [_clean_item(raw, i) for i, raw in enumerate(appliances)]

    recommendations: list[dict[str, Any]] = []
    already_efficient: list[dict[str, Any]] = []
    not_assessed: list[dict[str, Any]] = []

    for item in items:
        name = item["name"]
        old_w = item["watts"]
        hours = item["hours"]
        quantity = item["quantity"]

        # ---- 1. Which catalog entry applies? ------------------------
        auto_detected = item["type_key"] is None

        if auto_detected:
            reason = _name_signals_efficient(name.lower())

            if reason:
                already_efficient.append({
                    "name": name,
                    "type_label": None,
                    "old_watts": old_w,
                    "replacement_watts": None,
                    "reason": f"No change needed - {reason}.",
                })
                continue

            entry = _detect_type(name, old_w)
        else:
            entry = _BY_KEY[item["type_key"]]

        if entry is None:
            not_assessed.append({
                "name": name,
                "reason": (
                    "Could not tell what type of appliance this is. "
                    "Pick a type from the list to assess it."
                ),
            })
            continue

        # ---- 2. Replacement figures (catalog, or the user's quote) ---
        new_w = (
            item["replacement_watts"]
            if item["replacement_watts"] is not None
            else float(entry["replacement_w"])
        )
        cost_each = (
            item["replacement_cost_rs"]
            if item["replacement_cost_rs"] is not None
            else float(entry["replacement_cost_rs"])
        )

        if old_w <= 0:
            not_assessed.append({
                "name": name,
                "reason": "Watts is 0, so there is nothing to compare. Enter the appliance's rated power.",
            })
            continue

        # ---- 3. Already efficient? ----------------------------------
        if old_w <= new_w * (1 + EFFICIENT_TOLERANCE):
            already_efficient.append({
                "name": name,
                "type_label": entry["label"],
                "old_watts": old_w,
                "replacement_watts": new_w,
                "reason": (
                    f"At {old_w:g} W it already uses about as little as "
                    f"{_article(entry['replacement'])} {entry['replacement']} "
                    f"({new_w:g} W). Keep it."
                ),
            })
            continue

        if hours <= 0:
            not_assessed.append({
                "name": name,
                "reason": "Hours per day is 0, so replacing it would save nothing. Enter its daily use.",
            })
            continue

        # ---- 4. Savings, cost and payback ---------------------------
        kwh_per_day = (old_w - new_w) * hours * quantity / 1000
        monthly_saving = kwh_per_day * 30 * tariff
        yearly_saving = kwh_per_day * 365 * tariff
        total_cost = cost_each * quantity
        payback = total_cost / monthly_saving if monthly_saving > 0 else None
        priority = _priority(payback)

        # ---- 5. Text ------------------------------------------------
        headline = (
            f"Replace {name} ({old_w:g} W) with {entry['replacement']} ({new_w:g} W)"
        )

        cost_phrase = (
            _rupees(total_cost)
            if quantity == 1
            else f"{_rupees(total_cost)} ({quantity} × {_rupees(cost_each)})"
        )

        if payback is None:
            payback_sentence = "At a ₹0 tariff there is no money saving, so it never pays back."
        else:
            payback_sentence = f"so it pays for itself in roughly {_payback_text(payback)}."

        detail = (
            f"You save {kwh_per_day:.2f} kWh per day, about "
            f"{_rupees(yearly_saving)} per year. "
            f"The replacement costs about {cost_phrase}"
            f"{', ' if payback is not None else '. '}{payback_sentence}"
        )

        summary_text = (
            f"Replace your {name} ({old_w:g} W) with "
            f"{_article(entry['replacement'])} {entry['replacement']} ({new_w:g} W). "
            f"{detail}"
        )

        notes = [entry["notes"]] if entry.get("notes") else []
        warnings = []

        if auto_detected:
            warnings.append(f"Type auto-detected from the name as '{entry['label']}'. Pick a type if that is wrong.")

        if not entry["min_w"] <= old_w <= entry["max_w"]:
            warnings.append(
                f"{old_w:g} W is outside the typical {entry['min_w']}-{entry['max_w']} W "
                f"range for '{entry['label']}'. Check the type and watts."
            )

        age = item["age_years"]

        if age is not None and age >= entry["lifespan_years"]:
            notes.append(
                f"At {age:g} years old it is already past the typical "
                f"{entry['lifespan_years']}-year lifespan, so it may need replacing soon anyway."
            )

        recommendations.append({
            "name": name,
            "type_key": entry["type_key"],
            "type_label": entry["label"],
            "auto_detected": auto_detected,
            "quantity": quantity,
            "hours_per_day": hours,
            "old_watts": old_w,
            "age_years": age,
            "replacement": {
                "name": entry["replacement"],
                "watts": new_w,
                "cost_each_rs": round(cost_each, 2),
                "watts_source": "your quote" if item["replacement_watts"] is not None else "catalog estimate",
                "cost_source": "your quote" if item["replacement_cost_rs"] is not None else "catalog estimate",
            },
            "kwh_saved_per_day": round(kwh_per_day, 3),
            "kwh_saved_per_year": round(kwh_per_day * 365, 1),
            "monthly_saving_rs": round(monthly_saving, 2),
            "yearly_saving_rs": round(yearly_saving, 2),
            "total_replacement_cost_rs": round(total_cost, 2),
            "payback_months": None if payback is None else round(payback, 1),
            "payback_text": _payback_text(payback),
            "priority": priority,
            "headline": headline,
            "detail": detail,
            "summary_text": summary_text,
            "notes": notes,
            "warnings": warnings,
            "_yearly": yearly_saving,
            "_monthly": monthly_saving,
            "_cost": total_cost,
            "_kwh_year": kwh_per_day * 365,
        })

    # ---- 6. Sort, share of savings, summary --------------------------
    recommendations.sort(key=lambda rec: rec["_yearly"], reverse=True)

    total_yearly = sum(rec["_yearly"] for rec in recommendations)
    total_monthly = sum(rec["_monthly"] for rec in recommendations)
    total_cost = sum(rec["_cost"] for rec in recommendations)
    total_kwh_year = sum(rec["_kwh_year"] for rec in recommendations)

    for rec in recommendations:
        rec["share_of_savings_pct"] = (
            round(rec["_yearly"] / total_yearly * 100, 1) if total_yearly > 0 else 0.0
        )

        for private in ("_yearly", "_monthly", "_cost", "_kwh_year"):
            del rec[private]

    overall_payback = total_cost / total_monthly if total_monthly > 0 else None

    summary = {
        "total_yearly_saving_rs": round(total_yearly, 2),
        "total_monthly_saving_rs": round(total_monthly, 2),
        "total_investment_rs": round(total_cost, 2),
        "overall_payback_months": None if overall_payback is None else round(overall_payback, 1),
        "overall_payback_text": _payback_text(overall_payback) if recommendations else "-",
        "kwh_saved_per_year": round(total_kwh_year, 1),
        "kwh_saved_per_day": round(total_kwh_year / 365, 3),
        "tariff_rs_per_kwh": tariff,
        "recommended_count": len(recommendations),
        "already_efficient_count": len(already_efficient),
        "not_assessed_count": len(not_assessed),
    }

    return {
        "recommendations": recommendations,
        "already_efficient": already_efficient,
        "not_assessed": not_assessed,
        "summary": summary,
        "assumptions": list(ASSUMPTIONS),
    }


# =========================================================
# 7. ENERGY COPILOT HELPERS
# =========================================================
#
# The Energy Copilot calls these so a question such as "which appliance
# should I replace?" is answered by recommend_replacements() using the
# appliances the user has already entered.

_REPLACEMENT_QUESTION = re.compile(
    r"\b(replace|replaces|replacing|replacement|upgrade|upgrading|swap|swapping|"
    r"switch(?:ing)? to|buy|buying|led|bldc|inverter)\b|बदल"
)


def is_replacement_question(question: str) -> bool:
    """True for questions like 'which appliance should I replace?' or 'should I buy an LED?'."""

    return bool(_REPLACEMENT_QUESTION.search(str(question or "").lower()))


def _join_names(names: list[str]) -> str:
    return ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else names[0]


def copilot_replacement_answer(result: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    """
    Turn a recommend_replacements() result into a short plain-English answer
    plus a list of compact action dicts (best three recommendations).
    """

    recs = result["recommendations"]
    efficient = [item["name"] for item in result["already_efficient"]]
    unmatched = [item["name"] for item in result["not_assessed"]]
    summary = result["summary"]

    parts: list[str] = []

    if recs:
        parts.append(recs[0]["summary_text"])

        if len(recs) > 1:
            parts.append(
                f"Replacing all {len(recs)} suggested appliances could save about "
                f"{_rupees(summary['total_yearly_saving_rs'])} per year for roughly "
                f"{_rupees(summary['total_investment_rs'])} upfront."
            )
    elif efficient and not unmatched:
        verb = "is" if len(efficient) == 1 else "are"
        parts.append(f"No replacement needed - {_join_names(efficient)} {verb} already efficient.")

    if recs and efficient:
        verb = "is" if len(efficient) == 1 else "are"
        parts.append(f"{_join_names(efficient)} {verb} already efficient.")

    if unmatched:
        parts.append(
            f"I could not match {_join_names(unmatched)} to a known appliance type, "
            "so it was not assessed. Choose its type in the Replacement Advisor."
        )

    if not parts:
        parts.append("There were no appliances to assess.")

    parts.append(
        "These are indicative estimates using typical Indian prices - "
        "enter real quotes in the Replacement Advisor for an accurate payback."
    )

    actions = [
        {
            "appliance": rec["name"],
            "replacement": rec["replacement"]["name"],
            "kwh_saved_per_day": rec["kwh_saved_per_day"],
            "monthly_saving_rs": rec["monthly_saving_rs"],
            "yearly_saving_rs": rec["yearly_saving_rs"],
            "total_replacement_cost_rs": rec["total_replacement_cost_rs"],
            "payback_months": rec["payback_months"],
            "priority": rec["priority"],
        }
        for rec in recs[:3]
    ]

    return " ".join(parts), actions