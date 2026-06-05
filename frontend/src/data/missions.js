import { computed, watch } from "vue"
import { createResource, frappeRequest } from "frappe-ui"

import { employeeResource } from "@/data/employee"
import { formatGregorianDate } from "@/utils/jalali"

export const missionFlowTypeOptions = ["برنامه‌ریزی‌شده", "بدون برنامه‌ریزی"]
export const missionTypeOptions = ["روزانه", "ساعتی"]

export const missionStatusOptions = [
	"در انتظار تایید برنامه سفر",
	"تایید برنامه سفر",
	"در حال انجام سفر",
	"در انتظار تایید نهایی سرپرست",
	"نیازمند اصلاح",
	"تایید نهایی سرپرست",
	"ردشده",
]

function getToday() {
	return formatGregorianDate(new Date())
}

function normalizeAmount(value) {
	const parsed = Number(value || 0)
	return Number.isFinite(parsed) ? parsed : 0
}

function normalizeExpense(expense, index = 0) {
	return {
		id: expense?.id || `exp-${index + 1}`,
		date: expense?.date || getToday(),
		category: expense?.category || "",
		description: expense?.description || "",
		amount: normalizeAmount(expense?.amount),
		receipt_file: expense?.receipt_file || "",
		receipt_file_url: expense?.receipt_file_url || "",
	}
}

function normalizeMission(row) {
	const expenses = Array.isArray(row?.expenses)
		? row.expenses.map((expense, index) => normalizeExpense(expense, index))
		: []
	const totalExpense = expenses.reduce((total, entry) => total + normalizeAmount(entry.amount), 0)

	return {
		id: row?.id || row?.name || "",
		name: row?.name || row?.id || "",
		doctype: row?.doctype || "Travel Request",
		title: row?.title || "",
		destination: row?.destination || "",
		purpose: row?.purpose || "",
		notes: row?.notes || "",
		flow_type: row?.flow_type || missionFlowTypeOptions[1],
		mission_type: row?.mission_type || missionTypeOptions[0],
		start_date: row?.start_date || getToday(),
		end_date: row?.end_date || row?.start_date || getToday(),
		hourly_date: row?.hourly_date || "",
		hourly_from_time: row?.hourly_from_time || "",
		hourly_to_time: row?.hourly_to_time || "",
		status: row?.status || missionStatusOptions[2],
		mission_allowance: normalizeAmount(row?.mission_allowance),
		total_expense: normalizeAmount(row?.total_expense ?? totalExpense),
		expenses,
		employee: row?.employee || "",
		employee_name: row?.employee_name || "",
		supervisor_employee: row?.supervisor_employee || "",
		is_planned: Boolean(row?.is_planned ?? row?.flow_type === missionFlowTypeOptions[0]),
		can_review: Boolean(row?.can_review),
		linked_expense_claim: row?.linked_expense_claim || "",
		settlement_type: row?.settlement_type || "",
		settlement_amount: normalizeAmount(row?.settlement_amount),
		settlement_message: row?.settlement_message || "",
		created_at: row?.created_at || "",
		updated_at: row?.updated_at || "",
	}
}

export const travelExpenseTypes = createResource({
	url: "hrms.api.travel.get_travel_expense_types",
	auto: false,
	cache: "hrms:travel_expense_types",
	transform(rows) {
		if (!Array.isArray(rows)) return []
		return rows.map((row) => ({
			name: row?.name,
			label: row?.label || row?.name,
			description: row?.description || "",
			default_account: row?.default_account || "",
		}))
	},
})

export const myTravelRequests = createResource({
	url: "hrms.api.travel.get_travel_requests",
	auto: false,
	cache: "hrms:my_travel_requests",
	makeParams() {
		return {
			limit: 100,
			for_approval: 0,
		}
	},
	transform(rows) {
		if (!Array.isArray(rows)) return []
		return rows.map((row) => normalizeMission(row))
	},
})

export const teamTravelRequests = createResource({
	url: "hrms.api.travel.get_travel_requests",
	auto: false,
	cache: "hrms:team_travel_requests",
	makeParams() {
		return {
			limit: 100,
			for_approval: 1,
		}
	},
	transform(rows) {
		if (!Array.isArray(rows)) return []
		return rows.map((row) => normalizeMission(row))
	},
})

watch(
	() => employeeResource.data?.name,
	(employeeName) => {
		if (!employeeName) return
		travelExpenseTypes.reload()
		myTravelRequests.reload()
		teamTravelRequests.reload()
	},
	{ immediate: true }
)

export const myMissions = computed(() => myTravelRequests.data || [])
export const teamMissions = computed(() => teamTravelRequests.data || [])

export const allMissions = computed(() => {
	const byId = new Map()
	for (const row of [...teamMissions.value, ...myMissions.value]) {
		if (!row?.id) continue
		byId.set(row.id, row)
	}
	return Array.from(byId.values()).sort(
		(left, right) =>
			new Date(right.updated_at || right.start_date || 0).getTime() -
			new Date(left.updated_at || left.start_date || 0).getTime()
	)
})

export const activeMissions = computed(() =>
	myMissions.value.filter((mission) =>
		[
			"در انتظار تایید برنامه سفر",
			"تایید برنامه سفر",
			"در حال انجام سفر",
			"در انتظار تایید نهایی سرپرست",
			"نیازمند اصلاح",
		].includes(mission.status)
	)
)

export const missionTotals = computed(() => {
	return myMissions.value.reduce(
		(acc, mission) => {
			acc.totalExpense += normalizeAmount(mission.total_expense)
			acc.totalAllowance += normalizeAmount(mission.mission_allowance)
			acc.totalCount += 1
			if (
				[
					"در انتظار تایید برنامه سفر",
					"تایید برنامه سفر",
					"در حال انجام سفر",
					"در انتظار تایید نهایی سرپرست",
					"نیازمند اصلاح",
				].includes(mission.status)
			) {
				acc.activeCount += 1
			}
			return acc
		},
		{
			totalExpense: 0,
			totalAllowance: 0,
			totalCount: 0,
			activeCount: 0,
		}
	)
})

export const expenseTypeOptions = computed(() => {
	const rows = travelExpenseTypes.data || []
	return rows.map((row) => ({
		label: row.label,
		value: row.name,
		description: row.description,
		default_account: row.default_account,
	}))
})

export function buildMissionDraft(overrides = {}) {
	const employeeName = employeeResource.data?.employee_name || ""
	const employeeId = employeeResource.data?.name || ""
	const flowType = overrides?.flow_type || missionFlowTypeOptions[1]
	const initialStatus =
		overrides?.status ||
		(flowType === "برنامه‌ریزی‌شده" ? "در انتظار تایید برنامه سفر" : "در حال انجام سفر")

	return normalizeMission({
		id: "",
		name: "",
		title: "",
		destination: "",
		purpose: "",
		notes: "",
		flow_type: flowType,
		mission_type: missionTypeOptions[0],
		start_date: getToday(),
		end_date: getToday(),
		hourly_date: getToday(),
		hourly_from_time: "",
		hourly_to_time: "",
		status: initialStatus,
		mission_allowance: 0,
		total_expense: 0,
		expenses: [],
		employee: employeeId,
		employee_name: employeeName,
		...overrides,
	})
}

export function getMissionById(id) {
	const missionId = String(id || "")
	return allMissions.value.find((mission) => mission.id === missionId) || null
}

async function callTravelApi(method, params = {}) {
	const response = await frappeRequest({
		url: `/api/method/hrms.api.travel.${method}`,
		params,
	})
	return response?.message ?? response
}

export async function upsertMission(payload) {
	const data = await callTravelApi("upsert_travel_request", {
		payload: JSON.stringify(payload || {}),
	})
	await Promise.all([myTravelRequests.reload(), teamTravelRequests.reload()])
	return normalizeMission(data)
}

export async function applyMissionAction(name, action, payload = {}) {
	const data = await callTravelApi("apply_travel_action", {
		name,
		action,
		payload: JSON.stringify(payload || {}),
	})
	await Promise.all([myTravelRequests.reload(), teamTravelRequests.reload()])
	return normalizeMission(data)
}

export async function fetchMissionById(name) {
	const data = await callTravelApi("get_travel_request_detail", { name })
	return normalizeMission(data)
}

export async function attachMissionExpenseImage(name, expenseId, fileName, fileContent) {
	const data = await callTravelApi("attach_travel_expense_image", {
		name,
		expense_id: expenseId,
		file_name: fileName,
		file_content: fileContent,
	})
	await Promise.all([myTravelRequests.reload(), teamTravelRequests.reload()])
	return data
}

export function calculateMissionSettlement(allowance, totalExpense, status) {
	if (status !== "تایید نهایی سرپرست") {
		return {
			type: "",
			amount: 0,
			message: "",
		}
	}

	const diff = normalizeAmount(totalExpense) - normalizeAmount(allowance)
	if (diff > 0) {
		return {
			type: "company_debt",
			amount: diff,
			message: "شرکت بابت این ماموریت به کارمند بدهکار است.",
		}
	}
	if (diff < 0) {
		return {
			type: "employee_debt",
			amount: Math.abs(diff),
			message: "کارمند بابت این ماموریت به شرکت بدهکار است.",
		}
	}
	return {
		type: "balanced",
		amount: 0,
		message: "هزینه ماموریت با مبلغ دریافتی برابر است.",
	}
}
