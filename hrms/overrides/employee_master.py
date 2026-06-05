# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.model.naming import set_name_by_naming_series
from frappe.utils import add_years, cint, get_link_to_form, getdate
import re

from erpnext.setup.doctype.employee.employee import Employee
from hrms.utils.attendance_device_mapping import DEVICE_MAPPING_TABLE_FIELD, normalize_code, normalize_text

NATIONAL_ID_FIELDS = (
	"custom_national_id_code",
	"national_identity_number",
	"national_id",
	"national_id_no",
	"national_code",
	"custom_national_code",
	"custom_national_id",
)
CHILD_ROW_META_FIELDS = {
	"name",
	"owner",
	"creation",
	"modified",
	"modified_by",
	"parent",
	"parentfield",
	"parenttype",
	"idx",
	"doctype",
	"docstatus",
}


class EmployeeMaster(Employee):
	def set_employee_name(self):
		# Force employee_name to be First Name + Last Name and ignore middle_name.
		self.employee_name = " ".join(filter(lambda x: x, [self.first_name, self.last_name]))

	def validate(self):
		super().validate()
		self.normalize_national_ids()

	def normalize_national_ids(self):
		for fieldname in NATIONAL_ID_FIELDS:
			if not self.meta.has_field(fieldname):
				continue
			normalized = normalize_national_id(self.get(fieldname))
			if normalized and self.get(fieldname) != normalized:
				self.set(fieldname, normalized)

	def before_rename(self, old, new, merge=False):
		# Handle merge conflicts for Employee Skill Map (employee field is unique).
		if not merge:
			return
		self.resolve_employee_skill_map_conflict(old, new)
		self.resolve_attendance_device_mapping_conflict(old, new)

	def resolve_employee_skill_map_conflict(self, old, new):
		old_map_exists = frappe.db.exists("Employee Skill Map", old)
		new_map_exists = frappe.db.exists("Employee Skill Map", new)
		if not (old_map_exists and new_map_exists):
			return

		old_map = frappe.get_doc("Employee Skill Map", old)
		new_map = frappe.get_doc("Employee Skill Map", new)
		updated = False

		for table_field in ("employee_skills", "trainings"):
			existing = {child_row_signature(row) for row in (new_map.get(table_field) or [])}
			for row in old_map.get(table_field) or []:
				signature = child_row_signature(row)
				if signature in existing:
					continue
				new_map.append(table_field, child_row_payload(row))
				existing.add(signature)
				updated = True

		if updated:
			new_map.save(ignore_permissions=True)

		# Remove old map so global link update in merge doesn't hit unique constraint.
		frappe.delete_doc("Employee Skill Map", old, ignore_permissions=True)

	def resolve_attendance_device_mapping_conflict(self, old, new):
		if not frappe.db.exists("DocType", "Employee Attendance Device Mapping"):
			return
		if not self.meta.has_field(DEVICE_MAPPING_TABLE_FIELD):
			return
		if not (frappe.db.exists("Employee", old) and frappe.db.exists("Employee", new)):
			return

		old_doc = frappe.get_doc("Employee", old)
		new_doc = frappe.get_doc("Employee", new)
		updated = False

		existing = {
			(normalize_code(row.get("attendance_device_id")), normalize_text(row.get("device_id")))
			for row in (new_doc.get(DEVICE_MAPPING_TABLE_FIELD) or [])
		}
		for row in old_doc.get(DEVICE_MAPPING_TABLE_FIELD) or []:
			key = (normalize_code(row.get("attendance_device_id")), normalize_text(row.get("device_id")))
			if not key[0] or key in existing:
				continue
			new_doc.append(
				DEVICE_MAPPING_TABLE_FIELD,
				{
					"attendance_device_id": key[0],
					"device_id": key[1],
				},
			)
			existing.add(key)
			updated = True

		if updated:
			new_doc.save(ignore_permissions=True)

	def autoname(self):
		naming_method = frappe.db.get_single_value("HR Settings", "emp_created_by")
		if not naming_method:
			frappe.throw(_("Please setup Employee Naming System in Human Resource > HR Settings"))
		else:
			if naming_method == "Naming Series":
				set_name_by_naming_series(self)
			elif naming_method == "Employee Number":
				self.name = self.employee_number
			elif naming_method == "Full Name":
				self.set_employee_name()
				self.name = self.employee_name

		self.employee = self.name


def normalize_national_id(value):
	digits = re.sub(r"\D", "", str(value or ""))
	if not digits:
		return ""
	if len(digits) < 10:
		return digits.zfill(10)
	if len(digits) > 10:
		return digits[-10:]
	return digits


def child_row_payload(row):
	return {key: value for key, value in row.as_dict().items() if key not in CHILD_ROW_META_FIELDS}


def child_row_signature(row):
	payload = child_row_payload(row)
	return tuple((key, str(payload.get(key) or "")) for key in sorted(payload))


@frappe.whitelist()
def normalize_existing_employee_national_ids():
	updated = 0
	samples = []
	employee_meta = frappe.get_meta("Employee")
	existing_fields = [field for field in NATIONAL_ID_FIELDS if employee_meta.has_field(field)]
	if not existing_fields:
		return {"updated": 0, "fields": [], "sample": []}

	fields = ["name"] + existing_fields
	employees = frappe.get_all("Employee", fields=fields, limit_page_length=0)
	for row in employees:
		changes = {}
		for fieldname in existing_fields:
			normalized = normalize_national_id(row.get(fieldname))
			if normalized and row.get(fieldname) != normalized:
				changes[fieldname] = normalized

		if not changes:
			continue

		frappe.db.set_value("Employee", row["name"], changes, update_modified=False)
		updated += 1
		if len(samples) < 20:
			samples.append({"employee": row["name"], "changes": changes})

	if updated:
		frappe.db.commit()

	return {"updated": updated, "fields": existing_fields, "sample": samples}


@frappe.whitelist()
def normalize_existing_employee_names():
	updated = 0
	samples = []
	employees = frappe.get_all(
		"Employee",
		fields=["name", "first_name", "last_name", "employee_name"],
		limit_page_length=0,
	)
	for row in employees:
		expected = " ".join(filter(None, [row.get("first_name"), row.get("last_name")]))
		if (row.get("employee_name") or "") == expected:
			continue

		frappe.db.set_value(
			"Employee",
			row["name"],
			{"employee_name": expected},
			update_modified=False,
		)
		updated += 1
		if len(samples) < 20:
			samples.append({"employee": row["name"], "employee_name": expected})

	if updated:
		frappe.db.commit()

	return {"updated": updated, "sample": samples}


def validate_onboarding_process(doc, method=None):
	"""Validates Employee Creation for linked Employee Onboarding"""
	if not doc.job_applicant:
		return

	employee_onboarding = frappe.get_all(
		"Employee Onboarding",
		filters={
			"job_applicant": doc.job_applicant,
			"docstatus": 1,
			"boarding_status": ("!=", "Completed"),
		},
	)
	if employee_onboarding:
		onboarding = frappe.get_doc("Employee Onboarding", employee_onboarding[0].name)
		onboarding.validate_employee_creation()
		onboarding.db_set("employee", doc.name)


def publish_update(doc, method=None):
	import hrms

	hrms.refetch_resource("hrms:employee", doc.user_id)


def update_job_applicant_and_offer(doc, method=None):
	"""Updates Job Applicant and Job Offer status as 'Accepted' and submits them"""
	if not doc.job_applicant:
		return

	applicant_status_before_change = frappe.db.get_value("Job Applicant", doc.job_applicant, "status")
	if applicant_status_before_change != "Accepted":
		frappe.db.set_value("Job Applicant", doc.job_applicant, "status", "Accepted")
		frappe.msgprint(
			_("Updated the status of linked Job Applicant {0} to {1}").format(
				get_link_to_form("Job Applicant", doc.job_applicant), frappe.bold(_("Accepted"))
			)
		)
	offer_status_before_change = frappe.db.get_value(
		"Job Offer", {"job_applicant": doc.job_applicant, "docstatus": ["!=", 2]}, "status"
	)
	if offer_status_before_change and offer_status_before_change != "Accepted":
		job_offer = frappe.get_last_doc("Job Offer", filters={"job_applicant": doc.job_applicant})
		job_offer.status = "Accepted"
		job_offer.flags.ignore_mandatory = True
		job_offer.flags.ignore_permissions = True
		job_offer.save()

		msg = _("Updated the status of Job Offer {0} for the linked Job Applicant {1} to {2}").format(
			get_link_to_form("Job Offer", job_offer.name),
			frappe.bold(doc.job_applicant),
			frappe.bold(_("Accepted")),
		)
		if job_offer.docstatus == 0:
			msg += "<br>" + _("You may add additional details, if any, and submit the offer.")

		frappe.msgprint(msg)


def update_approver_role(doc, method=None):
	"""Adds relevant approver role for the user linked to Employee"""
	if doc.leave_approver:
		user = frappe.get_doc("User", doc.leave_approver)
		user.flags.ignore_permissions = True
		user.add_roles("Leave Approver")

	if doc.expense_approver:
		user = frappe.get_doc("User", doc.expense_approver)
		user.flags.ignore_permissions = True
		user.add_roles("Expense Approver")


def update_approver_user_roles(doc, method=None):
	approver_roles = set()
	if frappe.db.exists("Employee", {"leave_approver": doc.name}):
		approver_roles.add("Leave Approver")

	if frappe.db.exists("Employee", {"expense_approver": doc.name}):
		approver_roles.add("Expense Approver")

	if approver_roles:
		doc.append_roles(*approver_roles)


def update_employee_transfer(doc, method=None):
	"""Unsets Employee ID in Employee Transfer if doc is deleted"""
	if frappe.db.exists("Employee Transfer", {"new_employee_id": doc.name, "docstatus": 1}):
		emp_transfer = frappe.get_doc("Employee Transfer", {"new_employee_id": doc.name, "docstatus": 1})
		emp_transfer.db_set("new_employee_id", "")


@frappe.whitelist()
def get_timeline_data(doctype, name):
	"""Return timeline for attendance"""
	from frappe.desk.notifications import get_open_count

	out = {}

	open_count = get_open_count(doctype, name)
	out["count"] = open_count["count"]

	timeline_data = dict(
		frappe.db.sql(
			"""
			select unix_timestamp(attendance_date), count(*)
			from `tabAttendance` where employee=%s
			and attendance_date > date_sub(curdate(), interval 1 year)
			and status in ('Present', 'Half Day')
			group by attendance_date""",
			name,
		)
	)

	out["timeline_data"] = timeline_data
	return out


@frappe.whitelist()
def get_retirement_date(date_of_birth=None):
	if date_of_birth:
		try:
			retirement_age = cint(frappe.db.get_single_value("HR Settings", "retirement_age") or 60)
			dt = add_years(getdate(date_of_birth), retirement_age)
			return dt.strftime("%Y-%m-%d")
		except ValueError:
			# invalid date
			return
