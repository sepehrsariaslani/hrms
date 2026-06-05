# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class CareerPathMap(Document):
	def validate(self):
		if self.auto_sync_stations:
			self.sync_stations_from_designations()

	def sync_stations_from_designations(self):
		station_by_designation = {row.designation: row for row in (self.stations or []) if row.designation}
		designations = frappe.get_all("Designation", pluck="name", order_by="name asc")

		self.stations = []
		for designation in designations:
			row = station_by_designation.get(designation) or frappe._dict()
			job_grade = frappe.db.get_value("Designation", designation, "job_grade")
			grade_level = flt(frappe.db.get_value("Job Grade", job_grade, "level_number")) if job_grade else 0

			self.append(
				"stations",
				{
					"designation": designation,
					"notes": row.get("notes"),
					"grade_level": grade_level,
				},
			)

