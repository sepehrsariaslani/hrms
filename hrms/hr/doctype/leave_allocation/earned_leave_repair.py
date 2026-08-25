from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate


def repair_earned_leave_allocations(
	leave_type_name: str,
	as_of_date: str | None = None,
	dry_run: bool = True,
) -> list[dict]:
	"""Repair earned leave allocations for one leave type on the current site.

	This is intended for fixing sites where earned leave was granted upfront
	instead of accruing per passed period.
	"""
	target_date = getdate(as_of_date) if as_of_date else getdate()
	previous_date = getattr(frappe.flags, "current_date", None)
	frappe.flags.current_date = target_date

	try:
		leave_type = frappe.get_doc("Leave Type", leave_type_name)
		if not leave_type.is_earned_leave:
			frappe.throw(_("Leave Type {0} is not configured as earned leave").format(leave_type_name))

		annual_cap = sync_max_leaves_allowed_with_policy(leave_type_name, dry_run=dry_run)
		allocation_names = frappe.get_all(
			"Leave Allocation",
			filters={
				"leave_type": leave_type_name,
				"docstatus": 1,
				"leave_policy_assignment": ("is", "set"),
				"leave_policy": ("is", "set"),
			},
			order_by="creation asc",
			pluck="name",
		)

		results = []
		for allocation_name in allocation_names:
			snapshot = get_repaired_allocation_snapshot(allocation_name, target_date)
			snapshot["annual_cap"] = annual_cap
			results.append(snapshot)
			if not dry_run:
				apply_repaired_snapshot(snapshot)

		if not dry_run:
			frappe.db.commit()

		return results
	finally:
		if previous_date is None:
			try:
				del frappe.flags.current_date
			except AttributeError:
				pass
		else:
			frappe.flags.current_date = previous_date


def sync_max_leaves_allowed_with_policy(leave_type_name: str, dry_run: bool = True) -> float:
	annual_allocations = frappe.get_all(
		"Leave Policy Detail",
		filters={"leave_type": leave_type_name},
		pluck="annual_allocation",
	)
	annual_cap = max((flt(value) for value in annual_allocations), default=0.0)
	if annual_cap and not dry_run:
		frappe.db.set_value("Leave Type", leave_type_name, "max_leaves_allowed", annual_cap)
	return annual_cap


def get_repaired_allocation_snapshot(allocation_name: str, as_of_date=None) -> dict:
	target_date = getdate(as_of_date) if as_of_date else getdate()
	allocation = frappe.get_doc("Leave Allocation", allocation_name)
	assignment = frappe.get_doc("Leave Policy Assignment", allocation.leave_policy_assignment)
	leave_type = frappe.get_doc("Leave Type", allocation.leave_type)
	date_of_joining = frappe.db.get_value("Employee", allocation.employee, "date_of_joining")
	annual_allocation = flt(
		frappe.db.get_value(
			"Leave Policy Detail",
			{"parent": allocation.leave_policy, "leave_type": allocation.leave_type},
			"annual_allocation",
		)
	)
	new_leaves_allocated = flt(
		assignment.get_new_leaves(annual_allocation, leave_type, date_of_joining),
		allocation.precision("new_leaves_allocated"),
	)
	earned_leave_schedule = assignment.get_earned_leave_schedule(
		annual_allocation, leave_type, date_of_joining, new_leaves_allocated
	)

	used_leaves = abs(
		frappe.db.sql(
			"""
			SELECT COALESCE(SUM(leaves), 0)
			FROM `tabLeave Ledger Entry`
			WHERE employee=%s
			  AND leave_type=%s
			  AND transaction_type='Leave Application'
			  AND docstatus=1
			  AND is_expired=0
			""",
			(allocation.employee, allocation.leave_type),
		)[0][0]
	)
	used_leaves = flt(used_leaves, allocation.precision("total_leaves_allocated"))
	ledger_names = frappe.get_all(
		"Leave Ledger Entry",
		filters={
			"transaction_type": "Leave Allocation",
			"transaction_name": allocation.name,
			"is_carry_forward": 0,
			"is_expired": 0,
			"docstatus": 1,
		},
		order_by="creation asc",
		pluck="name",
	)
	if len(ledger_names) != 1:
		frappe.throw(
			_("Expected exactly one active Leave Allocation ledger entry for {0}, found {1}").format(
				allocation.name, len(ledger_names)
			)
		)

	rounded_schedule = []
	for row in earned_leave_schedule:
		rounded_schedule.append(
			{
				"allocation_date": row["allocation_date"],
				"number_of_leaves": flt(row["number_of_leaves"], allocation.precision("new_leaves_allocated")),
				"attempted": row.get("attempted", 0),
				"failed": row.get("failed", 0),
				"is_allocated": row.get("is_allocated", 0),
				"allocated_via": row.get("allocated_via"),
				"failure_reason": row.get("failure_reason", ""),
			}
		)

	return {
		"allocation_name": allocation.name,
		"employee": allocation.employee,
		"employee_name": allocation.employee_name,
		"date_of_joining": date_of_joining,
		"as_of_date": target_date,
		"new_leaves_allocated": new_leaves_allocated,
		"total_leaves_allocated": new_leaves_allocated,
		"expected_balance": flt(new_leaves_allocated - used_leaves, allocation.precision("total_leaves_allocated")),
		"used_leaves": used_leaves,
		"ledger_name": ledger_names[0],
		"schedule": rounded_schedule,
	}


def apply_repaired_snapshot(snapshot: dict) -> None:
	frappe.db.set_value(
		"Leave Allocation",
		snapshot["allocation_name"],
		{
			"new_leaves_allocated": snapshot["new_leaves_allocated"],
			"total_leaves_allocated": snapshot["total_leaves_allocated"],
			"unused_leaves": 0,
			"carry_forwarded_leaves_count": 0,
		},
		update_modified=False,
	)
	frappe.db.set_value(
		"Leave Ledger Entry",
		snapshot["ledger_name"],
		{
			"leaves": snapshot["new_leaves_allocated"],
		},
		update_modified=False,
	)
	frappe.db.delete("Earned Leave Schedule", {"parent": snapshot["allocation_name"]})
	for idx, row in enumerate(snapshot["schedule"], start=1):
		child = frappe.get_doc(
			{
				"doctype": "Earned Leave Schedule",
				"parent": snapshot["allocation_name"],
				"parentfield": "earned_leave_schedule",
				"parenttype": "Leave Allocation",
				"idx": idx,
				**row,
			}
		)
		child.db_insert()
