<template>
	<BaseLayout :pageTitle="__('درخواست‌ها')">
		<template #body>
			<div class="mx-auto mt-6 mb-8 w-full max-w-7xl px-4">
				<div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5">
					<div class="flex flex-wrap items-center justify-between gap-3">
						<div>
							<div class="text-lg font-bold text-slate-900">{{ __("مرکز درخواست‌ها") }}</div>
							<div class="mt-1 text-xs text-slate-500">
								{{ __("همه درخواست‌های منابع انسانی را با فیلترهای سریع مدیریت کنید.") }}
							</div>
						</div>
						<Button variant="outline" :loading="isLoading" @click="reloadAll">
							{{ __("بروزرسانی") }}
						</Button>
					</div>

					<div class="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
						<div class="rounded-xl border border-slate-200 bg-slate-50 p-3">
							<div class="text-xs font-semibold text-slate-500">{{ __("کل درخواست‌ها") }}</div>
							<div class="mt-1 text-2xl font-bold text-slate-900">
								{{ toPersianDigits(summary.total) }}
							</div>
						</div>
						<div class="rounded-xl border border-amber-200 bg-amber-50 p-3">
							<div class="text-xs font-semibold text-amber-700">{{ __("در انتظار") }}</div>
							<div class="mt-1 text-2xl font-bold text-amber-800">
								{{ toPersianDigits(summary.pending) }}
							</div>
						</div>
						<div class="rounded-xl border border-emerald-200 bg-emerald-50 p-3">
							<div class="text-xs font-semibold text-emerald-700">{{ __("تایید شده") }}</div>
							<div class="mt-1 text-2xl font-bold text-emerald-800">
								{{ toPersianDigits(summary.approved) }}
							</div>
						</div>
						<div class="rounded-xl border border-rose-200 bg-rose-50 p-3">
							<div class="text-xs font-semibold text-rose-700">{{ __("رد شده") }}</div>
							<div class="mt-1 text-2xl font-bold text-rose-800">
								{{ toPersianDigits(summary.rejected) }}
							</div>
						</div>
					</div>

					<div class="mt-4">
						<TabButtons :buttons="scopeButtons" v-model="activeScope" />
					</div>

						<div class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
							<div>
								<div class="mb-1 text-xs font-semibold text-slate-500">{{ __("نوع درخواست") }}</div>
								<SearchableDropdown
									v-model="selectedType"
									:options="typeDropdownOptions"
									:placeholder="__('انتخاب نوع درخواست')"
								/>
							</div>
							<div>
								<div class="mb-1 text-xs font-semibold text-slate-500">{{ __("وضعیت") }}</div>
								<SearchableDropdown
									v-model="selectedStatus"
									:options="statusDropdownOptions"
									:placeholder="__('انتخاب وضعیت')"
								/>
							</div>
							<div>
								<div class="mb-1 text-xs font-semibold text-slate-500">{{ __("گروه‌بندی") }}</div>
								<SearchableDropdown
									v-model="groupBy"
									:options="groupByOptions"
									:placeholder="__('گروه‌بندی')"
								/>
							</div>
						<div>
							<div class="mb-1 text-xs font-semibold text-slate-500">{{ __("جستجو") }}</div>
							<input
								v-model.trim="searchQuery"
								type="text"
								class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
								:placeholder="__('نام کارمند، موضوع، دلیل...')"
							/>
						</div>
					</div>

					<div class="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
						<div>
							{{ __("تعداد نتایج") }}:
							<span class="font-bold text-slate-700">{{ toPersianDigits(filteredRequests.length) }}</span>
						</div>
						<Button variant="ghost" @click="clearFilters">
							{{ __("پاک کردن فیلترها") }}
						</Button>
					</div>
				</div>

				<div v-if="isLoading" class="mt-4 rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
					{{ __("در حال بارگذاری درخواست‌ها...") }}
				</div>
				<RequestList
					v-else
					class="mt-4"
					:items="filteredRequests"
					:groupBy="groupBy"
					:emptyStateMessage="__('درخواستی با این فیلترها پیدا نشد.')"
				/>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, markRaw, onMounted, ref, watch } from "vue"
import { createResource } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import RequestList from "@/components/RequestList.vue"
import TabButtons from "@/components/TabButtons.vue"
import SearchableDropdown from "@/components/SearchableDropdown.vue"

import LeaveRequestItem from "@/components/LeaveRequestItem.vue"
import ExpenseClaimItem from "@/components/ExpenseClaimItem.vue"
import ShiftRequestItem from "@/components/ShiftRequestItem.vue"
import AttendanceRequestItem from "@/components/AttendanceRequestItem.vue"
import ComplaintItem from "@/components/ComplaintItem.vue"

import { getDates, getTotalDays } from "@/data/attendance"
import { getLeaveDates, getLeaveDurationText } from "@/data/leaves"
import { formatJalaliDateShort, toPersianDigits } from "@/utils/jalali"
import { useListUpdate } from "@/composables/realtime"

const __ = inject("$translate")
const employee = inject("$employee")
const socket = inject("$socket")

const REQUEST_FETCH_LIMIT = 500

const activeScope = ref("all")
const selectedType = ref("all")
const selectedStatus = ref("all")
const groupBy = ref("none")
const searchQuery = ref("")

const scopeButtons = [
	{ key: "all", label: __("همه درخواست‌ها") },
	{ key: "my", label: __("درخواست‌های من") },
	{ key: "team", label: __("درخواست‌های تیم") },
]

const requestComponentMap = {
	"Leave Application": markRaw(LeaveRequestItem),
	"Expense Claim": markRaw(ExpenseClaimItem),
	"Shift Request": markRaw(ShiftRequestItem),
	"Attendance Request": markRaw(AttendanceRequestItem),
	"Employee Grievance": markRaw(ComplaintItem),
}

const requestTypeMap = {
	"Leave Application": __("مرخصی"),
	"Expense Claim": __("مطالبه هزینه"),
	"Shift Request": __("درخواست شیفت"),
	"Attendance Request": __("درخواست حضور"),
	"Employee Grievance": __("شکایت / بازخورد"),
}

const pendingStatusSet = new Set(["draft", "open", "pending", "pending approval", "submitted", "investigated", "unpaid"])
const approvedStatusSet = new Set(["approved", "accepted", "completed", "paid", "resolved"])
const rejectedStatusSet = new Set(["rejected", "cancelled", "invalid"])

const myLeavesResource = createResource({
	url: "hrms.api.get_leave_applications",
	auto: false,
	makeParams() {
		return {
			employee: employee.data?.name,
			limit: REQUEST_FETCH_LIMIT,
		}
	},
	transform(data) {
		return (data || []).map((leave) => ({
			...leave,
			doctype: "Leave Application",
			leave_dates: getLeaveDates(leave),
			leave_duration_text: getLeaveDurationText(leave),
		}))
	},
})

const teamLeavesResource = createResource({
	url: "hrms.api.get_leave_applications",
	auto: false,
	makeParams() {
		return {
			employee: employee.data?.name,
			approver_id: employee.data?.user_id,
			for_approval: 1,
			limit: REQUEST_FETCH_LIMIT,
		}
	},
	transform(data) {
		return (data || []).map((leave) => ({
			...leave,
			doctype: "Leave Application",
			leave_dates: getLeaveDates(leave),
			leave_duration_text: getLeaveDurationText(leave),
		}))
	},
})

const myClaimsResource = createResource({
	url: "hrms.api.get_expense_claims",
	auto: false,
	makeParams() {
		return {
			employee: employee.data?.name,
			limit: REQUEST_FETCH_LIMIT,
		}
	},
	transform(data) {
		return (data || []).map((claim) => ({ ...claim, doctype: "Expense Claim" }))
	},
})

const teamClaimsResource = createResource({
	url: "hrms.api.get_expense_claims",
	auto: false,
	makeParams() {
		return {
			employee: employee.data?.name,
			approver_id: employee.data?.user_id,
			for_approval: 1,
			limit: REQUEST_FETCH_LIMIT,
		}
	},
	transform(data) {
		return (data || []).map((claim) => ({ ...claim, doctype: "Expense Claim" }))
	},
})

function formatRequestTime(value) {
	if (!value) return ""
	const [hour = "00", minute = "00"] = String(value).split(":")
	return toPersianDigits(`${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`)
}

function transformAttendanceRequests(data) {
	return (data || []).map((request) => {
		const isCheckinRequest = request.request_mode === "Checkin Request"
		return {
			...request,
			doctype: "Attendance Request",
			is_checkin_request: isCheckinRequest,
			attendance_dates: isCheckinRequest ? formatJalaliDateShort(request.from_date) : getDates(request),
			total_attendance_days: isCheckinRequest ? 1 : getTotalDays(request),
			final_log_type: request.reviewed_log_type || request.requested_log_type,
			final_time: request.reviewed_time || request.requested_time,
			formatted_request_time: formatRequestTime(request.reviewed_time || request.requested_time),
		}
	})
}

const myAttendanceResource = createResource({
	url: "hrms.api.get_attendance_requests",
	auto: false,
	makeParams() {
		return {
			employee: employee.data?.name,
			limit: REQUEST_FETCH_LIMIT,
		}
	},
	transform: transformAttendanceRequests,
})

const teamAttendanceResource = createResource({
	url: "hrms.api.get_attendance_requests",
	auto: false,
	makeParams() {
		return {
			employee: employee.data?.name,
			for_approval: 1,
			limit: REQUEST_FETCH_LIMIT,
		}
	},
	transform: transformAttendanceRequests,
})

function transformShiftRequests(data) {
	return (data || []).map((request) => ({
		...request,
		doctype: "Shift Request",
		shift_dates: getDates(request),
		total_shift_days: getTotalDays(request),
	}))
}

const myShiftResource = createResource({
	url: "hrms.api.get_shift_requests",
	auto: false,
	makeParams() {
		return {
			employee: employee.data?.name,
			limit: REQUEST_FETCH_LIMIT,
		}
	},
	transform: transformShiftRequests,
})

const teamShiftResource = createResource({
	url: "hrms.api.get_shift_requests",
	auto: false,
	makeParams() {
		return {
			employee: employee.data?.name,
			approver_id: employee.data?.user_id,
			for_approval: 1,
			limit: REQUEST_FETCH_LIMIT,
		}
	},
	transform: transformShiftRequests,
})

function transformGrievances(data) {
	return (data || []).map((item) => ({
		...item,
		doctype: "Employee Grievance",
		complaint_date: formatJalaliDateShort(item.date),
	}))
}

const myGrievancesResource = createResource({
	url: "hrms.api.get_employee_grievances",
	auto: false,
	makeParams() {
		return {
			employee: employee.data?.name,
			limit: REQUEST_FETCH_LIMIT,
		}
	},
	transform: transformGrievances,
})

const teamGrievancesResource = createResource({
	url: "hrms.api.get_employee_grievances",
	auto: false,
	makeParams() {
		return {
			employee: employee.data?.name,
			for_approval: 1,
			limit: REQUEST_FETCH_LIMIT,
		}
	},
	transform: transformGrievances,
})

const allResources = [
	myLeavesResource,
	teamLeavesResource,
	myClaimsResource,
	teamClaimsResource,
	myAttendanceResource,
	teamAttendanceResource,
	myShiftResource,
	teamShiftResource,
	myGrievancesResource,
	teamGrievancesResource,
]

const isLoading = computed(() => allResources.some((resource) => resource.loading))

function getRequestStatus(request) {
	if (request.doctype === "Attendance Request") {
		if (request.request_mode === "Checkin Request") {
			return request.review_status || (request.docstatus ? "Submitted" : "Draft")
		}
		if (request.workflow_state_field && request[request.workflow_state_field]) {
			return request[request.workflow_state_field]
		}
		return request.review_status || (request.docstatus ? "Submitted" : "Draft")
	}

	if (request.doctype === "Shift Request") {
		if (request.workflow_state_field && request[request.workflow_state_field]) {
			return request[request.workflow_state_field]
		}
		return request.docstatus ? request.status || "Submitted" : "Open"
	}

	if (request.doctype === "Expense Claim") {
		if (request.workflow_state_field && request[request.workflow_state_field]) {
			return request[request.workflow_state_field]
		}
		if (
			request.approval_status === "Approved"
			&& ["Draft", "Unpaid", "Submitted"].includes(request.status)
		) {
			return `${request.approval_status} & ${request.status}`
		}
		if (request.approval_status === "Rejected") return "Rejected"
		return request.status || request.approval_status || "Draft"
	}

	if (request.workflow_state_field && request[request.workflow_state_field]) {
		return request[request.workflow_state_field]
	}
	return request.status || "Open"
}

function getLastUpdatedAt(request) {
	return request.modified || request.creation || request.posting_date || request.from_date || request.date || "1970-01-01"
}

function normalizeRequests(requests) {
	return (requests || []).map((request) => ({
		...request,
		component: requestComponentMap[request.doctype],
		request_status: getRequestStatus(request),
		updated_at: getLastUpdatedAt(request),
	}))
}

function mergeAndSort(requests) {
	const rowsByKey = new Map()
	for (const request of requests) {
		const key = `${request.doctype}:${request.name}`
		const current = rowsByKey.get(key)
		if (!current) {
			rowsByKey.set(key, request)
			continue
		}
		if (new Date(request.updated_at).getTime() > new Date(current.updated_at).getTime()) {
			rowsByKey.set(key, request)
		}
	}
	return Array.from(rowsByKey.values()).sort(
		(left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime()
	)
}

const myRequests = computed(() =>
	mergeAndSort(
		normalizeRequests([
			...(myLeavesResource.data || []),
			...(myClaimsResource.data || []),
			...(myShiftResource.data || []),
			...(myAttendanceResource.data || []),
			...(myGrievancesResource.data || []),
		])
	)
)

const teamRequests = computed(() =>
	mergeAndSort(
		normalizeRequests([
			...(teamLeavesResource.data || []),
			...(teamClaimsResource.data || []),
			...(teamShiftResource.data || []),
			...(teamAttendanceResource.data || []),
			...(teamGrievancesResource.data || []),
		])
	)
)

const scopeRequests = computed(() => {
	if (activeScope.value === "my") return myRequests.value
	if (activeScope.value === "team") return teamRequests.value
	return mergeAndSort([...myRequests.value, ...teamRequests.value])
})

const typeOptions = computed(() => {
	const seen = new Set()
	const options = []
	for (const request of scopeRequests.value) {
		if (seen.has(request.doctype)) continue
		seen.add(request.doctype)
		options.push({
			value: request.doctype,
			label: requestTypeMap[request.doctype] || request.doctype,
		})
	}
	return options
})

const statusOptions = computed(() => {
	return Array.from(
		new Set(
			scopeRequests.value
				.map((request) => request.request_status)
				.filter(Boolean)
		)
	).sort((left, right) => left.localeCompare(right))
})

const typeDropdownOptions = computed(() => [
	{ value: "all", label: __("همه") },
	...typeOptions.value,
])

const statusDropdownOptions = computed(() => [
	{ value: "all", label: __("همه وضعیت‌ها") },
	...statusOptions.value.map((status) => ({ value: status, label: __(status) })),
])

const groupByOptions = computed(() => [
	{ value: "none", label: __("بدون گروه‌بندی") },
	{ value: "doctype", label: __("بر اساس نوع درخواست") },
	{ value: "status", label: __("بر اساس وضعیت") },
])

function matchSearch(request, query) {
	if (!query) return true
	const haystack = [
		request.employee_name,
		request.subject,
		request.reason,
		request.leave_type,
		request.shift_type,
		request.expense_type,
		request.feedback_type,
		request.grievance_type,
		request.request_mode,
		request.name,
		requestTypeMap[request.doctype],
	]
		.filter(Boolean)
		.join(" ")
		.toLowerCase()
	return haystack.includes(query.toLowerCase())
}

const filteredRequests = computed(() => {
	return scopeRequests.value.filter((request) => {
		if (selectedType.value !== "all" && request.doctype !== selectedType.value) return false
		if (selectedStatus.value !== "all" && request.request_status !== selectedStatus.value) return false
		return matchSearch(request, searchQuery.value)
	})
})

function classifyStatus(status) {
	const normalizedStatus = String(status || "").trim().toLowerCase()
	if (approvedStatusSet.has(normalizedStatus)) return "approved"
	if (rejectedStatusSet.has(normalizedStatus)) return "rejected"
	if (pendingStatusSet.has(normalizedStatus)) return "pending"
	return "pending"
}

const summary = computed(() => {
	const result = { total: scopeRequests.value.length, pending: 0, approved: 0, rejected: 0 }
	for (const request of scopeRequests.value) {
		const bucket = classifyStatus(request.request_status)
		result[bucket] += 1
	}
	return result
})

function clearFilters() {
	selectedType.value = "all"
	selectedStatus.value = "all"
	groupBy.value = "none"
	searchQuery.value = ""
}

function reloadAll() {
	if (!employee.data?.name) return
	allResources.forEach((resource) => resource.reload())
}

watch(
	() => employee.data?.name,
	(employeeName) => {
		if (!employeeName) return
		reloadAll()
	},
	{ immediate: true }
)

watch(
	() => activeScope.value,
	() => {
		selectedType.value = "all"
		selectedStatus.value = "all"
	}
)

onMounted(() => {
	if (!socket) return
	useListUpdate(socket, "Leave Application", () => {
		myLeavesResource.reload()
		teamLeavesResource.reload()
	})
	useListUpdate(socket, "Expense Claim", () => {
		myClaimsResource.reload()
		teamClaimsResource.reload()
	})
	useListUpdate(socket, "Shift Request", () => {
		myShiftResource.reload()
		teamShiftResource.reload()
	})
	useListUpdate(socket, "Attendance Request", () => {
		myAttendanceResource.reload()
		teamAttendanceResource.reload()
	})
	useListUpdate(socket, "Employee Grievance", () => {
		myGrievancesResource.reload()
		teamGrievancesResource.reload()
	})
})
</script>
