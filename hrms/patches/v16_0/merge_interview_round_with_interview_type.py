import frappe


def execute():
	InterviewType = frappe.qb.DocType("Interview Type")
	InterviewRound = frappe.qb.DocType("Interview Round")

	(
		frappe.qb.update(InterviewRound)
		.left_join(InterviewType)
		.on(InterviewType.name == InterviewRound.interview_type)
		.set(InterviewRound.description, InterviewType.description)
	).run()
