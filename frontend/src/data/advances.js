import { createResource } from "frappe-ui"
import { employeeResource } from "./employee"
import { watch } from "vue"

const transformAdvanceData = (data) => {
	return data.map((claim) => {
		claim.doctype = "Employee Advance"
		return claim
	})
}

export const advanceBalance = createResource({
	url: "hrms.api.get_employee_advance_balance",
	auto: false,
	cache: "hrms:employee_advance_balance",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
		}
	},
	transform(data) {
		return transformAdvanceData(data)
	},
})

watch(
	() => employeeResource.data?.name,
	(employeeName) => {
		if (!employeeName) return
		advanceBalance.reload()
	},
	{ immediate: true }
)
