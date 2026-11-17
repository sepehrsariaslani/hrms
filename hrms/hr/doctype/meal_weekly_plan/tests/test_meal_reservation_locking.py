import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


class MealReservationLockingTests(unittest.TestCase):
	def test_employee_day_barrier_is_a_versioned_row_write(self):
		from doctype.meal_weekly_plan.reservation_locking import employee_day_write_barrier

		query, values = employee_day_write_barrier("EMP-1")
		self.assertEqual(query, "update `tabEmployee` set name=name where name=%s")
		self.assertEqual(values, ("EMP-1",))

	def test_plan_day_capacity_barrier_is_a_versioned_row_write(self):
		from doctype.meal_weekly_plan.reservation_locking import plan_day_write_barrier

		query, values = plan_day_write_barrier("PLAN-1", "2026-11-17")
		self.assertEqual(
			query,
			"update `tabMeal Weekly Plan Item` set parent=parent where parent=%s and meal_date=%s",
		)
		self.assertEqual(values, ("PLAN-1", "2026-11-17"))


if __name__ == "__main__":
	unittest.main()
