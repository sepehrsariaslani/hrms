# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, get_link_to_form

from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry
from hrms.utils.jalali_helper import jalali_to_gregorian


class LeaveAdjustment(Document):
	def before_validate(self):
		system_precision = cint(frappe.db.get_single_value("System Settings", "float_precision")) or 3
		precision = self.precision("leaves_to_adjust") or system_precision
		self.leaves_to_adjust = flt(self.leaves_to_adjust, precision)
		self.posting_date = normalize_adjustment_posting_date(self.posting_date)

	def before_save(self):
		self.set_leaves_after_adjustment()

	def set_leaves_after_adjustment(self):
		if self.adjustment_type == "Allocate":
			self.leaves_after_adjustment = flt(self.allocated_leaves) + flt(self.leaves_to_adjust)
		elif self.adjustment_type == "Reduce":
			self.leaves_after_adjustment = flt(self.allocated_leaves) - flt(self.leaves_to_adjust)

	def validate(self):
		self.validate_duplicate_leave_adjustment()
		self.validate_non_zero_adjustment()
		self.validate_over_allocation()
		self.validate_leave_balance()

	def validate_duplicate_leave_adjustment(self):
		duplicate_adjustment = frappe.db.exists(
			"Leave Adjustment",
			{"employee": self.employee, "leave_allocation": self.leave_allocation, "docstatus": 1},
		)
		if duplicate_adjustment:
			frappe.throw(
				title=_("Duplicate Leave Adjustment"),
				msg=_(
					"Leave Adjustment for this allocation already exists: {0}. Please amend existing adjustment."
				).format(get_link_to_form("Leave Adjustment", duplicate_adjustment)),
			)

	def validate_non_zero_adjustment(self):
		if self.leaves_to_adjust == 0:
			frappe.throw(_("Enter a non-zero value to adjust."))

	def validate_over_allocation(self):
		if self.adjustment_type == "Reduce":
			return

		max_leaves_allowed = frappe.db.get_value("Leave Type", self.leave_type, "max_leaves_allowed")

		new_allocation = flt(self.allocated_leaves) + flt(self.leaves_to_adjust)

		if max_leaves_allowed and (new_allocation > max_leaves_allowed):
			frappe.throw(
				_("Allocation is greater than the maximum allowed {0} for leave type {1}").format(
					frappe.bold(max_leaves_allowed), frappe.bold(self.leave_type)
				)
			)

	def validate_leave_balance(self):
		if self.adjustment_type == "Allocate":
			return

		leave_balance = get_leave_balance_on(
			employee=self.employee, leave_type=self.leave_type, date=self.posting_date
		)

		if leave_balance < self.leaves_to_adjust:
			frappe.throw(
				_("Reduction is more than {0}'s available leave balance {1} for leave type {2}").format(
					frappe.bold(self.employee_name), frappe.bold(leave_balance), frappe.bold(self.leave_type)
				)
			)

	def on_submit(self):
		self.create_leave_ledger_entry(submit=True)

	def on_cancel(self):
		self.create_leave_ledger_entry(submit=False)

	def create_leave_ledger_entry(self, submit):
		is_lwp = frappe.db.get_value("Leave Type", self.leave_type, "is_lwp")

		args = dict(
			leaves=self.leaves_to_adjust
			if self.adjustment_type == "Allocate"
			else (-1 * self.leaves_to_adjust),
			from_date=self.from_date,
			to_date=self.to_date,
			is_lwp=is_lwp,
		)
		create_leave_ledger_entry(self, args, submit)


@frappe.whitelist()
def get_leave_allocation_for_posting_date(employee, leave_type, posting_date):
	"""
	Returns the leave allocation for the given employee, leave type and posting date.
	"""
	posting_date = normalize_adjustment_posting_date(posting_date)
	return frappe.get_all(
		"Leave Allocation",
		{
			"employee": employee,
			"leave_type": leave_type,
			"from_date": ["<=", posting_date],
			"to_date": [">=", posting_date],
			"docstatus": 1,
		},
		["name"],
	)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_allocated_leave_types(doctype, txt, searchfield, start, page_len, filters):
	"""
	Returns the leave types allocated to the given employee
	"""
	return frappe.get_all(
		"Leave Allocation",
		{
			"employee": filters.get("employee"),
			"docstatus": 1,
		},
		[
			"leave_type",
			"name",
		],
		as_list=1,
	)


def normalize_adjustment_posting_date(posting_date):
	if not posting_date:
		return posting_date

	text = normalize_localized_date_text(posting_date)
	if not text:
		return posting_date

	date_part = text.split(" ", 1)[0]
	parts = date_part.replace("-", "/").split("/")
	if len(parts) != 3:
		return text

	try:
		year = int(parts[0])
	except ValueError:
		return text

	if 1300 <= year <= 1600:
		return jalali_to_gregorian(text)

	return text


def normalize_localized_date_text(value):
	text = str(value).strip()
	if not text:
		return text

	translation = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
	return text.translate(translation).replace("٫", ".").strip()
