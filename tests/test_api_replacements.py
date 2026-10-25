"""
API tests for the Replacement Advisor endpoints.

Needs FastAPI's TestClient, which needs httpx:

    python -m pip install httpx
    python -m unittest discover -s tests -v

No real Supabase project is contacted: the tests set dummy settings and
replace the login check with a stub where a logged-in user is needed.
"""

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ["SUPABASE_URL"] = "https://example.invalid"
os.environ["SUPABASE_PUBLISHABLE_KEY"] = "test-publishable-key"

try:
    from fastapi.testclient import TestClient
    from backend import main
except ImportError as error:  # httpx or fastapi missing
    TestClient = None
    IMPORT_ERROR = error


@unittest.skipIf(TestClient is None, "fastapi TestClient (httpx) is not installed")
class ReplacementEndpoints(unittest.TestCase):
    BODY = {
        "tariff": 8,
        "appliances": [
            {"name": "Old bulb", "type_key": "incandescent_bulb",
             "watts": 60, "hours_per_day": 10, "quantity": 1},
            {"name": "LED Bulb", "watts": 9, "hours_per_day": 6, "quantity": 4},
        ],
    }

    def setUp(self):
        self.client = TestClient(main.app)
        main.app.dependency_overrides.clear()

    def tearDown(self):
        main.app.dependency_overrides.clear()

    def login(self):
        main.app.dependency_overrides[main.require_user] = lambda: {"id": "test-user"}

    # ---- protection --------------------------------------------------

    def test_both_endpoints_need_login(self):
        self.assertEqual(self.client.post("/api/replacements", json=self.BODY).status_code, 401)
        self.assertEqual(self.client.get("/api/replacement-types").status_code, 401)

    def test_bad_token_is_rejected(self):
        headers = {"Authorization": "NotBearer abc"}
        self.assertEqual(
            self.client.post("/api/replacements", json=self.BODY, headers=headers).status_code, 401
        )

    def test_existing_endpoints_are_still_protected(self):
        for path in ("manual", "weather", "copilot"):
            self.assertEqual(self.client.post(f"/api/{path}", json={}).status_code, 401, path)

    # ---- behaviour ---------------------------------------------------

    def test_types_endpoint(self):
        self.login()
        response = self.client.get("/api/replacement-types")
        self.assertEqual(response.status_code, 200)
        types = response.json()["types"]
        self.assertGreaterEqual(len(types), 10)
        self.assertIn("incandescent_bulb", [t["type_key"] for t in types])

    def test_recommendations_endpoint(self):
        self.login()
        response = self.client.post("/api/replacements", json=self.BODY)
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(body["status"], "success")

        result = body["result"]
        self.assertEqual(len(result["recommendations"]), 1)
        self.assertEqual(len(result["already_efficient"]), 1)
        self.assertAlmostEqual(result["recommendations"][0]["kwh_saved_per_day"], 0.51, places=3)
        self.assertIn("total_yearly_saving_rs", result["summary"])
        self.assertTrue(result["assumptions"])

    def test_validation_errors_are_422(self):
        self.login()

        bad_hours = {"appliances": [{"name": "x", "watts": 60, "hours_per_day": 30}]}
        self.assertEqual(self.client.post("/api/replacements", json=bad_hours).status_code, 422)

        empty = {"appliances": []}
        self.assertEqual(self.client.post("/api/replacements", json=empty).status_code, 422)

        bad_type = {"appliances": [{"name": "x", "type_key": "toaster", "watts": 60, "hours_per_day": 2}]}
        response = self.client.post("/api/replacements", json=bad_type)
        self.assertEqual(response.status_code, 422)
        self.assertIn("unknown appliance type", response.json()["detail"])


@unittest.skipIf(TestClient is None, "fastapi TestClient (httpx) is not installed")
class CopilotRouting(unittest.TestCase):
    AC = [{"name": "Air Conditioner", "watts": 1500, "hours": 6, "quantity": 1}]

    def setUp(self):
        self.client = TestClient(main.app)
        main.app.dependency_overrides[main.require_user] = lambda: {"id": "test-user"}

    def tearDown(self):
        main.app.dependency_overrides.clear()

    def ask(self, question, appliances=None):
        body = {"question": question, "appliances": appliances or self.AC, "tariff": 8}
        response = self.client.post("/api/copilot", json=body)
        self.assertEqual(response.status_code, 200)
        return response.json()["result"]

    def test_replace_questions_use_the_advisor(self):
        for question in ("Which appliance should I replace?", "Should I buy an LED?",
                         "Is it worth to upgrade my AC"):
            result = self.ask(question)
            self.assertIn("replacement_advisor", result["tools_used"], question)

        result = self.ask("Which appliance should I replace?")
        self.assertIn("5-star inverter air conditioner", result["answer"])
        self.assertEqual(result["replacement_actions"][0]["appliance"], "Air Conditioner")

    def test_efficient_and_unknown_appliances_get_a_sensible_answer(self):
        led = self.ask("should I replace this?", [{"name": "LED Bulb", "watts": 9, "hours": 6, "quantity": 4}])
        self.assertIn("already efficient", led["answer"])

        odd = self.ask("should I replace this?", [{"name": "Toaster", "watts": 800, "hours": 1, "quantity": 1}])
        self.assertIn("could not match", odd["answer"])

    def test_existing_copilot_questions_are_unchanged(self):
        saving = self.ask("How can I reduce my electricity bill?")
        self.assertEqual(saving["tools_used"], ["appliance_energy_calculator", "scenario_optimizer"])
        self.assertTrue(saving["actions"])
        self.assertEqual(saving["replacement_actions"], [])

        ranking = self.ask("Which appliance uses the most energy?")
        self.assertEqual(ranking["tools_used"], ["appliance_energy_calculator"])
        self.assertIn("highest-consuming", ranking["answer"])

        general = self.ask("Tell me about my usage")
        self.assertIn("Highest contributor", general["answer"])


if __name__ == "__main__":
    unittest.main(verbosity=2)