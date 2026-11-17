import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from doctype.meal_weekly_plan.meal_rules import (
    can_activate_reservation,
    has_portion_capacity,
    retains_existing_portion_claim,
)


class MealRulesTests(unittest.TestCase):
    def test_only_one_active_reservation_per_employee_company_day(self):
        self.assertTrue(can_activate_reservation([], "Reserved"))
        self.assertFalse(can_activate_reservation(["Reserved"], "Reserved"))
        self.assertFalse(can_activate_reservation(["Delivered"], "Reserved"))
        self.assertTrue(can_activate_reservation(["Not Required"], "Reserved"))
        self.assertTrue(can_activate_reservation(["Reserved"], "Not Required"))

    def test_reservation_respects_optional_daily_plan_capacity(self):
        self.assertTrue(has_portion_capacity(10, None))
        self.assertTrue(has_portion_capacity(1, 2))
        self.assertFalse(has_portion_capacity(2, 2))
        self.assertFalse(has_portion_capacity(0, 0))

    def test_existing_reservation_does_not_consume_another_portion(self):
        self.assertTrue(has_portion_capacity(2, 2, already_reserved=True))

    def test_only_same_active_plan_day_retains_its_portion_claim(self):
        self.assertTrue(
            retains_existing_portion_claim(
                previous_status="Reserved",
                previous_plan="PLAN-1",
                previous_date="2026-11-16",
                plan="PLAN-1",
                meal_date="2026-11-16",
            )
        )
        self.assertFalse(
            retains_existing_portion_claim(
                previous_status="Reserved",
                previous_plan="PLAN-1",
                previous_date="2026-11-16",
                plan="PLAN-2",
                meal_date="2026-11-16",
            )
        )
        self.assertFalse(
            retains_existing_portion_claim(
                previous_status="Not Required",
                previous_plan="PLAN-1",
                previous_date="2026-11-16",
                plan="PLAN-1",
                meal_date="2026-11-16",
            )
        )


if __name__ == "__main__":
    unittest.main()
