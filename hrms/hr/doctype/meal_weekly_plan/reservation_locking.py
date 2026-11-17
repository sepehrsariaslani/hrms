"""Database write barriers for serializing meal reservation validation."""


def employee_day_write_barrier(employee):
	"""Return a no-op write that conflicts on one employee row."""
	return "update `tabEmployee` set name=name where name=%s", (employee,)


def plan_day_write_barrier(plan, meal_date):
	"""Return a no-op write that conflicts on one plan-day row."""
	return (
		"update `tabMeal Weekly Plan Item` set parent=parent where parent=%s and meal_date=%s",
		(plan, meal_date),
	)
