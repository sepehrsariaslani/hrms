# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import copy

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists

from hrms.payroll.utils import sanitize_expression


# fields that define how a Salary Component contributes to a Salary Structure row.
# These are kept in sync on the linked Salary Detail rows whenever the component changes.
SYNC_FIELDS = (
	"amount",
	"depends_on_payment_days",
	"variable_based_on_taxable_salary",
	"is_tax_applicable",
	"is_flexible_benefit",
	"statistical_component",
	"do_not_include_in_total",
	"do_not_include_in_accounts",
	"exempted_from_income_tax",
	"deduct_full_tax_on_selected_payroll_date",
	"accrual_component",
)


class SalaryComponent(Document):
	def before_validate(self):
		self._condition, self.condition = self.condition, sanitize_expression(self.condition)
		self._formula, self.formula = self.formula, sanitize_expression(self.formula)

	def validate(self):
		self.validate_abbr()
		self.validate_accounts()
		self.validate_accrual_component()
		self.valide_arrear_component()

	def on_update(self):
		# set old values (allowing multiline strings for better readability in the doctype form)
		if self._condition != self.condition:
			self.db_set("condition", self._condition)
		if self._formula != self.formula:
			self.db_set("formula", self._formula)

		# automatically propagate this component's configuration to every Salary
		# Structure that uses it, so the structure (and hence the Salary Slip)
		# always follows the latest component values without manual syncing.
		self.sync_salary_structures()

	def sync_salary_structures(self):
		"""Sync this component's config to all linked (non-cancelled) Salary Structures."""
		structures = self.get_structures_to_be_updated()
		if not structures:
			return

		for structure in structures:
			salary_structure = frappe.get_doc("Salary Structure", structure)
			# only used for versioning; avoids separate db calls with load_doc_before_save
			salary_structure._doc_before_save = copy.deepcopy(salary_structure)

			salary_detail_row = next(
				(
					d
					for d in salary_structure.get(f"{self.type.lower()}s")
					if d.salary_component == self.name
				),
				None,
			)
			if not salary_detail_row:
				continue

			salary_detail_row.set("amount_based_on_formula", self.amount_based_on_formula)
			salary_detail_row.set("formula", self._formula if self.amount_based_on_formula else None)
			salary_detail_row.set("condition", self._condition)

			for field in SYNC_FIELDS:
				if hasattr(self, field):
					salary_detail_row.set(field, self.get(field))

			salary_structure.db_update_all()
			# db_update_all() does not invalidate the cached Salary Structure,
			# so clear the cache so new Salary Slips pick up the changes immediately.
			salary_structure.clear_cache()
			salary_structure.flags.updater_reference = {
				"doctype": self.doctype,
				"docname": self.name,
				"label": _("via Salary Component sync"),
			}

	def clear_cache(self):
		from hrms.payroll.doctype.salary_slip.salary_slip import (
			SALARY_COMPONENT_VALUES,
			TAX_COMPONENTS_BY_COMPANY,
		)

		frappe.cache().delete_value(SALARY_COMPONENT_VALUES)
		frappe.cache().delete_value(TAX_COMPONENTS_BY_COMPANY)
		return super().clear_cache()

	def validate_abbr(self):
		if not self.salary_component_abbr:
			self.salary_component_abbr = "".join([c[0] for c in self.salary_component.split()]).upper()

		self.salary_component_abbr = self.salary_component_abbr.strip()
		self.salary_component_abbr = append_number_if_name_exists(
			"Salary Component",
			self.salary_component_abbr,
			"salary_component_abbr",
			separator="_",
			filters={"name": ["!=", self.name]},
		)

	def validate_accounts(self):
		if not (self.statistical_component or (self.accounts and all(d.account for d in self.accounts))):
			frappe.msgprint(
				title=_("Warning"),
				msg=_("Accounts not set for Salary Component {0}").format(self.name),
				indicator="orange",
			)

	def validate_accrual_component(self):
		if self.type != "Earning" and self.accrual_component:
			frappe.throw(
				_("Accrual Component can only be set for Earning Salary Components."),
				title=_("Invalid Accrual Component"),
			)

		if self.is_flexible_benefit:
			requires_accrual = self.payout_method in [
				"Accrue and payout at end of payroll period",
				"Accrue per cycle, pay only on claim",
			]

			if requires_accrual and not self.accrual_component:
				frappe.throw(
					_(
						"Accrual Component must be set for Flexible Benefit Salary Components with accrual payout methods."
					),
					title=_("Invalid Accrual Component"),
				)

			if not requires_accrual and self.accrual_component:
				frappe.throw(
					_(
						"Accrual Component can only be set for Flexible Benefit Salary Components with accrual payout methods."
					),
					title=_("Invalid Accrual Component"),
				)

	def valide_arrear_component(self):
		if self.variable_based_on_taxable_salary and self.arrear_component:
			frappe.throw(
				_("Arrear Component cannot be set for Salary Components based on taxable salary."),
				title=_("Invalid Arrear Component"),
			)

	@frappe.whitelist()
	def get_structures_to_be_updated(self):
		SalaryStructure = frappe.qb.DocType("Salary Structure")
		SalaryDetail = frappe.qb.DocType("Salary Detail")
		return (
			frappe.qb.from_(SalaryStructure)
			.inner_join(SalaryDetail)
			.on(SalaryStructure.name == SalaryDetail.parent)
			.select(SalaryStructure.name)
			.where((SalaryDetail.salary_component == self.name) & (SalaryStructure.docstatus != 2))
			.run(pluck=True)
		)

	@frappe.whitelist()
	def update_salary_structures(self, field, value, structures=None):
		is_formula_related = field == "formula"

		if not structures:
			structures = self.get_structures_to_be_updated()

		for structure in structures:
			salary_structure = frappe.get_doc("Salary Structure", structure)
			# this is only used for versioning and we do not want
			# to make separate db calls by using load_doc_before_save
			# which proves to be expensive while doing bulk replace
			salary_structure._doc_before_save = copy.deepcopy(salary_structure)

			salary_detail_row = next(
				(
					d
					for d in salary_structure.get(f"{self.type.lower()}s")
					if d.salary_component == self.name
				),
				None,
			)
			if not salary_detail_row:
				continue

			if is_formula_related:
				value = value if self.amount_based_on_formula else None
				salary_detail_row.set("amount_based_on_formula", self.amount_based_on_formula)

			salary_detail_row.set(field, value)
			salary_structure.db_update_all()
			# db_update_all() does not invalidate the cached Salary Structure,
			# so clear the cache so new Salary Slips pick up the changes immediately.
			salary_structure.clear_cache()
			salary_structure.flags.updater_reference = {
				"doctype": self.doctype,
				"docname": self.name,
				"label": _("via Salary Component sync"),
			}
