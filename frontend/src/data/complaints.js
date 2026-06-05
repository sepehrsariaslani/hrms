import { createResource } from "frappe-ui"
import { employeeResource } from "./employee"
import { watch } from "vue"

import { formatJalaliDateShort } from "@/utils/jalali"

const transformComplaintData = (data) =>
	data.map((complaint) => {
		complaint.doctype = "Employee Grievance"
		complaint.complaint_date = formatJalaliDateShort(complaint.date)
		return complaint
	})

export const myComplaints = createResource({
	url: "hrms.api.get_employee_grievances",
	auto: false,
	cache: "hrms:my_complaints",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
			limit: 10,
		}
	},
	transform(data) {
		return transformComplaintData(data)
	},
})

export const teamComplaints = createResource({
	url: "hrms.api.get_employee_grievances",
	auto: false,
	cache: "hrms:team_complaints",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
			for_approval: 1,
			limit: 10,
		}
	},
	transform(data) {
		return transformComplaintData(data)
	},
})

export const grievanceTypes = createResource({
	url: "hrms.api.get_grievance_types",
	auto: true,
	cache: "hrms:grievance_types",
})

watch(
	() => employeeResource.data?.name,
	(employeeName) => {
		if (!employeeName) return
		myComplaints.reload()
		teamComplaints.reload()
	},
	{ immediate: true }
)
