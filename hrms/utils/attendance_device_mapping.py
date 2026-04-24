import re

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

DEVICE_MAPPING_DOCTYPE = "Employee Attendance Device Mapping"
DEVICE_MAPPING_TABLE_FIELD = "custom_attendance_device_mappings"
ATTENDANCE_DEVICE_DOCTYPE = "Attendance Device"

PERSIAN_CHAR_MAP = str.maketrans(
	{
		"ي": "ی",
		"ى": "ی",
		"ئ": "ی",
		"ك": "ک",
		"ة": "ه",
		"ۀ": "ه",
		"ؤ": "و",
		"\u200c": " ",
		"\u200f": "",
		"\u200e": "",
	}
)
PERSIAN_DIGITS_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


EMPLOYEE_DEVICE_CUSTOM_FIELDS = {
	"Employee": [
		{
			"fieldname": DEVICE_MAPPING_TABLE_FIELD,
			"label": "Attendance Device Mappings",
			"fieldtype": "Table",
			"options": DEVICE_MAPPING_DOCTYPE,
			"insert_after": "attendance_device_id",
		}
	]
}


def normalize_text(value):
	text = str(value or "").strip()
	if not text or text.lower() in {"nan", "none", "null"}:
		return ""
	text = text.translate(PERSIAN_CHAR_MAP).translate(PERSIAN_DIGITS_MAP)
	return " ".join(text.split())


def normalize_code(value):
	text = normalize_text(value)
	if not text:
		return ""
	if re.fullmatch(r"-?\d+\.0+", text):
		return text.split(".", 1)[0]
	return text


def normalize_device_identifier(value):
	text = normalize_code(value)
	if not text:
		return ""
	if "|" not in text:
		return text
	parts = [normalize_code(part) for part in text.split("|") if normalize_code(part)]
	return parts[0] if parts else ""


def ensure_employee_device_mapping_setup(hide_legacy_field=True):
	create_custom_fields(EMPLOYEE_DEVICE_CUSTOM_FIELDS, update=True)
	employee_meta = frappe.get_meta("Employee")
	if hide_legacy_field and employee_meta.has_field("attendance_device_id"):
		make_property_setter(
			"Employee",
			"attendance_device_id",
			"hidden",
			1,
			"Check",
			validate_fields_for_doctype=False,
		)
		make_property_setter(
			"Employee",
			"attendance_device_id",
			"read_only",
			1,
			"Check",
			validate_fields_for_doctype=False,
		)
		make_property_setter(
			"Employee",
			"attendance_device_id",
			"description",
			"Deprecated. Use Attendance Device Mappings table.",
			"Text",
			validate_fields_for_doctype=False,
		)
	frappe.clear_cache(doctype="Employee")


def _normalized_mapping_key(attendance_device_id, device_id):
	return normalize_code(attendance_device_id), normalize_device_identifier(device_id)


def append_employee_device_mapping(
	employee_doc,
	attendance_device_id,
	device_id=None,
	company=None,
	location=None,
):
	code, device = _normalized_mapping_key(attendance_device_id, device_id)
	if not code:
		return False
	if not employee_doc.meta.has_field(DEVICE_MAPPING_TABLE_FIELD):
		return False

	device_link = (
		ensure_attendance_device(
			device,
			company=company or employee_doc.get("company"),
			location=location,
		)
		if device
		else ""
	)

	existing = {
		_normalized_mapping_key(row.get("attendance_device_id"), row.get("device_id"))
		for row in (employee_doc.get(DEVICE_MAPPING_TABLE_FIELD) or [])
	}
	if (code, device_link) in existing:
		return False

	employee_doc.append(
		DEVICE_MAPPING_TABLE_FIELD,
		{
			"attendance_device_id": code,
			"device_id": device_link,
		},
	)
	return True


def get_employee_mapping_rows():
	if not frappe.db.exists("DocType", DEVICE_MAPPING_DOCTYPE):
		return []
	return frappe.get_all(
		DEVICE_MAPPING_DOCTYPE,
		fields=["parent", "device_id", "attendance_device_id"],
		filters={"parenttype": "Employee"},
		limit_page_length=0,
	)


def ensure_attendance_device(device_id, company=None, location=None):
	device_id = normalize_device_identifier(device_id)
	if not device_id:
		return ""
	if not frappe.db.exists("DocType", ATTENDANCE_DEVICE_DOCTYPE):
		return device_id

	existing = frappe.db.get_value(
		ATTENDANCE_DEVICE_DOCTYPE,
		{"device_id": device_id},
		["name", "company", "location"],
		as_dict=True,
	)
	if existing:
		updates = {}
		if company and not existing.company:
			updates["company"] = company
		if location and not existing.location:
			updates["location"] = location
		if updates:
			frappe.db.set_value(ATTENDANCE_DEVICE_DOCTYPE, existing.name, updates, update_modified=False)
		return existing.name

	doc = frappe.get_doc(
		{
			"doctype": ATTENDANCE_DEVICE_DOCTYPE,
			"device_id": device_id,
			"company": company,
			"location": normalize_text(location),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def resolve_employee_by_attendance_device_id(attendance_device_id, device_id=None):
	code = normalize_code(attendance_device_id)
	device = normalize_device_identifier(device_id)
	if not code:
		return "", "empty_code", []

	rows = []
	if frappe.db.exists("DocType", DEVICE_MAPPING_DOCTYPE):
		rows = frappe.get_all(
			DEVICE_MAPPING_DOCTYPE,
			fields=["parent", "device_id"],
			filters={
				"parenttype": "Employee",
				"attendance_device_id": code,
			},
			limit_page_length=0,
		)

	if rows and device:
		device_keys = {device}
		if frappe.db.exists("DocType", ATTENDANCE_DEVICE_DOCTYPE):
			by_location = frappe.get_all(
				ATTENDANCE_DEVICE_DOCTYPE,
				filters={"location": device},
				pluck="name",
			)
			by_device_id = frappe.get_all(
				ATTENDANCE_DEVICE_DOCTYPE,
				filters={"device_id": device},
				pluck="name",
			)
			device_keys.update({normalize_text(value) for value in by_location + by_device_id})

		device_matches = [
			row.parent for row in rows if normalize_text(row.device_id) in device_keys
		]
		unique_device_matches = sorted(set(device_matches))
		if len(unique_device_matches) == 1:
			return unique_device_matches[0], "table_device+code", []
		if len(unique_device_matches) > 1:
			return "", "ambiguous_table_device+code", unique_device_matches

	parents = sorted({row.parent for row in rows})
	if len(parents) == 1:
		return parents[0], "table_code", []
	if len(parents) > 1:
		return "", "ambiguous_table_code", parents

	legacy_matches = frappe.get_all(
		"Employee",
		fields=["name"],
		filters={"attendance_device_id": code},
		limit_page_length=0,
	)
	legacy_names = sorted({row.name for row in legacy_matches})
	if len(legacy_names) == 1:
		return legacy_names[0], "legacy_field", []
	if len(legacy_names) > 1:
		return "", "ambiguous_legacy_field", legacy_names

	return "", "not_found", []


@frappe.whitelist()
def upsert_employee_device_mapping(employee, attendance_device_id, device_id=None, location=None):
	if not employee:
		frappe.throw("employee is required")

	employee_doc = frappe.get_doc("Employee", employee)
	changed = append_employee_device_mapping(
		employee_doc,
		attendance_device_id,
		device_id=device_id,
		company=employee_doc.get("company"),
		location=location,
	)
	if not changed:
		return {
			"employee": employee_doc.name,
			"added": False,
			"message": "mapping already exists or empty code",
		}

	employee_doc.flags.ignore_permissions = True
	employee_doc.flags.ignore_mandatory = True
	employee_doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"employee": employee_doc.name,
		"added": True,
		"attendance_device_id": normalize_code(attendance_device_id),
		"device_id": normalize_device_identifier(device_id),
	}
