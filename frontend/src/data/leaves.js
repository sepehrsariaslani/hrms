import { createResource } from "frappe-ui"
import { employeeResource } from "./employee"
import { watch } from "vue"

import { formatJalaliDateShort } from "@/utils/jalali"

const transformLeaveData = (data) => {
	return data.map((leave) => {
		const isHourly = leave.leave_duration_mode === "ساعتی"
		leave.is_hourly_leave = isHourly
		leave.leave_dates = getLeaveDates(leave)
		leave.leave_duration_text = getLeaveDurationText(leave)
		leave.doctype = "Leave Application"
		return leave
	})
}

export const getLeaveDates = (leave) => {
	if (leave.leave_duration_mode === "ساعتی") {
		return formatJalaliDateShort(leave.hourly_date || leave.from_date)
	}
	if (leave.from_date == leave.to_date)
		return formatJalaliDateShort(leave.from_date)
	else
		return `${formatJalaliDateShort(leave.from_date)} - ${formatJalaliDateShort(
			leave.to_date
		)}`
}

export const getLeaveDurationText = (leave) => {
	if (leave.leave_duration_mode !== "ساعتی") return `${formatDurationNumber(leave.total_leave_days)} روز`
	const fromTime = String(leave.hourly_from_time || "").slice(0, 5)
	const toTime = String(leave.hourly_to_time || "").slice(0, 5)
	const totalHours = formatDurationNumber(leave.total_leave_hours)
	if (fromTime && toTime && totalHours) return `${fromTime} - ${toTime} (${totalHours} ساعت)`
	if (fromTime && toTime) return `${fromTime} - ${toTime}`
	if (totalHours) return `${totalHours} ساعت`
	return "ساعتی"
}

const formatDurationNumber = (value) => {
	const numericValue = Number(value)
	if (!Number.isFinite(numericValue)) return ""
	return String(parseFloat(numericValue.toFixed(2)))
}

export const myLeaves = createResource({
	url: "hrms.api.get_leave_applications",
	auto: false,
	cache: "hrms:my_leaves",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
			limit: 10,
		}
	},
	transform(data) {
		return transformLeaveData(data)
	},
	onSuccess() {
		leaveBalance.reload()
	},
})

export const teamLeaves = createResource({
	url: "hrms.api.get_leave_applications",
	auto: false,
	cache: "hrms:team_leaves",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
			approver_id: employeeResource.data?.user_id,
			for_approval: 1,
			limit: 10,
		}
	},
	transform(data) {
		return transformLeaveData(data)
	},
})

export const leaveBalance = createResource({
	url: "hrms.api.get_leave_balance_map",
	auto: false,
	cache: "hrms:leave_balance",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
		}
	},
	transform: (data) => {
		// Calculate balance percentage for each leave type
		return Object.fromEntries(
			Object.entries(data).map(([leave_type, allocation]) => {
				allocation.balance_percentage =
					(allocation.balance_leaves / allocation.allocated_leaves) * 100
				return [leave_type, allocation]
			})
		)
	},
})

watch(
	() => employeeResource.data?.name,
	(employeeName) => {
		if (!employeeName) return
		myLeaves.reload()
		teamLeaves.reload()
		leaveBalance.reload()
	},
	{ immediate: true }
)
