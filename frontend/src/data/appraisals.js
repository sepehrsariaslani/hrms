import { createResource } from "frappe-ui"
import { employeeResource } from "./employee"
import { watch } from "vue"

import { formatJalaliDateShort } from "@/utils/jalali"

const DOCSTATUS_LABELS = {
	0: "Draft",
	1: "Submitted",
	2: "Cancelled",
}

export const transformAppraisalData = (data = []) =>
	data.map((appraisal) => {
		const normalized = { ...appraisal }
		normalized.doctype = "Appraisal"
		normalized.status =
			normalized.status || DOCSTATUS_LABELS[Number(normalized.docstatus)] || "Draft"
		normalized.appraisal_dates = getAppraisalDates(normalized)
		normalized.formatted_final_score = formatScore(normalized.final_score)
		return normalized
	})

export const getAppraisalDates = (appraisal) => {
	const startDate = appraisal.start_date ? formatJalaliDateShort(appraisal.start_date) : "-"
	const endDate = appraisal.end_date ? formatJalaliDateShort(appraisal.end_date) : "-"

	if (startDate === "-" && endDate === "-") return "-"
	return startDate === endDate ? startDate : `${startDate} - ${endDate}`
}

export const formatScore = (value) => {
	if (value === null || value === undefined || value === "") return "-"
	const score = Number(value)
	if (!Number.isFinite(score)) return "-"
	return score.toFixed(2)
}

export const myAppraisals = createResource({
	url: "hrms.api.get_appraisals",
	auto: false,
	cache: "hrms:my_appraisals",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
			limit: 20,
		}
	},
	transform(data) {
		return transformAppraisalData(data)
	},
})

export const teamAppraisals = createResource({
	url: "hrms.api.get_appraisals",
	auto: false,
	cache: "hrms:team_appraisals",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
			for_approval: 1,
			limit: 20,
		}
	},
	transform(data) {
		return transformAppraisalData(data)
	},
})

watch(
	() => employeeResource.data?.name,
	(employeeName) => {
		if (!employeeName) return
		myAppraisals.reload()
		teamAppraisals.reload()
	},
	{ immediate: true }
)
