import frappe
from erpnext.setup.doctype.employee.test_employee import make_employee
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate

from hrms.hr.doctype.meal_weekly_plan.meal_weekly_plan import get_week_start_date


test_dependencies = ["Employee"]


class TestMealReservationIntegration(FrappeTestCase):
	def setUp(self):
		self.company = "_Test Company"
		self.meal_date = nowdate()

	def _make_employee(self):
		email = f"meal-reservation-{frappe.generate_hash(length=10)}@example.com"
		return make_employee(email, company=self.company)

	def _make_plan(self, max_portions=1):
		plan = frappe.get_doc(
			{
				"doctype": "Meal Weekly Plan",
				"company": self.company,
				"week_start_date": get_week_start_date(self.meal_date),
				"cutoff_time": "23:59:00",
				"status": "Draft",
				"meal_items": [
					{
						"meal_date": self.meal_date,
						"meal_type": "Lunch",
						"is_available": 0,
						"max_portions": max_portions,
					}
				],
			}
		)
		plan.insert(ignore_permissions=True)
		return plan

	def _make_reservation(self, plan, employee, status="Reserved"):
		reservation = frappe.get_doc(
			{
				"doctype": "Meal Reservation",
				"meal_plan": plan.name,
				"company": self.company,
				"reservation_date": self.meal_date,
				"employee": employee,
				"reservation_status": status,
			}
		)
		reservation.insert(ignore_permissions=True)
		return reservation

	def test_rejects_active_reservation_for_same_employee_company_date_across_plans(self):
		employee = self._make_employee()
		first_plan = self._make_plan(max_portions=10)
		second_plan = self._make_plan(max_portions=10)
		self._make_reservation(first_plan, employee)

		with self.assertRaises(frappe.ValidationError):
			self._make_reservation(second_plan, employee)

	def test_rejects_reservation_when_plan_max_portions_is_reached(self):
		plan = self._make_plan(max_portions=1)
		self._make_reservation(plan, self._make_employee())

		with self.assertRaises(frappe.ValidationError):
			self._make_reservation(plan, self._make_employee())

	def test_not_required_reservation_releases_its_plan_portion(self):
		plan = self._make_plan(max_portions=1)
		reservation = self._make_reservation(plan, self._make_employee())
		reservation.reservation_status = "Not Required"
		reservation.save(ignore_permissions=True)

		second_reservation = self._make_reservation(plan, self._make_employee())

		self.assertEqual(second_reservation.reservation_status, "Reserved")
		self.assertEqual(
			frappe.db.count(
				"Meal Reservation",
				{
					"meal_plan": plan.name,
					"reservation_date": self.meal_date,
					"reservation_status": "Reserved",
				},
			),
			1,
		)

	def test_editing_existing_active_reservation_at_capacity_keeps_its_claim(self):
		plan = self._make_plan(max_portions=1)
		reservation = self._make_reservation(plan, self._make_employee())
		reservation.reservation_note = "Updated note"
		reservation.save(ignore_permissions=True)

		self.assertEqual(reservation.reservation_note, "Updated note")
		self.assertEqual(reservation.reservation_status, "Reserved")
		self.assertEqual(
			frappe.db.count(
				"Meal Reservation",
				{
					"meal_plan": plan.name,
					"reservation_date": self.meal_date,
					"reservation_status": "Reserved",
				},
			),
			1,
		)

	def test_moving_existing_active_reservation_to_full_plan_is_rejected(self):
		first_plan = self._make_plan(max_portions=1)
		full_plan = self._make_plan(max_portions=1)
		reservation = self._make_reservation(first_plan, self._make_employee())
		self._make_reservation(full_plan, self._make_employee())

		reservation.meal_plan = full_plan.name
		with self.assertRaises(frappe.ValidationError):
			reservation.save(ignore_permissions=True)
