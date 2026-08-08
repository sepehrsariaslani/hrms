from datetime import date

import frappe
from frappe.utils import flt

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.leave_allocation.test_leave_allocation import create_leave_allocation
from hrms.hr.doctype.shift_type.test_shift_type import make_shift_assignment, setup_shift_type
from hrms.hr.report.smart_attendance_report.smart_attendance_report import (
	get_employee_shifts,
	get_leave_map,
)
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_leave_application
from hrms.tests.utils import HRMSTestSuite


class TestSmartAttendanceReport(HRMSTestSuite):
	def setUp(self):
		frappe.db.set_single_value("HR Settings", "standard_working_hours", 7.33)

	def test_daily_leave_uses_default_shift_hours_when_no_assignment_exists(self):
		shift = setup_shift_type(
			shift_type="Smart Attendance Default Shift",
			start_time="08:00:00",
			end_time="17:00:00",
			standard_working_hours=8.88,
		)
		employee = make_employee(
			"smart.attendance.default.shift@example.com",
			company="_Test Company",
			default_shift=shift.name,
		)
		create_leave_allocation(
			employee=employee,
			leave_type="_Test Leave Type",
			from_date=date(2026, 8, 1),
			to_date=date(2026, 8, 31),
			new_leaves_allocated=15,
		).insert().submit()
		make_leave_application(employee, date(2026, 8, 5), date(2026, 8, 5), "_Test Leave Type")

		filters = frappe._dict(
			{
				"company": "_Test Company",
				"employee": employee,
				"from_date": date(2026, 8, 5),
				"to_date": date(2026, 8, 5),
			}
		)

		shifts = get_employee_shifts(filters)
		self.assertEqual("Smart Attendance Default Shift", shifts[(employee, date(2026, 8, 5))]["shift_type"])

		leave_map = get_leave_map(filters, shifts)
		self.assertEqual(8.88, flt(leave_map[(employee, date(2026, 8, 5))]["hours"], 2))

	def test_shift_assignment_overrides_default_shift_hours(self):
		default_shift = setup_shift_type(
			shift_type="Smart Attendance Base Shift",
			start_time="08:00:00",
			end_time="17:00:00",
			standard_working_hours=8.88,
		)
		override_shift = setup_shift_type(
			shift_type="Smart Attendance Override Shift",
			start_time="08:00:00",
			end_time="16:00:00",
			standard_working_hours=6.5,
		)
		employee = make_employee(
			"smart.attendance.override.shift@example.com",
			company="_Test Company",
			default_shift=default_shift.name,
		)
		make_shift_assignment(override_shift.name, employee, date(2026, 8, 5), date(2026, 8, 5))

		filters = frappe._dict(
			{
				"company": "_Test Company",
				"employee": employee,
				"from_date": date(2026, 8, 5),
				"to_date": date(2026, 8, 5),
			}
		)

		shifts = get_employee_shifts(filters)
		self.assertEqual("Smart Attendance Override Shift", shifts[(employee, date(2026, 8, 5))]["shift_type"])
		self.assertEqual(6.5, flt(shifts[(employee, date(2026, 8, 5))]["standard_working_hours"], 2))
