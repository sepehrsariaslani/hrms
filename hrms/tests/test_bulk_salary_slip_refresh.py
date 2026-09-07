import unittest

import frappe

from hrms.payroll.doctype.salary_slip.salary_slip import bulk_refresh_from_smart_attendance


class TestBulkSalarySlipRefresh(unittest.TestCase):
	def test_rejects_empty_selection(self):
		with self.assertRaises(frappe.ValidationError):
			bulk_refresh_from_smart_attendance([])
