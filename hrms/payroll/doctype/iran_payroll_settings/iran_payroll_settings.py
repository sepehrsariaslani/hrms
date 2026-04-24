import frappe
from frappe.model.document import Document


class IranPayrollSettings(Document):
	def validate(self):
		self.validate_yearly_rules()

	def validate_yearly_rules(self):
		seen_years = set()
		for row in self.get("yearly_rules") or []:
			if row.law_year in seen_years:
				frappe.throw(f"Law year {row.law_year} is duplicated in yearly rules")
			seen_years.add(row.law_year)
