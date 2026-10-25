"""
Unit tests for src/replacement_advisor.py

Run from the project root (no extra packages needed):

    python -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from replacement_advisor import (  # noqa: E402
    CATALOG,
    copilot_replacement_answer,
    is_replacement_question,
    list_replacement_types,
    recommend_replacements,
)


def item(name, watts, hours, quantity=1, **extra):
    return {"name": name, "watts": watts, "hours_per_day": hours, "quantity": quantity, **extra}


class IncandescentToLed(unittest.TestCase):
    def setUp(self):
        out = recommend_replacements(
            [item("Old bulb", 60, 10, type_key="incandescent_bulb")], tariff_per_kwh=8
        )
        self.rec = out["recommendations"][0]
        self.out = out

    def test_energy_and_money(self):
        # (60 - 9) W x 10 h / 1000 = 0.51 kWh per day
        self.assertAlmostEqual(self.rec["kwh_saved_per_day"], 0.51, places=3)
        self.assertAlmostEqual(self.rec["monthly_saving_rs"], 0.51 * 30 * 8, places=2)
        self.assertAlmostEqual(self.rec["yearly_saving_rs"], 0.51 * 365 * 8, places=2)

    def test_cost_payback_priority(self):
        self.assertEqual(self.rec["replacement"]["name"], "LED bulb")
        self.assertEqual(self.rec["replacement"]["watts"], 9)
        self.assertEqual(self.rec["total_replacement_cost_rs"], 100)
        self.assertAlmostEqual(self.rec["payback_months"], 100 / (0.51 * 30 * 8), places=1)
        self.assertEqual(self.rec["priority"], "High")

    def test_user_watts_are_never_overwritten(self):
        self.assertEqual(self.rec["old_watts"], 60)

    def test_sentence_matches_requested_style(self):
        text = self.rec["summary_text"]
        self.assertIn("Replace your Old bulb (60 W) with an LED bulb (9 W)", text)
        self.assertIn("0.51 kWh per day", text)
        self.assertIn("pays for itself", text)

    def test_summary_totals(self):
        s = self.out["summary"]
        self.assertEqual(s["recommended_count"], 1)
        self.assertAlmostEqual(s["total_yearly_saving_rs"], self.rec["yearly_saving_rs"], places=2)
        self.assertEqual(s["total_investment_rs"], 100)
        self.assertAlmostEqual(self.rec["share_of_savings_pct"], 100.0)


class AlreadyEfficient(unittest.TestCase):
    def test_led_bulb_at_replacement_wattage(self):
        out = recommend_replacements([item("Bulb", 9, 6, type_key="incandescent_bulb")])
        self.assertEqual(out["recommendations"], [])
        self.assertEqual(len(out["already_efficient"]), 1)
        self.assertEqual(out["summary"]["already_efficient_count"], 1)

    def test_within_ten_percent_is_efficient_but_above_is_not(self):
        near = recommend_replacements([item("Bulb", 9.9, 6, type_key="incandescent_bulb")])
        far = recommend_replacements([item("Bulb", 10.5, 6, type_key="incandescent_bulb")])
        self.assertEqual(len(near["already_efficient"]), 1)
        self.assertEqual(len(far["recommendations"]), 1)

    def test_name_that_says_led_is_efficient_without_a_type(self):
        out = recommend_replacements([item("LED Bulb", 9, 6, 4)])
        self.assertEqual(out["recommendations"], [])
        self.assertEqual(out["already_efficient"][0]["name"], "LED Bulb")

    def test_non_inverter_ac_is_not_mistaken_for_inverter(self):
        out = recommend_replacements([item("Non-inverter AC", 1500, 6)])
        self.assertEqual(len(out["recommendations"]), 1)
        self.assertEqual(out["recommendations"][0]["type_key"], "air_conditioner")


class KeywordFallback(unittest.TestCase):
    def detect(self, name, watts):
        out = recommend_replacements([item(name, watts, 5)])
        recs = out["recommendations"]
        return recs[0]["type_key"] if recs else None

    def test_common_names(self):
        self.assertEqual(self.detect("Old tube light", 40), "tube_light")
        self.assertEqual(self.detect("Ceiling Fan", 75), "ceiling_fan")
        self.assertEqual(self.detect("Air Conditioner", 1500), "air_conditioner")
        self.assertEqual(self.detect("Bedroom AC", 1600), "air_conditioner")
        self.assertEqual(self.detect("Refrigerator", 220), "refrigerator")
        self.assertEqual(self.detect("Water heater", 2000), "geyser")

    def test_bulb_uses_watts_to_choose_between_incandescent_and_cfl(self):
        self.assertEqual(self.detect("Bulb", 60), "incandescent_bulb")
        self.assertEqual(self.detect("Bulb", 18), "cfl")

    def test_unknown_name_is_not_assessed_not_an_error(self):
        out = recommend_replacements([item("Toaster", 800, 1)])
        self.assertEqual(out["recommendations"], [])
        self.assertEqual(out["not_assessed"][0]["name"], "Toaster")

    def test_explicit_type_beats_the_name(self):
        out = recommend_replacements([item("Thing", 75, 5, type_key="ceiling_fan")])
        self.assertEqual(out["recommendations"][0]["type_key"], "ceiling_fan")
        self.assertFalse(out["recommendations"][0]["auto_detected"])


class ZeroAndEdgeCases(unittest.TestCase):
    def test_zero_hours_is_not_assessed(self):
        out = recommend_replacements([item("Old bulb", 60, 0, type_key="incandescent_bulb")])
        self.assertEqual(out["recommendations"], [])
        self.assertIn("Hours per day is 0", out["not_assessed"][0]["reason"])
        self.assertEqual(out["summary"]["total_yearly_saving_rs"], 0)
        self.assertIsNone(out["summary"]["overall_payback_months"])

    def test_zero_watts_is_not_assessed(self):
        out = recommend_replacements([item("Old bulb", 0, 5, type_key="incandescent_bulb")])
        self.assertEqual(len(out["not_assessed"]), 1)

    def test_zero_tariff_gives_no_payback_and_no_crash(self):
        out = recommend_replacements([item("Old bulb", 60, 5, type_key="incandescent_bulb")], 0)
        rec = out["recommendations"][0]
        self.assertGreater(rec["kwh_saved_per_day"], 0)
        self.assertEqual(rec["yearly_saving_rs"], 0)
        self.assertIsNone(rec["payback_months"])
        self.assertEqual(rec["priority"], "Low")

    def test_user_quote_overrides_catalog(self):
        out = recommend_replacements([
            item("Old bulb", 60, 10, type_key="incandescent_bulb",
                 replacement_watts=12, replacement_cost_rs=150)
        ])
        rec = out["recommendations"][0]
        self.assertEqual(rec["replacement"]["watts"], 12)
        self.assertEqual(rec["replacement"]["watts_source"], "your quote")
        self.assertAlmostEqual(rec["kwh_saved_per_day"], 0.48, places=3)
        self.assertEqual(rec["total_replacement_cost_rs"], 150)

    def test_quantity_multiplies_savings_and_cost(self):
        one = recommend_replacements([item("b", 60, 5, 1, type_key="incandescent_bulb")])
        four = recommend_replacements([item("b", 60, 5, 4, type_key="incandescent_bulb")])
        a, b = one["recommendations"][0], four["recommendations"][0]
        self.assertAlmostEqual(b["kwh_saved_per_day"], a["kwh_saved_per_day"] * 4, places=3)
        self.assertEqual(b["total_replacement_cost_rs"], 400)
        self.assertEqual(a["payback_months"], b["payback_months"])


class PriorityBoundaries(unittest.TestCase):
    def priority(self, cost):
        # monthly saving = 0.51 kWh x 30 x Rs 8 = Rs 122.40
        out = recommend_replacements([
            item("b", 60, 10, type_key="incandescent_bulb", replacement_cost_rs=cost)
        ])
        return out["recommendations"][0]["priority"]

    def test_bands(self):
        self.assertEqual(self.priority(1400), "High")     # 11.4 months
        self.assertEqual(self.priority(1500), "Medium")   # 12.3 months
        self.assertEqual(self.priority(4400), "Medium")   # 35.9 months
        self.assertEqual(self.priority(4500), "Low")      # 36.8 months


class SortingAndSummary(unittest.TestCase):
    def test_sorted_by_yearly_saving_and_totals_add_up(self):
        out = recommend_replacements([
            item("Bulb", 60, 5, 2, type_key="incandescent_bulb"),
            item("AC", 1500, 6, 1, type_key="air_conditioner"),
            item("Fan", 75, 10, 2, type_key="ceiling_fan"),
        ])
        recs = out["recommendations"]
        yearly = [r["yearly_saving_rs"] for r in recs]
        self.assertEqual(yearly, sorted(yearly, reverse=True))
        self.assertEqual(recs[0]["type_key"], "air_conditioner")
        self.assertAlmostEqual(sum(r["share_of_savings_pct"] for r in recs), 100.0, delta=0.2)
        self.assertAlmostEqual(
            out["summary"]["total_yearly_saving_rs"], sum(yearly), delta=0.05
        )
        self.assertAlmostEqual(
            out["summary"]["total_investment_rs"],
            sum(r["total_replacement_cost_rs"] for r in recs), places=2,
        )

    def test_assumptions_are_returned(self):
        out = recommend_replacements([item("b", 60, 5, type_key="incandescent_bulb")])
        self.assertGreaterEqual(len(out["assumptions"]), 4)
        self.assertTrue(any("indicative" in a.lower() for a in out["assumptions"]))


class Validation(unittest.TestCase):
    def bad(self, **kwargs):
        base = item("Old bulb", 60, 5, type_key="incandescent_bulb")
        base.update(kwargs)
        with self.assertRaises(ValueError):
            recommend_replacements([base])

    def test_rejects_bad_numbers(self):
        self.bad(hours_per_day=25)
        self.bad(hours_per_day=-1)
        self.bad(watts=-5)
        self.bad(watts=float("nan"))
        self.bad(watts="lots")
        self.bad(quantity=0)
        self.bad(quantity=2.5)
        self.bad(age_years=-1)
        self.bad(replacement_cost_rs=-10)

    def test_rejects_bad_structure(self):
        with self.assertRaises(ValueError):
            recommend_replacements([])
        with self.assertRaises(ValueError):
            recommend_replacements([item("", 60, 5)])
        with self.assertRaises(ValueError):
            recommend_replacements([item("x", 60, 5, type_key="toaster")])
        with self.assertRaises(ValueError):
            recommend_replacements([item("x", 60, 5)], tariff_per_kwh=-1)

    def test_auto_type_values_are_accepted(self):
        out = recommend_replacements([item("Old tube light", 40, 5, type_key="auto")])
        self.assertEqual(out["recommendations"][0]["type_key"], "tube_light")
        out = recommend_replacements([item("Old tube light", 40, 5, type_key="")])
        self.assertEqual(out["recommendations"][0]["type_key"], "tube_light")


class Catalog(unittest.TestCase):
    REQUIRED = {"type_key", "label", "min_w", "max_w", "replacement",
                "replacement_w", "replacement_cost_rs", "lifespan_years", "keywords"}

    def test_entries_are_complete_and_sane(self):
        keys = [e["type_key"] for e in CATALOG]
        self.assertEqual(len(keys), len(set(keys)), "duplicate type_key")
        self.assertGreaterEqual(len(CATALOG), 10)

        for entry in CATALOG:
            self.assertTrue(self.REQUIRED <= set(entry), entry["type_key"])
            self.assertLess(entry["min_w"], entry["max_w"], entry["type_key"])
            self.assertLess(entry["replacement_w"], entry["max_w"], entry["type_key"])
            self.assertGreater(entry["replacement_cost_rs"], 0, entry["type_key"])

    def test_dropdown_list_hides_internal_fields(self):
        listing = list_replacement_types()
        self.assertEqual(len(listing), len(CATALOG))
        self.assertNotIn("keywords", listing[0])
        self.assertIn("label", listing[0])


class ExcludedNames(unittest.TestCase):
    def test_exhaust_fan_is_not_a_ceiling_fan_and_room_heater_is_not_a_geyser(self):
        out = recommend_replacements([item("Exhaust fan", 40, 4), item("Room heater", 1500, 2)])
        self.assertEqual(out["recommendations"], [])
        self.assertEqual({entry["name"] for entry in out["not_assessed"]}, {"Exhaust fan", "Room heater"})

    def test_plain_fan_and_water_heater_still_match(self):
        out = recommend_replacements([item("Fan", 75, 8), item("Water heater", 2000, 1)])
        self.assertEqual({rec["type_key"] for rec in out["recommendations"]}, {"ceiling_fan", "geyser"})


class CopilotHelpers(unittest.TestCase):
    def test_question_detection(self):
        for question in ("Which appliance should I replace?", "Should I buy an LED?",
                         "Is it worth to upgrade my AC", "कौन सा उपकरण बदलूं"):
            self.assertTrue(is_replacement_question(question), question)

        for question in ("How can I reduce my electricity bill?", "Which appliance uses the most energy?",
                         "Tell me about my usage", "The electrician called", ""):
            self.assertFalse(is_replacement_question(question), question)

    def test_answer_mentions_replacement_efficient_and_unmatched(self):
        result = recommend_replacements([
            item("Air Conditioner", 1500, 6), item("LED Bulb", 9, 6, 4), item("Toaster", 800, 1),
        ])
        answer, actions = copilot_replacement_answer(result)

        self.assertIn("5-star inverter air conditioner", answer)
        self.assertIn("LED Bulb is already efficient", answer)
        self.assertIn("could not match Toaster", answer)
        self.assertEqual([a["appliance"] for a in actions], ["Air Conditioner"])

    def test_answer_when_everything_is_efficient(self):
        answer, actions = copilot_replacement_answer(recommend_replacements([item("LED Bulb", 9, 6, 4)]))
        self.assertIn("already efficient", answer)
        self.assertEqual(actions, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)