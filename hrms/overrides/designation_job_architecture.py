import frappe
from frappe.utils import flt


def apply_job_score(doc, method=None):
	"""Keep total job score aligned with the three grading factors."""
	if doc.doctype != "Designation":
		return

	if not frappe.db.has_column("Designation", "job_score"):
		return

	doc.job_score = flt(doc.get("know_how_score")) + flt(doc.get("problem_solving_score")) + flt(
		doc.get("accountability_score")
	)

