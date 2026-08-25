<template>
	<div ref="rootEl" class="relative w-full">
		<button
			type="button"
			class="w-full rounded border px-3 py-2.5 text-left text-sm transition-colors"
			:class="buttonClass"
			:disabled="isDisabled"
			@click="toggleCalendar"
		>
			<span :class="displayValue ? 'text-gray-900' : 'text-gray-400'">
				{{ displayValue || placeholder }}
			</span>
		</button>

		<div
			v-if="isOpen"
			class="absolute z-[1200] mt-2 w-full min-w-[270px] rounded-lg border border-gray-200 bg-white p-3 shadow-lg"
		>
			<div class="mb-3 flex items-center justify-between">
				<Button variant="ghost" icon="chevron-right" class="!px-2" @click="navigateMonth(-1)" />
				<span class="text-sm font-semibold text-gray-900">{{ monthTitle }}</span>
				<Button variant="ghost" icon="chevron-left" class="!px-2" @click="navigateMonth(1)" />
			</div>

			<div class="mb-2 grid grid-cols-7 text-center text-xs text-gray-500">
				<span v-for="day in weekDays" :key="day">{{ day }}</span>
			</div>

			<div class="grid grid-cols-7 gap-y-1 text-center">
				<div v-for="index in monthMeta.offset" :key="`blank-${index}`" />
				<button
					v-for="day in monthMeta.days"
					:key="day.key"
					type="button"
					class="mx-auto flex h-8 w-8 items-center justify-center rounded-full text-sm"
					:class="getDayClass(day)"
					:disabled="day.isDisabled"
					@click="selectDay(day)"
				>
					{{ toPersianDigits(day.jalaliDay) }}
				</button>
			</div>

			<div class="mt-3 flex items-center justify-between border-t border-gray-100 pt-2">
				<button
					type="button"
					class="text-xs font-medium text-amber-700"
					@click="goToToday"
				>
					امروز
				</button>
				<button
					type="button"
					class="text-xs font-medium text-gray-500"
					@click="isOpen = false"
				>
					بستن
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"
import {
	PERSIAN_MONTHS,
	formatGregorianDate,
	formatJalaliDate,
	getJalaliDaysInMonth,
	gregorianToJalali,
	jalaliToGregorian,
	toPersianDigits,
} from "@/utils/jalali"

const props = defineProps({
	modelValue: {
		type: String,
		default: "",
	},
	placeholder: {
		type: String,
		default: "",
	},
	disabled: {
		type: [Boolean, Number],
		default: false,
	},
	minDate: {
		type: String,
		default: "",
	},
	maxDate: {
		type: String,
		default: "",
	},
})

const emit = defineEmits(["update:modelValue", "change"])

const rootEl = ref(null)
const isOpen = ref(false)
const weekDays = ["ش", "ی", "د", "س", "چ", "پ", "ج"]

const isDisabled = computed(() => Boolean(props.disabled))
const displayValue = computed(() => formatJalaliDate(normalizeDateValue(props.modelValue)))

const buttonClass = computed(() => {
	if (isDisabled.value) return "bg-gray-100 text-gray-500 cursor-not-allowed border-gray-200"
	return "bg-white text-gray-900 border-gray-300 hover:border-gray-400"
})

const activeJalaliMonth = ref(getJalaliMonthFromValue(props.modelValue))

const monthTitle = computed(() => {
	return `${PERSIAN_MONTHS[activeJalaliMonth.value.month - 1]} ${toPersianDigits(
		activeJalaliMonth.value.year
	)}`
})

const monthMeta = computed(() => {
	const year = activeJalaliMonth.value.year
	const month = activeJalaliMonth.value.month
	const firstGregorian = jalaliToGregorian(year, month, 1)
	const firstDate = new Date(
		firstGregorian.year,
		firstGregorian.month - 1,
		firstGregorian.day
	)
	const offset = (firstDate.getDay() + 1) % 7
	const daysInMonth = getJalaliDaysInMonth(year, month)
	const days = []

	for (let day = 1; day <= daysInMonth; day++) {
		const gregorian = jalaliToGregorian(year, month, day)
		const gregorianDate = formatGregorianDate(
			new Date(gregorian.year, gregorian.month - 1, gregorian.day)
		)
		days.push({
			key: `${year}-${month}-${day}`,
			jalaliDay: day,
			gregorianDate,
			isToday: gregorianDate === formatGregorianDate(new Date()),
			isSelected: gregorianDate === normalizeDateValue(props.modelValue),
			isDisabled: isOutOfRange(gregorianDate),
		})
	}

	return { offset, days }
})

watch(
	() => props.modelValue,
	(value) => {
		if (!value) return
		activeJalaliMonth.value = getJalaliMonthFromValue(value)
	}
)

function toggleCalendar() {
	if (isDisabled.value) return
	isOpen.value = !isOpen.value
}

function navigateMonth(direction) {
	let month = activeJalaliMonth.value.month + direction
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

function selectDay(day) {
	if (day.isDisabled) return
	emit("update:modelValue", day.gregorianDate)
	emit("change", day.gregorianDate)
	isOpen.value = false
}

function goToToday() {
	const today = formatGregorianDate(new Date())
	const todayMonth = getJalaliMonthFromValue(today)
	activeJalaliMonth.value = todayMonth
	if (!isOutOfRange(today)) {
		emit("update:modelValue", today)
		emit("change", today)
	}
	isOpen.value = false
}

function getDayClass(day) {
	if (day.isSelected) return "bg-gray-900 text-white"
	if (day.isDisabled) return "text-gray-300 cursor-not-allowed"
	if (day.isToday) return "ring-1 ring-amber-500 text-amber-700"
	return "text-gray-700 hover:bg-gray-100"
}

function normalizeDateValue(value) {
	if (!value) return ""
	if (typeof value === "string") return value.slice(0, 10)
	return ""
}

function getJalaliMonthFromValue(value) {
	const normalizedValue = normalizeDateValue(value) || formatGregorianDate(new Date())
	const [year, month, day] = normalizedValue.split("-").map(Number)
	const jalali = gregorianToJalali(year, month, day)
	return { year: jalali.year, month: jalali.month }
}

function isOutOfRange(dateValue) {
	const minDate = normalizeDateValue(props.minDate)
	const maxDate = normalizeDateValue(props.maxDate)
	if (minDate && dateValue < minDate) return true
	if (maxDate && dateValue > maxDate) return true
	return false
}

function handleClickOutside(event) {
	if (!rootEl.value || rootEl.value.contains(event.target)) return
	isOpen.value = false
}

onMounted(() => {
	document.addEventListener("mousedown", handleClickOutside)
})

onBeforeUnmount(() => {
	document.removeEventListener("mousedown", handleClickOutside)
})
</script>
