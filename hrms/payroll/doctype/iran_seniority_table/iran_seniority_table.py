import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class IranSeniorityTable(Document):
	def validate(self):
		self.validate_fiscal_year_uniqueness()
		self.validate_ranges()

	def validate_fiscal_year_uniqueness(self):
		if not self.fiscal_year:
			return

		existing = frappe.db.get_value(
			"Iran Seniority Table",
			{"fiscal_year": self.fiscal_year, "name": ["!=", self.name]},
			"name",
		)
		if existing:
			frappe.throw(_("برای سال مالی {0} قبلاً یک جدول پایه سنوات ثبت شده است.").format(self.fiscal_year))

	def validate_ranges(self):
		seen_min_years = set()
		for row in self.get("rules") or []:
			min_years = cint(row.min_years)
			if min_years in seen_min_years:
				frappe.throw(_("مقدار حداقل سابقه در ردیف {0} تکراری است.").format(row.idx))
			seen_min_years.add(min_years)
