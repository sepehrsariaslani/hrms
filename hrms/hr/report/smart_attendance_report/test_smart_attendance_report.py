from datetime import date, datetime

import frappe
from frappe.utils import flt

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.leave_allocation.test_leave_allocation import create_leave_allocation
from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin
from hrms.hr.doctype.shift_type.test_shift_type import make_shift_assignment, setup_shift_type
from hrms.hr.report.smart_attendance_report.smart_attendance_report import (
	ensure_single_day_leave_application,
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

	def test_smart_attendance_daily_leave_uses_normalized_leave_days(self):
		shift = setup_shift_type(
			shift_type="Smart Attendance Normalized Shift",
			start_time="08:00:00",
			end_time="17:00:00",
			standard_working_hours=8.88,
		)
		employee = make_employee(
			"smart.attendance.normalized.leave@example.com",
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

		leave_application, error = ensure_single_day_leave_application(
			employee,
			"_Test Company",
			"_Test Leave Type",
			date(2026, 8, 5),
		)
		self.assertIsNone(error)

		doc = frappe.get_doc("Leave Application", leave_application)
		self.assertEqual(8.88, flt(doc.total_leave_hours, 2))
		self.assertEqual(1.21, flt(doc.total_leave_days, 2))

	def test_last_period_day_pairs_with_next_day_overnight_exit(self):
		shift = setup_shift_type(
			shift_type="Smart Attendance Overnight Boundary Shift",
			start_time="15:00:00",
			end_time="00:30:00",
			standard_working_hours=7.33,
		)
		employee = make_employee(
			"smart.attendance.overnight.boundary@example.com",
			company="_Test Company",
			default_shift=shift.name,
		)
		make_checkin(employee, datetime(2026, 8, 10, 15, 30), "IN")
		make_checkin(employee, datetime(2026, 8, 11, 0, 3), "OUT")

		rows = get_data(
			{
				"employee": employee,
				"from_date": date(2026, 8, 10),
				"to_date": date(2026, 8, 11),
			}
		)

		self.assertEqual(len(rows), 2)
		self.assertEqual(rows[0]["time_off"], 0)
		self.assertEqual(rows[0]["actual_end"], "00:03(+1)")
		self.assertEqual(rows[0]["log_status"], "✅ کامل")
		self.assertEqual(rows[1]["all_logs"], "")
		self.assertFalse(rows[1]["has_issue"])

	def test_approved_leave_overrides_single_stray_checkin_shortage(self):
		shift = setup_shift_type(
			shift_type="Smart Attendance Leave Stray Log Shift",
			start_time="08:00:00",
			end_time="16:20:00",
			standard_working_hours=7.33,
		)
		employee = make_employee(
			"smart.attendance.leave.stray@example.com",
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
		make_leave_application(employee, date(2026, 8, 12), date(2026, 8, 12), "_Test Leave Type")
		make_checkin(employee, datetime(2026, 8, 12, 0, 1), "OUT")

		rows = get_data(
			{
				"employee": employee,
				"from_date": date(2026, 8, 12),
				"to_date": date(2026, 8, 12),
			}
		)

		self.assertEqual(rows[0]["leave_hours"], 7.33)
		self.assertEqual(rows[0]["time_off"], 0)
		self.assertTrue(rows[0]["has_issue"])
