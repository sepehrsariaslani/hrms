import frappe
from frappe.model.document import Document


class IranPayrollSettings(Document):
	def validate(self):
		self.validate_yearly_rules()
		self.validate_designation_rules()

	def validate_yearly_rules(self):
		seen_years = set()
		for row in self.get("yearly_rules") or []:
			if row.law_year in seen_years:
				frappe.throw(f"Law year {row.law_year} is duplicated in yearly rules")
			seen_years.add(row.law_year)

	def validate_designation_rules(self):
		seen_designations = set()
		for row in self.get("designation_rules") or []:
			if not row.designation or not row.company:
				continue
			key = (row.company, row.designation)
			if key in seen_designations:
				frappe.throw(f"سمت سازمانی {row.designation} برای شرکت {row.company} تکراری است.")
			seen_designations.add(key)
