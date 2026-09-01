def execute():
	"""Install Salary Slip accounting fields on every existing site."""
	from hrms.regional.iran.setup import make_custom_fields

	make_custom_fields()
