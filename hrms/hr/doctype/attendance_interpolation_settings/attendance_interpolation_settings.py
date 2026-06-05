import frappe
from frappe.model.document import Document


class AttendanceInterpolationSettings(Document):
    def validate(self):
        if not self.target_site:
            frappe.throw(frappe._("Target Site is required."))

        if not self.sql_host or not self.sql_port or not self.sql_database or not self.sql_user:
            frappe.throw(frappe._("SQL connection fields are required."))
