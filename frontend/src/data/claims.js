import { createResource } from "frappe-ui"
import { employeeResource } from "./employee"
import { reactive } from "vue"
import { watch } from "vue"

export const expenseClaimSummary = createResource({
	url: "hrms.api.get_expense_claim_summary",
	auto: false,
	cache: "hrms:expense_claim_summary",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
		}
	},
})

const transformClaimData = (data) => {
	return data.map((claim) => {
		claim.doctype = "Expense Claim"
		return claim
	})
}

export const myClaims = createResource({
	url: "hrms.api.get_expense_claims",
	auto: false,
	cache: "hrms:my_claims",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
			limit: 10,
		}
	},
	transform(data) {
		return transformClaimData(data)
	},
	onSuccess() {
		expenseClaimSummary.reload()
	},
})

export const teamClaims = createResource({
	url: "hrms.api.get_expense_claims",
	auto: false,
	cache: "hrms:team_claims",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
			approver_id: employeeResource.data?.user_id,
			for_approval: 1,
			limit: 10,
		}
	},
	transform(data) {
		return transformClaimData(data)
	},
})

export let claimTypesByID = reactive({})

export const claimTypesResource = createResource({
	url: "hrms.api.get_expense_claim_types",
	auto: true,
	transform(data) {
		return data.map((row) => {
			claimTypesByID[row.name] = row
			return row
		})
	},
})

watch(
	() => employeeResource.data?.name,
	(employeeName) => {
		if (!employeeName) return
		expenseClaimSummary.reload()
		myClaims.reload()
		teamClaims.reload()
	},
	{ immediate: true }
)
