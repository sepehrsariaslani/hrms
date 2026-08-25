<template>
	<div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
		<!-- Header -->
		<div class="mb-3 flex items-center justify-between">
			<h3 class="text-sm font-bold text-slate-800">{{ __("نمودار تردد روزانه") }}</h3>
			<div class="flex items-center gap-1">
				<Button
					size="sm"
					variant="ghost"
					class="!rounded-lg !px-2 !py-0.5 text-[11px]"
					:class="quickRange === '7d' ? 'bg-amber-50 text-amber-700' : 'text-slate-500'"
					@click="setQuickRange('7d')"
				>
					۷ روز اخیر
				</Button>
				<Button
					size="sm"
					variant="ghost"
					class="!rounded-lg !px-2 !py-0.5 text-[11px]"
					:class="quickRange === 'month' ? 'bg-amber-50 text-amber-700' : 'text-slate-500'"
					@click="setQuickRange('month')"
				>
					این ماه
				</Button>
			</div>
		</div>

		<!-- Date Range Pickers -->
		<div class="mb-4 flex items-center gap-2">
			<div class="flex-1">
				<JalaliDatePicker
					v-model="fromDate"
					:placeholder="__('از تاریخ')"
					:max-date="todayStr"
					@change="onDateChange"
				/>
			</div>
			<div class="flex-1">
				<JalaliDatePicker
					v-model="toDate"
					:placeholder="__('تا تاریخ')"
					:max-date="todayStr"
					@change="onDateChange"
				/>
			</div>
		</div>

		<!-- Loading State -->
		<div v-if="chartResource.loading" class="flex flex-col gap-3">
			<div class="h-5 w-32 animate-pulse rounded bg-slate-100" />
			<div class="h-[200px] animate-pulse rounded-xl bg-slate-100" />
			<div class="flex justify-center gap-4">
				<div class="h-3 w-16 animate-pulse rounded bg-slate-100" />
				<div class="h-3 w-16 animate-pulse rounded bg-slate-100" />
				<div class="h-3 w-16 animate-pulse rounded bg-slate-100" />
			</div>
		</div>

		<!-- Error State -->
		<div v-else-if="chartResource.error" class="flex flex-col items-center py-8">
			<FeatherIcon name="alert-circle" class="h-7 w-7 text-red-400" />
			<p class="mt-2 text-sm text-slate-500">{{ __("خطا در دریافت داده‌های تردد") }}</p>
			<button
				class="mt-2 text-xs font-medium text-amber-600 underline"
				@click="fetchData"
			>
				{{ __("تلاش مجدد") }}
			</button>
		</div>

		<!-- Empty State -->
		<div v-else-if="!chartData.length" class="flex flex-col items-center py-12">
			<FeatherIcon name="bar-chart-2" class="h-8 w-8 text-slate-300" />
			<p class="mt-2 text-sm text-slate-400">
				{{ __("در این بازه زمانی ترددی ثبت نشده است") }}
			</p>
		</div>

		<!-- Chart -->
		<div v-else class="flex flex-col gap-3">
			<!-- Chart Area -->
			<div class="relative flex" dir="rtl">
				<!-- Y-Axis -->
				<div class="flex flex-col justify-between pl-2 pb-6" style="height: 200px">
					<span
						v-for="label in yAxisLabels"
						-key="label"
						class="text-[10px] leading-none text-slate-400"
					>
						{{ label }}
					</span>
				</div>

				<!-- Chart Body -->
				<div class="relative flex-1 border-r border-b border-slate-200">
					<!-- Grid Lines -->
					<div
						v-for="i in gridLineCount"
						:key="`grid-${i}`"
						class="absolute right-0 left-0 border-t border-dashed border-slate-100"
						:style="{ bottom: `${(i / gridLineCount) * 100}%` }"
					/>

					<!-- Bars Container -->
					<div
						class="absolute inset-0 flex items-end justify-around px-1"
						:style="{ paddingBottom: '0' }"
					>
						<div
							v-for="(day, idx) in chartData"
							-key="day.date"
							class="group relative flex flex-col items-center"
							:style="{ width: barWidth + 'px' }"
							:aria-label="day.ariaLabel"
							tabindex="0"
							@mouseenter="hoveredIdx = idx"
							@mouseleave="hoveredIdx = null"
							@focus="hoveredIdx = idx"
							@blur="hoveredIdx = null"
						>
							<!-- Tooltip -->
							<div
								v-if="hoveredIdx === idx"
								class="absolute bottom-full z-10 mb-2 whitespace-nowrap rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-lg"
								dir="rtl"
							>
								<div class="font-semibold text-slate-800">{{ day.jalaliFull }}</div>
								<div class="mt-1 border-t border-slate-100 pt-1">
									<span class="text-slate-500">{{ __("کل حضور") }}: </span>
									<span class="font-medium text-slate-700">{{ formatHours(day.totalHours) }}</span>
								</div>
								<div>
									<span class="text-blue-500">{{ __("ساعات عادی") }}: </span>
									<span class="font-medium text-slate-700">{{ formatHours(day.regularHours) }}</span>
								</div>
								<div v-if="day.overtimeHours > 0">
									<span class="text-emerald-500">{{ __("اضافه‌کاری") }}: </span>
									<span class="font-medium text-emerald-600">{{ formatHours(day.overtimeHours) }}</span>
								</div>
								<div v-if="day.deficitHours > 0">
									<span class="text-red-400">{{ __("کمبود ساعت") }}: </span>
									<span class="font-medium text-red-500">{{ formatHours(day.deficitHours) }}</span>
								</div>
							</div>

							<!-- Bar Stack (bottom to top: deficit -> regular -> overtime) -->
							<div
								class="flex w-full flex-col justify-end rounded-t"
								:style="{ height: '200px' }"
							>
								<!-- Deficit (red, bottom) -->
								<div
									v-if="day.deficitHours > 0"
									class="w-full rounded-b bg-red-400 transition-all duration-300"
									:style="{ height: getBarPercent(day.deficitHours) + '%' }"
								/>
								<!-- Regular (blue, middle) -->
								<div
									v-if="day.regularHours > 0"
									class="w-full bg-blue-500 transition-all duration-300"
									:class="day.overtimeHours > 0 ? '' : 'rounded-t'"
									:style="{ height: getBarPercent(day.regularHours) + '%' }"
								/>
								<!-- Overtime (green, top) -->
								<div
									v-if="day.overtimeHours > 0"
									class="w-full rounded-t bg-emerald-500 transition-all duration-300"
									:style="{ height: getBarPercent(day.overtimeHours) + '%' }"
								/>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- X-Axis Labels -->
			<div class="relative flex justify-around pr-10" dir="rtl">
				<span
					v-for="(day, idx) in chartData"
					-key="'label-' + day.date"
					class="text-center text-[10px] text-slate-500"
					:style="{ width: barWidth + 'px' }"
				>
					{{ shouldShowXLabel(idx) ? toPersianDigits(day.jalaliDay) : "" }}
				</span>
			</div>

			<!-- Legend -->
			<div class="mt-2 flex items-center justify-center gap-4" dir="rtl">
				<div class="flex items-center gap-1.5">
					<span class="inline-block h-2 w-2 rounded-full bg-blue-500" />
					<span class="text-[11px] text-slate-500">{{ __("ساعات عادی") }}</span>
				</div>
				<div class="flex items-center gap-1.5">
					<span class="inline-block h-2 w-2 rounded-full bg-emerald-500" />
					<span class="text-[11px] text-slate-500">{{ __("اضافه‌کاری") }}</span>
				</div>
				<div class="flex items-center gap-1.5">
					<span class="inline-block h-2 w-2 rounded-full bg-red-400" />
					<span class="text-[11px] text-slate-500">{{ __("کمبود ساعت") }}</span>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue"
import { Button, FeatherIcon, createResource } from "frappe-ui"

import JalaliDatePicker from "@/components/JalaliDatePicker.vue"
import {
	gregorianToJalali,
	jalaliToGregorian,
	getJalaliDaysInMonth,
	formatJalaliDate,
	toPersianDigits,
} from "@/utils/jalali"

const props = defineProps({
	employee: {
		type: String,
		required: true,
	},
})

const __ = inject("$translate")

// ─── Date State ─────────────────────────────────────────────────────────────
const now = new Date()
const jalaliNow = gregorianToJalali(now.getFullYear(), now.getMonth() + 1, now.getDate())
const todayStr = formatGregorianDate(now)

const defaultFrom = jalaliToGregorian(jalaliNow.year, jalaliNow.month, 1)
const defaultTo = jalaliToGregorian(jalaliNow.year, jalaliNow.month, getJalaliDaysInMonth(jalaliNow.year, jalaliNow.month))

const fromDate = ref(formatGregorianDate(new Date(defaultFrom.year, defaultFrom.month - 1, defaultFrom.day)))
const toDate = ref(formatGregorianDate(new Date(defaultTo.year, defaultTo.month - 1, defaultTo.day)))
const quickRange = ref("month")
const hoveredIdx = ref(null)

// ─── Standard Hours ──────────────────────────────────────────────────────────
const STANDARD_HOURS = 8 // fallback; could be fetched from employee shift

// ─── API Resource ────────────────────────────────────────────────────────────
const chartResource = createResource({
	url: "frappe.client.get_list",
	auto: false,
})

function fetchData() {
	if (!props.employee) return
	chartResource.fetch({
		doctype: "Employee Checkin",
		fields: ["name", "log_type", "time"],
		filters: [
			["employee", "=", props.employee],
			["time", ">=", fromDate.value + " 00:00:00"],
			["time", "<=", toDate.value + " 23:59:59"],
		],
		order_by: "time asc",
		limit_page_length: 500,
	})
}

// Fetch on mount and when dates change
watch(
	() => [props.employee, fromDate.value, toDate.value],
	() => fetchData(),
	{ immediate: Boolean(props.employee) },
)

// ─── Date Helpers ────────────────────────────────────────────────────────────
function formatGregorianDate(date) {
	const year = date.getFullYear()
	const month = String(date.getMonth() + 1).padStart(2, "0")
	const day = String(date.getDate()).padStart(2, "0")
	return `${year}-${month}-${day}`
}

function getJalaliDayNumber(gregDateStr) {
	const [y, m, d] = gregDateStr.split("-").map(Number)
	const jalali = gregorianToJalali(y, m, d)
	return jalali.day
}

function getJalaliFullDate(gregDateStr) {
	return formatJalaliDate(gregDateStr, { withWeekday: true })
}

// ─── Quick Range ─────────────────────────────────────────────────────────────
function setQuickRange(range) {
	quickRange.value = range
	const today = new Date()
	if (range === "7d") {
		const sevenDaysAgo = new Date(today)
		sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 6)
		fromDate.value = formatGregorianDate(sevenDaysAgo)
		toDate.value = formatGregorianDate(today)
	} else if (range === "month") {
		const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)
		const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0)
		fromDate.value = formatGregorianDate(firstDay)
		toDate.value = formatGregorianDate(lastDay)
	}
}

// ─── Date Change Handler ─────────────────────────────────────────────────────
function onDateChange() {
	// Validate max 90 days range
	const from = new Date(fromDate.value)
	const to = new Date(toDate.value)
	const diffDays = (to - from) / (1000 * 60 * 60 * 24)
	if (diffDays > 90) {
		// Auto-clamp to 90 days
		const clampedTo = new Date(from)
		clampedTo.setDate(clampedTo.getDate() + 90)
		toDate.value = formatGregorianDate(clampedTo)
	}
	// Swap if from > to
	if (fromDate.value > toDate.value) {
		;[fromDate.value, toDate.value] = [toDate.value, fromDate.value]
	}
	quickRange.value = null
}

// ─── Chart Data Processing ───────────────────────────────────────────────────
const chartData = computed(() => {
	const checkins = chartResource.data || []
	if (!checkins.length) return []

	// Group by date
	const byDate = {}
	for (const c of checkins) {
		const date = String(c.time || "").split(" ")[0]
		if (!date) continue
		if (!byDate[date]) byDate[date] = []
		byDate[date].push(c)
	}

	// Generate full date range
	const from = new Date(fromDate.value)
	const to = new Date(toDate.value)
	const allDates = []
	for (let d = new Date(from); d <= to; d.setDate(d.getDate() + 1)) {
		allDates.push(formatGregorianDate(d))
	}

	return allDates.map((date) => {
		const logs = byDate[date] || []
		const sorted = [...logs].sort((a, b) => String(a.time).localeCompare(String(b.time)))

		// Calculate worked hours by pairing IN/OUT
		let totalMinutes = 0
		let lastInTime = null
		for (const log of sorted) {
			if (log.log_type === "IN") {
				lastInTime = log.time
			} else if (log.log_type === "OUT" && lastInTime) {
				const inMs = new Date(lastInTime.replace(" ", "T")).getTime()
				const outMs = new Date(log.time.replace(" ", "T")).getTime()
				if (outMs > inMs) totalMinutes += (outMs - inMs) / 60000
				lastInTime = null
			}
		}

		const totalHours = totalMinutes / 60
		const standardMinutes = STANDARD_HOURS * 60

		let regularHours = 0
		let overtimeHours = 0
		let deficitHours = 0

		if (totalMinutes >= standardMinutes) {
			regularHours = STANDARD_HOURS
			overtimeHours = totalHours - STANDARD_HOURS
		} else {
			regularHours = totalHours
			deficitHours = STANDARD_HOURS - totalHours
		}

		const jalaliFull = getJalaliFullDate(date)
		const jalaliDay = getJalaliDayNumber(date)

		return {
			date,
			jalaliFull,
			jalaliDay,
			totalHours,
			regularHours,
			overtimeHours,
			deficitHours,
			ariaLabel: `${jalaliFull} - ${__("کل حضور")} ${formatHours(totalHours)} ${__("ساعت")}`,
		}
	})
})

// ─── Chart Dimensions ────────────────────────────────────────────────────────
const yMax = computed(() => {
	const maxVal = chartData.value.reduce((max, d) => {
		return Math.max(max, d.totalHours, STANDARD_HOURS + d.overtimeHours)
	}, STANDARD_HOURS + 2)
	return Math.ceil(maxVal)
})

const yAxisLabels = computed(() => {
	const labels = []
	const step = 2
	const count = Math.floor(yMax.value / step)
	for (let i = 0; i <= count; i++) {
		labels.unshift(toPersianDigits(i * step))
	}
	return labels
})

const gridLineCount = computed(() => Math.floor(yMax.value / 2))

const barWidth = computed(() => {
	const count = chartData.value.length
	if (count <= 7) return Math.min(48, Math.max(40, Math.floor((500 - count * 12) / count)))
	if (count <= 30) return Math.min(20, Math.max(12, Math.floor((500 - count * 4) / count)))
	return Math.min(12, Math.max(8, Math.floor((500 - count * 2) / count)))
})

// ─── Bar Height Calculation ──────────────────────────────────────────────────
function getBarPercent(hours) {
	if (!hours || hours <= 0) return 0
	const pct = (hours / yMax.value) * 100
	return Math.max(2, pct)
}

// ─── X-Axis Label Visibility ─────────────────────────────────────────────────
function shouldShowXLabel(idx) {
	const count = chartData.value.length
	if (count <= 14) return true
	if (count <= 31) return idx % 2 === 0
	return idx % 5 === 0
}

// ─── Format Helpers ──────────────────────────────────────────────────────────
function formatHours(hours) {
	if (!hours || hours <= 0) return toPersianDigits("0:00")
	const h = Math.floor(hours)
	const m = Math.round((hours - h) * 60)
	if (m === 60) return toPersianDigits(`${h + 1}:00`)
	return toPersianDigits(`${h}:${String(m).padStart(2, "0")}`)
}
</script>
