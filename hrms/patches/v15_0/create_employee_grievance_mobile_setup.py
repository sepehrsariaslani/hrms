from hrms.api import (
	ensure_employee_grievance_workflow,
	ensure_iran_grievance_types,
	sync_employee_grievance_reports_to,
)


def execute():
	ensure_iran_grievance_types()
	ensure_employee_grievance_workflow()
	sync_employee_grievance_reports_to()
