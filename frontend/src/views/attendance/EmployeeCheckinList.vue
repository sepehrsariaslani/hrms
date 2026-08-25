<template>
	<BaseLayout :pageTitle="__('تاریخچه تردد')">
		<template #body>
			<div class="w-full max-w-5xl mx-auto mt-7 mb-7 px-4 flex flex-col gap-4">

				<!-- Month Navigation -->
				<div class="flex items-center justify-between bg-white rounded-xl px-4 py-3 shadow-sm">
					<button
						class="p-1 rounded-lg hover:bg-gray-100 transition"
						@click="prevMonth"
					>
						<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-600" />
					</button>
					<span class="font-semibold text-gray-800 text-sm">{{ monthLabel }}</span>
					<button
						class="p-1 rounded-lg hover:bg-gray-100 transition"
						:disabled="!canGoNext"
						:class="canGoNext ? '' : 'opacity-30 cursor-not-allowed'"
						@click="nextMonth"
					>
						<FeatherIcon name="chevron-left" class="h-5 w-5 text-gray-600" />
					</button>
				</div>

				<!-- Loading -->
				<div v-if="checkinsResource.loading" class="flex justify-center py-14">
					<LoadingIndicator class="w-8 h-8 text-amber-500" />
				</div>

				<template v-else>
					<!-- Monthly Summary -->
					<div v-if="dailySummary.length" class="grid grid-cols-3 gap-3">
						<div class="bg-white rounded-xl p-3 text-center shadow-sm">
							<div class="text-xl font-bold text-amber-600">{{ totalDays }}</div>
							<div class="text-[11px] text-gray-500 mt-0.5">روز حضور</div>
						</div>
						<div class="bg-white rounded-xl p-3 text-center shadow-sm">
							<div class="text-xl font-bold text-green-600">{{ totalNetHoursLabel }}</div>
							<div class="text-[11px] text-gray-500 mt-0.5">ساعت خالص</div>
						</div>
						<div class="bg-white rounded-xl p-3 text-center shadow-sm">
							<div class="text-xl font-bold text-blue-600">{{ avgDailyHoursLabel }}</div>
							<div class="text-[11px] text-gray-500 mt-0.5">میانگین روزانه</div>
						</div>
					</div>

					<!-- Empty State -->
					<EmptyState v-if="!dailySummary.length" message="تردد یافت نشد" />

					<!-- Daily Cards -->
					<div v-else class="flex flex-col gap-3">
						<div
							v-for="day in dailySummary"
							:key="day.date"
							class="bg-white rounded-xl p-4 shadow-sm"
						>
							<!-- Header: date + net hours badge -->
							<div class="flex items-center justify-between mb-3">
								<div class="font-semibold text-gray-800 text-sm">{{ day.jalaliDate }}</div>
								<div
									:class="[
										'text-xs font-bold px-3 py-1 rounded-full',
										day.netMinutes > 0
											? 'bg-green-100 text-green-700'
											: 'bg-gray-100 text-gray-400',
									]"
								>
									{{ day.netMinutes > 0 ? formatNetHours(day.netMinutes) + ' ساعت خالص' : 'بدون جفت ورود/خروج' }}
								</div>
							</div>

							<!-- First-in / Last-out -->
							<div class="grid grid-cols-2 gap-2 mb-3">
								<div class="bg-blue-50 rounded-lg p-2.5 flex items-center gap-2">
									<FeatherIcon name="log-in" class="h-4 w-4 text-blue-500 shrink-0" />
									<div>
										<div class="text-[10px] text-gray-400">اولین ورود</div>
										<div class="text-sm font-medium text-gray-800">{{ day.firstIn || '—' }}</div>
									</div>
								</div>
								<div class="bg-amber-50 rounded-lg p-2.5 flex items-center gap-2">
									<FeatherIcon name="log-out" class="h-4 w-4 text-amber-500 shrink-0" />
									<div>
										<div class="text-[10px] text-gray-400">آخرین خروج</div>
										<div class="text-sm font-medium text-gray-800">{{ day.lastOut || '—' }}</div>
									</div>
								</div>
							</div>

							<!-- Individual log chips -->
							<div class="flex flex-wrap gap-1.5">
								<span
									v-for="log in day.logs"
									:key="log.name"
									:class="[
										'text-xs px-2.5 py-0.5 rounded-full font-medium',
										log.log_type === 'IN'
											? 'bg-blue-100 text-blue-700'
											: 'bg-amber-100 text-amber-700',
									]"
								>
									{{ log.log_type === 'IN' ? '↓' : '↑' }} {{ formatTime(log.time) }}
								</span>
							</div>
						</div>
					</div>
				</template>

			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue"
import { FeatherIcon, createResource, LoadingIndicator } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import EmptyState from "@/components/EmptyState.vue"
import {
	gregorianToJalali,
	jalaliToGregorian,
	PERSIAN_MONTHS,
	formatJalaliDate,
	getJalaliDaysInMonth,
} from "@/utils/jalali"

const __ = inject("$translate")
const employee = inject("$employee")

// ─── Month state ─────────────────────────────────────────────────────────────
const now = new Date()
const jalaliNow = gregorianToJalali(now.getFullYear(), now.getMonth() + 1, now.getDate())

const jalaliYear = ref(jalaliNow.jy)
const jalaliMonth = ref(jalaliNow.jm)

const monthLabel = computed(
	() => `${PERSIAN_MONTHS[jalaliMonth.value - 1]} ${jalaliYear.value}`
)

const canGoNext = computed(
	() =>
		jalaliYear.value < jalaliNow.jy ||
		(jalaliYear.value === jalaliNow.jy && jalaliMonth.value < jalaliNow.jm)
)

function prevMonth() {
	if (jalaliMonth.value === 1) {
		jalaliMonth.value = 12
		jalaliYear.value--
	} else {
		jalaliMonth.value--
	}
	fetchCheckins()
}

function nextMonth() {
	if (!canGoNext.value) return
	if (jalaliMonth.value === 12) {
		jalaliMonth.value = 1
		jalaliYear.value++
	} else {
		jalaliMonth.value++
	}
	fetchCheckins()
}

// ─── Date range ───────────────────────────────────────────────────────────────
function monthDateRange() {
	const jy = jalaliYear.value
	const jm = jalaliMonth.value
	const firstG = jalaliToGregorian(jy, jm, 1)
	const lastDay = getJalaliDaysInMonth(jy, jm)
	const lastG = jalaliToGregorian(jy, jm, lastDay)
	const pad = (n) => String(n).padStart(2, "0")
	return {
		from: `${firstG.gy}-${pad(firstG.gm)}-${pad(firstG.gd)}`,
		to: `${lastG.gy}-${pad(lastG.gm)}-${pad(lastG.gd)}`,
	}
}

// ─── Resource ─────────────────────────────────────────────────────────────────
const checkinsResource = createResource({
	url: "frappe.client.get_list",
	auto: false,
})

function fetchCheckins() {
	if (!employee.data?.name) return
	const { from, to } = monthDateRange()
	checkinsResource.fetch({
		doctype: "Employee Checkin",
		fields: ["name", "log_type", "time"],
		filters: [
			["employee", "=", employee.data.name],
			["time", ">=", from + " 00:00:00"],
			["time", "<=", to + " 23:59:59"],
		],
		order_by: "time asc",
		limit_page_length: 500,
	})
}

// Fetch when employee data becomes available
watch(
	() => employee.data?.name,
	(name) => {
		if (name) fetchCheckins()
	},
	{ immediate: true }
)

// ─── Helpers ──────────────────────────────────────────────────────────────────
function formatTime(datetime) {
	if (!datetime) return "—"
	const parts = String(datetime).split(" ")
	const timePart = parts[1] || parts[0]
	return timePart.substring(0, 5)
}

function formatNetHours(minutes) {
	if (!minutes || minutes <= 0) return "—"
	const h = Math.floor(minutes / 60)
	const m = Math.floor(minutes % 60)
	return `${h}:${String(m).padStart(2, "0")}`
}

// ─── Daily summary ────────────────────────────────────────────────────────────
const dailySummary = computed(() => {
	const checkins = checkinsResource.data || []
	if (!checkins.length) return []

	const byDate = {}
	for (const c of checkins) {
		const date = String(c.time || "").split(" ")[0]
		if (!date) continue
		if (!byDate[date]) byDate[date] = []
		byDate[date].push(c)
	}

	return Object.entries(byDate)
		.sort(([a], [b]) => b.localeCompare(a))
		.map(([date, logs]) => {
			const sorted = [...logs].sort((a, b) =>
				String(a.time).localeCompare(String(b.time))
			)

			let netMinutes = 0
			let firstIn = null
			let lastOut = null
			let lastInTime = null

			for (const log of sorted) {
				if (log.log_type === "IN") {
					if (!firstIn) firstIn = formatTime(log.time)
					lastInTime = log.time
				} else if (log.log_type === "OUT") {
					lastOut = formatTime(log.time)
					if (lastInTime) {
						const inMs = new Date(lastInTime.replace(" ", "T")).getTime()
						const outMs = new Date(log.time.replace(" ", "T")).getTime()
						if (outMs > inMs) netMinutes += (outMs - inMs) / 60000
						lastInTime = null
					}
				}
			}

			return {
				date,
				jalaliDate: formatJalaliDate(date),
				logs: sorted,
				netMinutes,
				firstIn,
				lastOut,
			}
		})
})

const totalDays = computed(() => dailySummary.value.length)

const totalNetMinutes = computed(() =>
	dailySummary.value.reduce((sum, d) => sum + d.netMinutes, 0)
)

const totalNetHoursLabel = computed(() => formatNetHours(totalNetMinutes.value))

const avgDailyHoursLabel = computed(() => {
	if (!totalDays.value) return "—"
	return formatNetHours(totalNetMinutes.value / totalDays.value)
})
</script>
