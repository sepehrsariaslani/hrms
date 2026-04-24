<template>
	<div class="flex flex-col w-full gap-5" v-if="calendarEvents.data">
		<div class="text-lg text-gray-800 font-bold">{{ __(props.title) }}</div>

		<div class="flex flex-col gap-6 bg-white py-6 px-3.5 rounded-lg border-none">
			<!-- Month Change -->
			<div class="flex flex-row justify-between items-center px-4">
				<Button
					icon="chevron-left"
					variant="ghost"
					@click="shiftMonth(-1)"
				/>
				<span class="text-lg text-gray-800 font-bold">
					{{ monthTitle }}
				</span>
				<Button
					icon="chevron-right"
					variant="ghost"
					@click="shiftMonth(1)"
				/>
			</div>

			<!-- Calendar -->
			<div class="grid grid-cols-7 gap-y-3">
				<div
					v-for="day in DAYS"
					:key="day"
					class="flex justify-center text-gray-600 text-sm font-medium leading-6"
				>
					{{ day }}
				</div>
				<div v-for="blank in monthDays.offset" :key="`blank-${blank}`" />
				<div v-for="day in monthDays.days" :key="day.key" class="flex justify-center">
					<button type="button" class="rounded-full" @click="selectDate(day)">
						<div
							class="h-8 w-8 flex rounded-full"
							:class="getDayClass(day)"
						>
							<span :class="getDayLabelClass(day)">
								{{ toPersianDigits(day.jalaliDay) }}
							</span>
						</div>
					</button>
				</div>
			</div>

			<hr />

			<!-- Summary -->
			<div class="grid grid-cols-2 gap-y-3 mx-2 sm:grid-cols-5">
				<div v-for="status in summaryStatuses" :key="status" class="flex flex-col gap-1">
					<div class="flex flex-row gap-1 items-center">
						<span class="rounded full h-3 w-3" :class="colorMap[status]" />
						<span class="text-gray-600 text-sm font-medium leading-5"> {{ __(status) }} </span>
					</div>
					<span class="text-gray-800 text-base font-semibold leading-6 mx-auto">
						{{ summary[status] || 0 }}
					</span>
				</div>
			</div>

			<template v-if="props.showCheckins">
				<hr />
				<div class="mx-2 flex flex-col gap-2">
					<div class="text-sm font-semibold text-gray-800">
						{{ `ورود و خروج ${selectedDateLabel}` }}
					</div>
					<div v-if="dailyCheckins.list.loading" class="text-xs text-gray-500">
						در حال بارگذاری...
					</div>
					<div
						v-else-if="selectedDateCheckins.length"
						class="flex flex-col rounded border border-gray-200 divide-y divide-gray-200 overflow-hidden"
					>
						<div
							v-for="checkin in selectedDateCheckins"
							:key="checkin.name"
							class="flex items-center justify-between px-3 py-2"
						>
							<span class="text-sm text-gray-700 font-medium">
								{{ __(checkin.log_type) }}
							</span>
							<span class="text-sm text-gray-900 font-semibold">
								{{ getCheckinTime(checkin.time) }}
							</span>
						</div>
					</div>
					<div v-else class="text-xs text-gray-500">
						برای این روز ورود/خروجی ثبت نشده است.
					</div>
				</div>
			</template>

			<hr />
			<div class="mx-2 flex flex-col gap-2">
				<div class="text-sm font-semibold text-gray-800">
					برنامه شیفت {{ selectedDateLabel }}
				</div>
				<div v-if="shiftsResource.loading" class="text-xs text-gray-500">
					در حال بارگذاری...
				</div>
				<div
					v-else-if="selectedDateShifts.length"
					class="flex flex-col rounded border border-gray-200 divide-y divide-gray-200 overflow-hidden"
				>
					<div
						v-for="shift in selectedDateShifts"
						:key="shift.name"
						class="flex items-center justify-between px-3 py-2"
					>
						<span class="text-sm text-gray-700 font-medium">
							{{ shift.shift_type }}
						</span>
						<span class="text-sm text-gray-900 font-semibold">
							{{ formatShiftTiming(shift) }}
						</span>
					</div>
				</div>
				<div v-else class="text-xs text-gray-500">
					برای این روز برنامه شیفتی ثبت نشده است.
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue"
import { createListResource, createResource } from "frappe-ui"
import {
	PERSIAN_MONTHS,
	formatGregorianDate,
	formatJalaliDate,
	formatJalaliTime,
	getJalaliDaysInMonth,
	gregorianToJalali,
	jalaliToGregorian,
	toPersianDigits,
} from "@/utils/jalali"

const props = defineProps({
	selectedDate: {
		type: String,
		default: "",
	},
	showCheckins: {
		type: Boolean,
		default: true,
	},
	title: {
		type: String,
		default: "Attendance Calendar",
	},
})
const emit = defineEmits(["dateSelected"])

const employee = inject("$employee")
const __ = inject("$translate")
const today = new Date()
const todayDateString = formatGregorianDate(today)
const currentJalaliDate = gregorianToJalali(
	today.getFullYear(),
	today.getMonth() + 1,
	today.getDate()
)
const localSelectedDate = ref(props.selectedDate || todayDateString)
const activeJalaliMonth = ref({
	year: currentJalaliDate.year,
	month: currentJalaliDate.month,
})

const colorMap = {
	Present: "bg-green-200 dark:bg-green-700",
	"Work From Home": "bg-green-200 dark:bg-green-700",
	"Half Day": "bg-yellow-200 dark:bg-yellow-700",
	Absent: "bg-red-200 dark:bg-red-700",
	"On Leave": "bg-blue-200 dark:bg-blue-700",
	Holiday: "bg-gray-200 dark:bg-gray-700",
}

// __("Present"), __("Half Day"), __("Absent"), __("On Leave"), __("Work From Home")
const summaryStatuses = ["Present", "Half Day", "Absent", "On Leave", "Holiday"]
const FULL_DAY_HOURS = 8

const selectedDateLabel = computed(() => {
	return formatJalaliDate(localSelectedDate.value, { withWeekday: true })
})

const monthTitle = computed(() => {
	return `${PERSIAN_MONTHS[activeJalaliMonth.value.month - 1]} ${toPersianDigits(
		activeJalaliMonth.value.year
	)}`
})

const monthDays = computed(() => {
	const year = activeJalaliMonth.value.year
	const month = activeJalaliMonth.value.month
	const firstGregorian = jalaliToGregorian(year, month, 1)
	const firstDate = new Date(
		firstGregorian.year,
		firstGregorian.month - 1,
		firstGregorian.day
	)
	const offset = (firstDate.getDay() + 1) % 7
	const totalDays = getJalaliDaysInMonth(year, month)
	const days = []

	for (let day = 1; day <= totalDays; day++) {
		const gregorianDate = jalaliToGregorian(year, month, day)
		const date = new Date(
			gregorianDate.year,
			gregorianDate.month - 1,
			gregorianDate.day
		)
		days.push({
			key: `${year}-${month}-${day}`,
			jalaliDay: day,
			gregorianDate: formatGregorianDate(date),
			isToday:
				date.getFullYear() === today.getFullYear() &&
				date.getMonth() === today.getMonth() &&
				date.getDate() === today.getDate(),
		})
	}

	return { offset, days }
})

const summary = computed(() => {
	const result = {
		Present: 0,
		"Half Day": 0,
		Absent: 0,
		"On Leave": 0,
		Holiday: 0,
	}

	for (const day of monthDays.value.days) {
		const date = day.gregorianDate
		const calendarStatus = calendarEvents.data?.[date]

		if (date > todayDateString) continue

		if (calendarStatus === "Holiday") {
			result.Holiday += 1
			continue
		}

		if (isApprovedLeaveDate(date) || calendarStatus === "On Leave") {
			result["On Leave"] += 1
			continue
		}

		const checkinSummary = monthCheckinSummary.value[date]
		if (!checkinSummary || !checkinSummary.total) {
			result.Absent += 1
			continue
		}

		const hasIn = (checkinSummary.IN || 0) > 0
		const hasOut = (checkinSummary.OUT || 0) > 0
		const workingHours = getWorkingHours(checkinSummary)
		if (hasIn && hasOut && workingHours > FULL_DAY_HOURS) {
			result.Present += 1
		} else {
			result["Half Day"] += 1
		}
	}

	return result
})

const selectedDateCheckins = computed(() => dailyCheckins.data || [])
const monthCheckinSummary = computed(() => {
	const summary = {}

	for (const checkin of monthCheckins.data || []) {
		const date = String(checkin.time || "").slice(0, 10)
		if (!date) continue

		if (!summary[date]) {
			summary[date] = {
				IN: 0,
				OUT: 0,
				total: 0,
				firstIn: "",
				lastOut: "",
			}
		}
		summary[date][checkin.log_type] = (summary[date][checkin.log_type] || 0) + 1
		summary[date].total += 1

		if (checkin.log_type === "IN" && !summary[date].firstIn) {
			summary[date].firstIn = checkin.time
		}

		if (checkin.log_type === "OUT") {
			summary[date].lastOut = checkin.time
		}
	}

	return summary
})

const monthShiftSummary = computed(() => {
	const summary = {}
	const range = getMonthDateRange()

	for (const shift of shiftsResource.data || []) {
		if (!shift.start_date) continue
		const shiftStart = shift.start_date > range.fromDate ? shift.start_date : range.fromDate
		const shiftEnd =
			(shift.end_date || shift.start_date) < range.toDate
				? shift.end_date || shift.start_date
				: range.toDate
		if (shiftStart > shiftEnd) continue

		for (const date of expandDateRange(shiftStart, shiftEnd)) {
			if (!summary[date]) {
				summary[date] = []
			}
			summary[date].push(shift)
		}
	}

	return summary
})

const selectedDateShifts = computed(() => monthShiftSummary.value[localSelectedDate.value] || [])

const leaveDateStates = computed(() => {
	const states = {}
	const range = getMonthDateRange()

	for (const leave of monthLeaveApplications.data || []) {
		const startDate = leave.from_date > range.fromDate ? leave.from_date : range.fromDate
		const endDate = leave.to_date < range.toDate ? leave.to_date : range.toDate
		if (!startDate || !endDate || startDate > endDate) continue

		const leaveState = getLeaveState(leave)
		if (!leaveState) continue

		for (const date of expandDateRange(startDate, endDate)) {
			if (!states[date] || leaveState === "approved") {
				states[date] = leaveState
			}
		}
	}

	return states
})

function shiftMonth(delta) {
	let month = activeJalaliMonth.value.month + delta
	let year = activeJalaliMonth.value.year

	if (month < 1) {
		month = 12
		year -= 1
	} else if (month > 12) {
		month = 1
		year += 1
	}

	activeJalaliMonth.value = { year, month }
}

function selectDate(day) {
	localSelectedDate.value = day.gregorianDate
}

function getDayClass(day) {
	const classes = []
	const status = getEventOnDate(day)
	if (status) classes.push(colorMap[status])
	if (hasScheduledShift(day.gregorianDate)) {
		classes.push("!ring-2 !ring-indigo-300")
	}

	const leaveState = leaveDateStates.value[day.gregorianDate]
	if (leaveState === "pending") {
		classes.push("!bg-blue-200 dark:!bg-blue-700 !ring-2 !ring-blue-400 dark:!ring-blue-500 animate-pulse")
	} else if (leaveState === "approved") {
		classes.push("!bg-blue-300 dark:!bg-blue-700")
	}

	if (day.isToday) {
		classes.push("!ring-2 !ring-sky-500")
	}

	if (hasSingleLogType(day.gregorianDate)) {
		classes.push("!ring-2 !ring-rose-400")
	}

	if (localSelectedDate.value === day.gregorianDate) {
		classes.push("!ring-2 !ring-gray-900 dark:!ring-gray-100")
	}

	return classes
}

function getDayLabelClass(day) {
	const status = getEventOnDate(day)
	const leaveState = leaveDateStates.value[day.gregorianDate]
	const hasStatus = Boolean(status || leaveState)
	return hasStatus
		? "text-sm font-semibold m-auto text-gray-900 dark:text-gray-100"
		: "text-sm font-medium m-auto text-gray-800"
}

function hasScheduledShift(date) {
	return Boolean(monthShiftSummary.value[date]?.length)
}

function hasSingleLogType(date) {
	const summary = monthCheckinSummary.value[date]
	if (!summary) return false
	const hasIn = (summary.IN || 0) > 0
	const hasOut = (summary.OUT || 0) > 0
	return hasIn !== hasOut
}

function getCheckinTime(timestamp) {
	return formatJalaliTime(timestamp, { withSeconds: true })
}

function formatShiftTiming(shift) {
	const start = String(shift.start_time || "").slice(0, 5)
	const end = String(shift.end_time || "").slice(0, 5)
	if (!(start && end)) return "-"
	return `${toPersianDigits(start)} - ${toPersianDigits(end)}`
}

function getWorkingHours(checkinSummary) {
	const firstIn = checkinSummary.firstIn
	const lastOut = checkinSummary.lastOut
	if (!(firstIn && lastOut)) return 0

	const firstDate = new Date(String(firstIn).replace(" ", "T"))
	const lastDate = new Date(String(lastOut).replace(" ", "T"))
	const durationHours = (lastDate.getTime() - firstDate.getTime()) / (1000 * 60 * 60)
	return durationHours > 0 ? durationHours : 0
}

const getEventOnDate = (day) => {
	return calendarEvents.data?.[day.gregorianDate]
}

function parseDocstatus(value) {
	if (value === null || value === undefined || value === "") return 0
	return Number(value)
}

function getLeaveState(leave) {
	const status = String(leave.status || leave.workflow_state || "").trim().toLowerCase()
	const docstatus = parseDocstatus(leave.docstatus)

	if (status === "approved" || docstatus === 1) return "approved"
	if (["rejected", "cancelled"].includes(status) || docstatus === 2) return null
	return "pending"
}

function isApprovedLeaveDate(date) {
	return leaveDateStates.value[date] === "approved"
}

function expandDateRange(fromDate, toDate) {
	const dates = []
	let currentDate = fromDate

	while (currentDate <= toDate) {
		dates.push(currentDate)
		const dateObj = new Date(`${currentDate}T12:00:00`)
		dateObj.setDate(dateObj.getDate() + 1)
		currentDate = formatGregorianDate(dateObj)
	}

	return dates
}

const DAYS = ["ش", "ی", "د", "س", "چ", "پ", "ج"]

const dailyCheckins = createListResource({
	doctype: "Employee Checkin",
	fields: ["name", "log_type", "time"],
	filters: {
		employee: employee.data.name,
	},
	orderBy: "time asc",
	auto: false,
})

const monthCheckins = createListResource({
	doctype: "Employee Checkin",
	fields: ["name", "log_type", "time"],
	filters: {
		employee: employee.data.name,
	},
	orderBy: "time asc",
	auto: false,
})

const monthLeaveApplications = createListResource({
	doctype: "Leave Application",
	fields: ["name", "from_date", "to_date", "status", "docstatus"],
	filters: {
		employee: employee.data.name,
	},
	orderBy: "from_date asc",
	auto: false,
})

const shiftsResource = createResource({
	url: "hrms.api.get_shifts",
	auto: false,
})

function loadDailyCheckins(date) {
	if (!employee.data?.name) return
	dailyCheckins.filters.employee = employee.data.name
	dailyCheckins.filters.time = [
		"between",
		[`${date} 00:00:00`, `${date} 23:59:59`],
	]
	dailyCheckins.reload()
}

function getMonthDateRange() {
	const year = activeJalaliMonth.value.year
	const month = activeJalaliMonth.value.month
	const firstGregorian = jalaliToGregorian(year, month, 1)
	const lastGregorian = jalaliToGregorian(year, month, getJalaliDaysInMonth(year, month))
	return {
		fromDate: formatGregorianDate(
			new Date(firstGregorian.year, firstGregorian.month - 1, firstGregorian.day)
		),
		toDate: formatGregorianDate(
			new Date(lastGregorian.year, lastGregorian.month - 1, lastGregorian.day)
		),
	}
}

function loadMonthCheckins() {
	if (!employee.data?.name) return
	const range = getMonthDateRange()
	monthCheckins.filters.employee = employee.data.name
	monthCheckins.filters.time = [
		"between",
		[`${range.fromDate} 00:00:00`, `${range.toDate} 23:59:59`],
	]
	monthCheckins.reload()
}

function loadMonthLeaveApplications() {
	if (!employee.data?.name) return
	const range = getMonthDateRange()
	monthLeaveApplications.filters.employee = employee.data.name
	monthLeaveApplications.filters.from_date = ["<=", range.toDate]
	monthLeaveApplications.filters.to_date = [">=", range.fromDate]
	monthLeaveApplications.reload()
}

async function loadShifts() {
	if (!employee.data?.name) return
	await shiftsResource.fetch({
		employee: employee.data.name,
	})
}

//resources
const calendarEvents = createResource({
	url: "hrms.api.get_attendance_calendar_events",
	auto: true,
	cache: "hrms:attendance_calendar_events",
	makeParams() {
		const range = getMonthDateRange()

		return {
			employee: employee.data.name,
			from_date: range.fromDate,
			to_date: range.toDate,
		}
	},
})

watch(
	() => `${activeJalaliMonth.value.year}-${activeJalaliMonth.value.month}`,
	() => {
		calendarEvents.fetch()
		loadMonthCheckins()
		loadMonthLeaveApplications()
		loadShifts()
	},
	{ immediate: true }
)

watch(
	() => employee.data?.name,
	(value) => {
		if (!value) return
		calendarEvents.fetch()
		loadMonthCheckins()
		loadMonthLeaveApplications()
		loadShifts()
		loadDailyCheckins(localSelectedDate.value)
	},
	{ immediate: true }
)

watch(
	() => props.selectedDate,
	(value) => {
		if (!value) return
		localSelectedDate.value = value
	}
)

watch(
	() => localSelectedDate.value,
	(value) => {
		if (!value || !props.showCheckins) return
		loadDailyCheckins(value)
		emit("dateSelected", value)
	},
	{ immediate: true }
)
</script>
