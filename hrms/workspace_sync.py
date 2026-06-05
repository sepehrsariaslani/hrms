import json

import frappe


ROOT_WORKSPACE_CANDIDATES = ("Human Resources", "HR", "HR Setup")


def dt(link_to, label=None):
	return {"link_type": "DocType", "link_to": link_to, "label": label or link_to}


def rp(link_to, label=None):
	return {"link_type": "Report", "link_to": link_to, "label": label or link_to}


HUMAN_RESOURCES_LAYOUT = {
	"cards": [
		{
			"label": "Core HR / اطلاعات پایه",
			"links": [
				dt("Employee"),
				dt("Employment Type"),
				dt("Employee Grade"),
				dt("Job Grade"),
				dt("Job Family"),
				dt("Job Family Grade"),
				dt("Designation"),
				dt("Designation Responsibility"),
				dt("Designation KPI"),
				dt("Designation Soft Skill"),
				dt("Designation Working Condition"),
				dt("Designation Direct Report"),
				dt("Department Approver"),
				dt("Identification Document Type"),
			],
		},
		{
			"label": "Employee Lifecycle / چرخه کارمند",
			"links": [
				dt("Employee Designation Assignment"),
				dt("Employee Transfer"),
				dt("Employee Promotion"),
				dt("Employee Property History"),
				dt("Employee Health Insurance"),
				dt("Employee Onboarding"),
				dt("Employee Separation"),
				dt("Exit Interview"),
				dt("Full and Final Statement"),
				dt("Employee Grievance"),
			],
		},
		{
			"label": "Time, Attendance & Shifts",
			"links": [
				dt("Attendance"),
				dt("Attendance Request"),
				dt("Employee Checkin"),
				dt("Employee Attendance Tool"),
				dt("Upload Attendance"),
				dt("Shift Type"),
				dt("Shift Assignment"),
				dt("Shift Request"),
				dt("Break Hours"),
				dt("Break Assignment"),
			],
		},
		{
			"label": "Leave Management",
			"links": [
				dt("Leave Type"),
				dt("Leave Policy"),
				dt("Leave Period"),
				dt("Leave Application"),
				dt("Leave Allocation"),
				dt("Leave Policy Assignment"),
				dt("Leave Control Panel"),
				dt("Leave Encashment"),
				dt("Compensatory Leave Request"),
			],
		},
		{
			"label": "Performance, Talent & Learning",
			"links": [
				dt("Appraisal"),
				dt("Appraisal Cycle"),
				dt("Appraisal Template"),
				dt("Goal"),
				dt("KRA"),
				dt("Competency"),
				dt("Competency Assessment"),
				dt("Nine Box Assessment"),
				dt("Individual Development Plan"),
				dt("Employee Skill Map"),
				dt("Training Program"),
				dt("Training Event"),
			],
		},
		{
			"label": "Reports / Attendance",
			"links": [
				rp("Smart Attendance Report", "گزارش حضور و غیاب هوشمند"),
				rp("Monthly Attendance Sheet"),
				rp("Shift Attendance"),
				rp("Leave Ledger"),
				rp("Employee Overtime"),
				rp("Employee Time"),
				rp("Employee Time Per Month"),
				rp("چک کردن ورود و خروج کارمندان"),
				rp("کل ساعات کاری کارمندان"),
			],
		},
		{
			"label": "Reports / HR & Finance",
			"links": [
				rp("Employee Analytics"),
				rp("Recruitment Analytics"),
				rp("Appraisal Overview"),
				rp("Employee Leave Balance"),
				rp("Employee Leave Balance Summary"),
				rp("Employee Advance Summary"),
				rp("Unpaid Expense Claim"),
				rp("Vehicle Expenses"),
				rp("مانده حساب کارمندان"),
				rp("میانگین حقوق ساعتی کارمند"),
			],
		},
		{
			"label": "Settings & Master Data",
			"links": [
				dt("Company"),
				dt("Branch"),
				dt("Department"),
				dt("HR Settings"),
				dt("Payroll Settings"),
				dt("Attendance Device"),
				dt("Employee Attendance Device Mapping"),
				dt("Holiday List Assignment"),
				dt("Daily Work Summary Group"),
			],
		},
	],
	"shortcuts": [
		("Employee", "Employee"),
		("Smart Attendance", "Employee Checkin"),
		("Leave Application", "Leave Application"),
		("Appraisal", "Appraisal"),
	],
	"other_card_label": "Other Items",
}


SHIFT_ATTENDANCE_LAYOUT = {
	"cards": [
		{
			"label": "Attendance Operations",
			"links": [
				dt("Attendance"),
				dt("Attendance Request"),
				dt("Employee Checkin"),
				dt("Employee Attendance Tool"),
				dt("Upload Attendance"),
				dt("Employee Times"),
			],
		},
		{
			"label": "Shift & Scheduling",
			"links": [
				dt("Shift Type"),
				dt("Shift Location"),
				dt("Shift Assignment"),
				dt("Shift Assignment Tool"),
				dt("Shift Schedule"),
				dt("Shift Schedule Assignment"),
				dt("Shift Request"),
			],
		},
		{
			"label": "Break Management",
			"links": [
				dt("Break Hours"),
				dt("Break Assignment"),
			],
		},
		{
			"label": "Weekly Shift Planning",
			"links": [
				dt("Weekly Shift Planner Settings"),
				dt("Weekly Shift Plan"),
				dt("Weekly Shift Plan Slot"),
				dt("Weekly Shift Finalization"),
				dt("Weekly Shift Finalization Slot"),
				dt("Shift Duty Role"),
				dt("Employee Shift Duty Role"),
			],
		},
		{
			"label": "Overtime",
			"links": [
				dt("Overtime Type"),
				dt("Overtime Slip"),
				dt("Overtime Details"),
				dt("Overtime Salary Component"),
			],
		},
		{
			"label": "Attendance Reports",
			"links": [
				rp("Smart Attendance Report", "گزارش حضور و غیاب هوشمند"),
				rp("Monthly Attendance Sheet"),
				rp("Shift Attendance"),
				rp("Employee Overtime"),
				rp("Employee Time"),
				rp("Employee Time Per Month"),
				rp("چک کردن ورود و خروج کارمندان"),
				rp("کل ساعات کاری کارمندان"),
				rp("Project Profitability"),
				rp("Employee Hours Utilization Based On Timesheet"),
			],
		},
	],
	"shortcuts": [
		("Employee Checkin", "Employee Checkin"),
		("Shift Assignment", "Shift Assignment"),
		("Break Assignment", "Break Assignment"),
	],
	"other_card_label": "Other Shift Items",
}


LEAVES_LAYOUT = {
	"cards": [
		{
			"label": "Leave Setup",
			"links": [
				dt("Holiday List"),
				dt("Holiday List Assignment"),
				dt("Leave Type"),
				dt("Leave Period"),
				dt("Leave Policy"),
				dt("Leave Block List"),
				dt("Leave Block List Date"),
				dt("Leave Block List Allow"),
			],
		},
		{
			"label": "Leave Transactions",
			"links": [
				dt("Leave Application"),
				dt("Leave Allocation"),
				dt("Leave Policy Assignment"),
				dt("Leave Adjustment"),
				dt("Leave Encashment"),
				dt("Compensatory Leave Request"),
			],
		},
		{
			"label": "Leave Control",
			"links": [
				dt("Leave Control Panel"),
				dt("Leave Ledger Entry"),
			],
		},
		{
			"label": "Leave Reports",
			"links": [
				rp("Employee Leave Balance"),
				rp("Employee Leave Balance Summary"),
				rp("Leave Ledger"),
				rp("Employees working on a holiday"),
			],
		},
	],
	"shortcuts": [
		("Leave Application", "Leave Application"),
		("Leave Allocation", "Leave Allocation"),
	],
	"other_card_label": "Other Leave Items",
}


RECRUITMENT_LAYOUT = {
	"cards": [
		{
			"label": "Planning & Job Setup",
			"links": [
				dt("Staffing Plan"),
				dt("Staffing Plan Detail"),
				dt("Job Requisition"),
				dt("Job Opening"),
				dt("Job Opening Template"),
			],
		},
		{
			"label": "Applicants",
			"links": [
				dt("Job Applicant"),
				dt("Job Applicant Source"),
				dt("Employee Referral"),
			],
		},
		{
			"label": "Interview & Offer",
			"links": [
				dt("Interview Type"),
				dt("Interview Round"),
				dt("Interview"),
				dt("Interview Detail"),
				dt("Interviewer"),
				dt("Interview Feedback"),
				dt("Job Offer"),
				dt("Job Offer Term Template"),
				dt("Job Offer Term"),
				dt("Offer Term"),
				dt("Appointment Letter"),
				dt("Appointment Letter Template"),
				dt("Appointment Letter Content"),
			],
		},
		{
			"label": "Recruitment Reports",
			"links": [
				rp("Recruitment Analytics"),
			],
		},
	],
	"shortcuts": [
		("Job Opening", "Job Opening"),
		("Job Applicant", "Job Applicant"),
		("Interview", "Interview"),
	],
	"other_card_label": "Other Recruitment Items",
}


PERFORMANCE_LAYOUT = {
	"cards": [
		{
			"label": "Appraisal & Goals",
			"links": [
				dt("Appraisal"),
				dt("Appraisal Cycle"),
				dt("Appraisal Template"),
				dt("Appraisal Goal"),
				dt("Appraisal Template Goal"),
				dt("Goal"),
				dt("KRA"),
				dt("Appraisal KRA"),
				dt("Appraisee"),
			],
		},
		{
			"label": "Competency & Nine Box",
			"links": [
				dt("Competency"),
				dt("Competency Requirement"),
				dt("Competency Behavioral Indicator"),
				dt("Competency Assessment"),
				dt("Competency Assessment Item"),
				dt("Nine Box Cycle"),
				dt("Nine Box Assessment"),
			],
		},
		{
			"label": "Growth & Feedback",
			"links": [
				dt("Employee Promotion"),
				dt("Employee Performance Feedback"),
				dt("Employee Feedback Criteria"),
				dt("Employee Feedback Rating"),
				dt("Individual Development Plan"),
				dt("Career Path Map"),
			],
		},
		{
			"label": "Performance Reports",
			"links": [
				rp("Appraisal Overview"),
			],
		},
	],
	"shortcuts": [
		("Appraisal", "Appraisal"),
		("Goal", "Goal"),
		("Competency Assessment", "Competency Assessment"),
	],
	"other_card_label": "Other Performance Items",
}


TENURE_LAYOUT = {
	"cards": [
		{
			"label": "Onboarding, Movement & Exit",
			"links": [
				dt("Employee Onboarding"),
				dt("Employee Onboarding Template"),
				dt("Employee Boarding Activity"),
				dt("Employee Separation"),
				dt("Employee Separation Template"),
				dt("Exit Interview"),
				dt("Full and Final Statement"),
			],
		},
		{
			"label": "Learning & Development",
			"links": [
				dt("Training Program"),
				dt("Training Event"),
				dt("Training Event Employee"),
				dt("Training Result"),
				dt("Training Result Employee"),
				dt("Training Feedback"),
				dt("Employee Training"),
				dt("Employee Skill Map"),
			],
		},
		{
			"label": "Engagement & Daily Ops",
			"links": [
				dt("Employee Grievance"),
				dt("Grievance Type"),
				dt("Daily Work Summary"),
				dt("Daily Work Summary Group"),
				dt("Daily Work Summary Group User"),
			],
		},
		{
			"label": "Tenure Reports",
			"links": [
				rp("Employee Exits"),
				rp("Employee Analytics"),
				rp("Employee Birthday"),
				rp("Employee Information"),
				rp("Daily Work Summary Replies"),
			],
		},
	],
	"shortcuts": [
		("Employee Onboarding", "Employee Onboarding"),
		("Employee Separation", "Employee Separation"),
	],
	"other_card_label": "Other Tenure Items",
}


EXPENSES_LAYOUT = {
	"cards": [
		{
			"label": "Employee Finance",
			"links": [
				dt("Expense Claim"),
				dt("Expense Claim Type"),
				dt("Employee Advance"),
				dt("Employee Imprest Account"),
				dt("Additional Salary"),
			],
		},
		{
			"label": "Travel & Logistics",
			"links": [
				dt("Travel Request"),
				dt("Travel Request Costing"),
				dt("Travel Itinerary"),
				dt("Purpose of Travel"),
			],
		},
		{
			"label": "Fleet & Operations",
			"links": [
				dt("Vehicle"),
				dt("Vehicle Service"),
				dt("Vehicle Service Item"),
				dt("Vehicle Log"),
			],
		},
		{
			"label": "Accounting Entries",
			"links": [
				dt("Payment Entry"),
				dt("Journal Entry"),
			],
		},
		{
			"label": "Expense Reports",
			"links": [
				rp("Unpaid Expense Claim"),
				rp("Vehicle Expenses"),
				rp("Employee Advance Summary"),
				rp("Accounts Receivable"),
				rp("Accounts Payable"),
				rp("General Ledger"),
				rp("مانده حساب کارمندان"),
			],
		},
	],
	"shortcuts": [
		("Expense Claim", "Expense Claim"),
		("Employee Advance", "Employee Advance"),
	],
	"other_card_label": "Other Expense Items",
}


WORKSPACE_LAYOUTS = {
	"Shift & Attendance": SHIFT_ATTENDANCE_LAYOUT,
	"Leaves": LEAVES_LAYOUT,
	"Recruitment": RECRUITMENT_LAYOUT,
	"Performance": PERFORMANCE_LAYOUT,
	"Tenure": TENURE_LAYOUT,
	"Expenses": EXPENSES_LAYOUT,
}


def sync_hr_workspace_setup():
	for workspace_name in ROOT_WORKSPACE_CANDIDATES:
		if frappe.db.exists("Workspace", workspace_name):
			apply_workspace_layout(workspace_name, HUMAN_RESOURCES_LAYOUT)

	for workspace_name, layout in WORKSPACE_LAYOUTS.items():
		if frappe.db.exists("Workspace", workspace_name):
			apply_workspace_layout(workspace_name, layout)


def apply_workspace_layout(workspace_name, layout):
	workspace = frappe.get_doc("Workspace", workspace_name)
	updated = False

	if sync_workspace_links_layout(
		workspace,
		layout.get("cards", []),
		other_card_label=layout.get("other_card_label", "Other"),
	):
		updated = True

	if reorder_workspace_content(workspace):
		updated = True

	shortcuts = layout.get("shortcuts", [])
	if ensure_workspace_shortcuts(workspace, shortcuts):
		updated = True
	if ensure_content_shortcuts(workspace, [label for label, _ in shortcuts]):
		updated = True

	if updated:
		workspace.flags.ignore_links = True
		workspace.save(ignore_permissions=True)


def sync_workspace_links_layout(workspace, card_defs, other_card_label="Other"):
	existing_links = collect_existing_link_rows(workspace)
	new_rows = []
	used_keys = set()

	for card in card_defs:
		card_label = card.get("label")
		card_links = []
		seen_in_card = set()

		for item in card.get("links", []):
			link_type = item.get("link_type")
			link_to = item.get("link_to")
			key = (link_type, link_to)
			if not link_type or not link_to or key in seen_in_card:
				continue
			seen_in_card.add(key)

			row = pop_existing_link_row(existing_links, key)
			if row is None and not link_target_exists(link_type, link_to):
				continue

			if row is None:
				row = make_link_row(item)
			else:
				row["label"] = item.get("label") or row.get("label") or link_to
				row["link_type"] = link_type
				row["link_to"] = link_to
				row["type"] = "Link"
				if link_type == "Report" and "is_query_report" not in row:
					row["is_query_report"] = get_report_query_flag(link_to)

			card_links.append(row)
			used_keys.add(key)

		if card_links:
			new_rows.append(make_card_break_row(card_label, len(card_links)))
			new_rows.extend(card_links)

	leftovers = []
	for key, rows in existing_links.items():
		if key in used_keys:
			continue
		leftovers.extend(rows)

	if leftovers:
		leftovers.sort(key=lambda row: ((row.get("label") or "").lower(), row.get("link_to") or ""))
		new_rows.append(make_card_break_row(other_card_label, len(leftovers)))
		new_rows.extend(leftovers)

	old_signature = get_workspace_link_signature(workspace.get("links") or [])
	new_signature = get_workspace_link_signature(new_rows)
	if old_signature == new_signature:
		return False

	workspace.set("links", [])
	for row in new_rows:
		workspace.append("links", row)

	return True


def collect_existing_link_rows(workspace):
	rows_map = {}
	for row in workspace.get("links") or []:
		if row.type != "Link":
			continue
		key = (row.get("link_type"), row.get("link_to"))
		rows_map.setdefault(key, []).append(clean_workspace_row(row))
	return rows_map


def clean_workspace_row(row):
	d = row.as_dict() if hasattr(row, "as_dict") else dict(row)
	for meta_key in (
		"name",
		"owner",
		"creation",
		"modified",
		"modified_by",
		"parent",
		"parentfield",
		"parenttype",
		"idx",
		"docstatus",
		"doctype",
	):
		d.pop(meta_key, None)

	out = {}
	for key in (
		"type",
		"label",
		"link_type",
		"link_to",
		"is_query_report",
		"dependencies",
		"hidden",
		"onboard",
	):
		value = d.get(key)
		if value in (None, ""):
			continue
		out[key] = value

	out.setdefault("type", "Link")
	return out


def pop_existing_link_row(rows_map, key):
	rows = rows_map.get(key)
	if not rows:
		return None
	return rows.pop(0)


def link_target_exists(link_type, link_to):
	if link_type == "DocType":
		return bool(frappe.db.exists("DocType", link_to))
	if link_type == "Report":
		return bool(frappe.db.exists("Report", link_to))
	return True


def make_link_row(item):
	link_type = item.get("link_type")
	link_to = item.get("link_to")
	row = {
		"type": "Link",
		"label": item.get("label") or link_to,
		"link_type": link_type,
		"link_to": link_to,
		"hidden": 0,
		"onboard": 0,
	}
	if link_type == "Report":
		row["is_query_report"] = get_report_query_flag(link_to)
	return row


def make_card_break_row(label, link_count):
	return {
		"type": "Card Break",
		"label": label,
		"link_count": link_count,
		"hidden": 0,
		"onboard": 0,
	}


def get_report_query_flag(report_name):
	report_type = frappe.db.get_value("Report", report_name, "report_type")
	return 1 if report_type == "Query Report" else 0


def get_workspace_link_signature(rows):
	signature = []
	for row in rows:
		if hasattr(row, "as_dict"):
			data = row.as_dict()
		else:
			data = dict(row)

		type_value = data.get("type")
		if type_value == "Card Break":
			signature.append(("Card Break", data.get("label"), int(data.get("link_count") or 0)))
		elif type_value == "Link":
			signature.append(
				(
					"Link",
					data.get("label"),
					data.get("link_type"),
					data.get("link_to"),
					int(data.get("is_query_report") or 0),
				)
			)
	return signature


def reorder_workspace_content(workspace):
	content = parse_workspace_content(workspace.content)
	if not content:
		return False

	card_names = [
		row.label
		for row in (workspace.get("links") or [])
		if row.type == "Card Break" and row.label
	]
	if not card_names:
		return False

	card_blocks = [block for block in content if block.get("type") == "card"]
	if not card_blocks:
		return False

	existing_by_name = {}
	for block in card_blocks:
		card_name = (block.get("data") or {}).get("card_name")
		if card_name:
			existing_by_name[card_name] = block

	ordered_blocks = []
	for card_name in card_names:
		block = existing_by_name.get(card_name)
		if block is None:
			block = {"type": "card", "data": {"card_name": card_name, "col": 4}}
		ordered_blocks.append(block)

	start = next((idx for idx, block in enumerate(content) if block.get("type") == "card"), None)
	end = next((idx for idx in range(len(content) - 1, -1, -1) if content[idx].get("type") == "card"), None)
	if start is None or end is None:
		return False

	prefix = [block for block in content[:start] if block.get("type") != "card"]
	suffix = [block for block in content[end + 1 :] if block.get("type") != "card"]
	new_content = prefix + ordered_blocks + suffix

	if json.dumps(new_content, sort_keys=True, ensure_ascii=False) == json.dumps(
		content, sort_keys=True, ensure_ascii=False
	):
		return False

	workspace.content = json.dumps(new_content, ensure_ascii=False)
	return True


def ensure_workspace_shortcuts(workspace, shortcuts):
	updated = False
	rows = workspace.get("shortcuts") or []

	for label, link_to in shortcuts:
		if not frappe.db.exists("DocType", link_to):
			continue

		existing = next((row for row in rows if row.type == "DocType" and row.link_to == link_to), None)
		if existing:
			if existing.label != label:
				existing.label = label
				updated = True
			continue

		workspace.append(
			"shortcuts",
			{
				"type": "DocType",
				"label": label,
				"link_to": link_to,
				"doc_view": "List",
				"color": "Grey",
			},
		)
		rows = workspace.get("shortcuts") or []
		updated = True

	return updated


def ensure_content_shortcuts(workspace, shortcut_labels):
	if not shortcut_labels:
		return False

	content = parse_workspace_content(workspace.content)
	updated = False
	spacer_index = next((idx for idx, block in enumerate(content) if block.get("type") == "spacer"), len(content))

	for label in shortcut_labels:
		exists = any(
			block.get("type") == "shortcut" and (block.get("data") or {}).get("shortcut_name") == label
			for block in content
		)
		if exists:
			continue

		content.insert(spacer_index, {"type": "shortcut", "data": {"shortcut_name": label, "col": 3}})
		spacer_index += 1
		updated = True

	if updated:
		workspace.content = json.dumps(content, ensure_ascii=False)

	return updated


def parse_workspace_content(raw_content):
	if not raw_content:
		return []
	if isinstance(raw_content, list):
		return raw_content
	try:
		parsed = json.loads(raw_content)
	except Exception:
		return []
	return parsed if isinstance(parsed, list) else []
