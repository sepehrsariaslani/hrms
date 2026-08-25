import { createResource } from "frappe-ui"
import { watch } from "vue"
import { employeeResource } from "./employee"

import dayjs from "@/utils/dayjs"
import { formatJalaliDateShort, toPersianDigits } from "@/utils/jalali"


export const getDates = (shift) => {
	const fromDate = formatJalaliDateShort(shift.from_date)
	const toDate = shift.to_date ? formatJalaliDateShort(shift.to_date) : "Ongoing"
	return fromDate == toDate ? fromDate : `${fromDate} - ${toDate}`
}

export const getTotalDays = (shift) => {
	if (!shift.to_date) return null
	const toDate = dayjs(shift.to_date)
	const fromDate = dayjs(shift.from_date)
	return toDate.diff(fromDate, "d") + 1
}

export const getShiftDates = (shift) => {
	const startDate = formatJalaliDateShort(shift.start_date)
	const endDate = shift.end_date ? formatJalaliDateShort(shift.end_date) : "Ongoing"
	return startDate == endDate ? startDate : `${startDate} - ${endDate}`
}

export const getTotalShiftDays = (shift) => {
	if (!shift.end_date) return null
	const end_date = dayjs(shift.end_date)
	const start_date = dayjs(shift.start_date)
	return end_date.diff(start_date, "d") + 1
}

export const getShiftTiming = (shift) => {
	return (
		shift.start_time.split(":").slice(0, 2).join(":") +
		" - " +
		shift.end_time.split(":").splice(0, 2).join(":")
	)
}

const formatTime = (value) => {
	if (!value) return ""
	const [hour = "00", minute = "00"] = String(value).split(":")
	return toPersianDigits(`${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`)
}

const transformShiftRequests = (data) =>
	data.map((request) => {
		request.doctype = "Shift Request"
		request.shift_dates = getDates(request)
		request.total_shift_days = getTotalDays(request)
		return request
	})

export const myAttendanceRequests = createResource({
	url: "hrms.api.get_attendance_requests",
	auto: true,
	cache: "hrms:my_attendance_requests",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
			limit: 10,
		}
	},
	transform(data) {
		return transformAttendanceRequests(data)
	}
})
const transformAttendanceRequests = (data) => {
		return data.map((request) => {
			request.doctype = "Attendance Request"
			request.is_checkin_request = request.request_mode === "Checkin Request"
			request.attendance_dates = request.is_checkin_request
				? formatJalaliDateShort(request.from_date)
				: getDates(request)
			request.total_attendance_days = request.is_checkin_request ? 1 : getTotalDays(request)
			request.final_log_type = request.reviewed_log_type || request.requested_log_type
			request.final_time = request.reviewed_time || request.requested_time
			request.formatted_request_time = formatTime(request.final_time)
			return request
		})
}
export const myShiftRequests = createResource({
	url: "hrms.api.get_shift_requests",
	auto: false,
	cache: "hrms:my_shift_requests",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
			limit: 10,
		}
	},
	transform(data) {
		return transformShiftRequests(data)
	},
})

export const teamShiftRequests = createResource({
	url: "hrms.api.get_shift_requests",
	auto: false,
	cache: "hrms:team_shift_requests",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
			approver_id: employeeResource.data?.user_id,
			for_approval: 1,
			limit: 10,
		}
	},
	transform(data) {
		return transformShiftRequests(data)
	},
})
export const teamAttendanceRequests = createResource({
	url: "hrms.api.get_attendance_requests",
	auto: false,
	cache: "hrms:team_attendance_requests",
	makeParams() {
		return {
			employee: employeeResource.data?.name,
			for_approval: 1,
			limit: 10,
		}
	},
	transform: (data) => {
		return transformAttendanceRequests(data)
	},
})

watch(
	() => employeeResource.data?.name,
	(employeeName) => {
		if (!employeeName) return
		myAttendanceRequests.reload()
		myShiftRequests.reload()
		teamShiftRequests.reload()
		teamAttendanceRequests.reload()
	},
	{ immediate: true }
)
