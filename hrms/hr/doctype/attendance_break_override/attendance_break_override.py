import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate


ALLOWED_ROLES = ("HR User", "HR Manager", "System Manager")


def get_effective_break_minutes(policy_minutes, override_minutes=None):
	"""Use a daily final-value override when present, otherwise the policy value."""
	value = policy_minutes if override_minutes is None else override_minutes
	return max(cint(value), 0)


def _require_break_override_permission():
	frappe.only_for(ALLOWED_ROLES)


def get_submitted_salary_slips(employee, work_date):
	return frappe.get_all(
		"Salary Slip",
		filters={
			"employee": employee,
			"docstatus": 1,
			"start_date": ["<=", work_date],
			"end_date": [">=", work_date],
		},
		pluck="name",
	)


def get_break_override(employee, work_date):
	if not employee or not work_date:
		return None
	work_date = getdate(work_date)
	override = frappe.db.get_value(
		"Attendance Break Override",
		{"employee": employee, "work_date": work_date},
		["name", "break_minutes", "reason", "modified", "modified_by"],
		as_dict=True,
	)
	if not override:
		return None
	return frappe._dict(
		{
			"name": override.name,
			"break_minutes": max(cint(override.break_minutes), 0),
			"reason": override.reason,
			"modified": override.modified,
			"modified_by": override.modified_by,
			"submitted_salary_slips": get_submitted_salary_slips(employee, work_date),
		}
	)


class AttendanceBreakOverride(Document):
	def validate(self):
		if not self.employee or not self.work_date:
			return
		self.work_date = getdate(self.work_date)
		self.break_minutes = max(cint(self.break_minutes), 0)
		if not (self.reason or "").strip():
			frappe.throw(_("دلیل ثبت استثنای استراحت الزامی است."))
		existing = frappe.db.exists(
			"Attendance Break Override",
			{"employee": self.employee, "work_date": self.work_date, "name": ["!=", self.name or ""]},
		)
		if existing:
			frappe.throw(_("برای این کارمند و تاریخ، استثنای استراحت دیگری ثبت شده است."))


@frappe.whitelist()
def get_attendance_break_override(employee, work_date):
	_require_break_override_permission()
	override = get_break_override(employee, work_date)
	return {"override": override, "financially_locked": bool(override and override.submitted_salary_slips)}


@frappe.whitelist()
def save_attendance_break_override(employee, work_date, break_minutes, reason):
	_require_break_override_permission()
	if not employee or not work_date:
		frappe.throw(_("کارمند و تاریخ الزامی هستند."))
	if not (reason or "").strip():
		frappe.throw(_("دلیل ثبت استثنای استراحت الزامی است."))

	existing = frappe.db.get_value(
		"Attendance Break Override", {"employee": employee, "work_date": getdate(work_date)}, "name"
	)
	doc = frappe.get_doc("Attendance Break Override", existing) if existing else frappe.new_doc("Attendance Break Override")
	doc.employee = employee
	doc.work_date = getdate(work_date)
	doc.break_minutes = max(cint(break_minutes), 0)
	doc.reason = reason.strip()
	doc.save()
	frappe.db.commit()
	override = get_break_override(employee, work_date)
	return {
		"success": True,
		"override": override,
		"financially_locked": bool(override.submitted_salary_slips),
		"message": _("استثنای استراحت ذخیره شد."),
	}


@frappe.whitelist()
def clear_attendance_break_override(employee, work_date):
	_require_break_override_permission()
	name = frappe.db.get_value(
		"Attendance Break Override", {"employee": employee, "work_date": getdate(work_date)}, "name"
	)
	if name:
		frappe.delete_doc("Attendance Break Override", name)
		frappe.db.commit()
	return {"success": True, "message": _("استثنای استراحت حذف شد.")}
