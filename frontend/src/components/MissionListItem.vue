<template>
	<router-link
		:to="{ name: 'MissionDetailView', params: { id: mission.id } }"
		class="block rounded-xl border border-slate-100 px-4 py-3 transition hover:border-amber-200 hover:bg-amber-50/40"
	>
		<div class="flex items-start justify-between gap-3">
			<div class="min-w-0">
				<p class="truncate text-sm font-semibold text-slate-900">{{ mission.title }}</p>
				<p class="mt-1 text-xs text-slate-500">
					{{ mission.destination || __('بدون مقصد') }}
					<span class="mx-1">•</span>
					{{ missionDateLabel }}
				</p>
			</div>
			<span
				class="rounded-full px-2.5 py-1 text-[11px] font-semibold"
				:class="statusStyle"
			>
				{{ mission.status }}
			</span>
		</div>

		<div class="mt-3 grid grid-cols-3 gap-2 text-[11px] text-slate-500">
			<div>
				<div>{{ __('هزینه ثبت‌شده') }}</div>
				<div class="mt-1 font-semibold text-slate-700">{{ formattedExpense }}</div>
			</div>
			<div>
				<div>{{ __('علی‌الحساب') }}</div>
				<div class="mt-1 font-semibold text-slate-700">{{ formattedAllowance }}</div>
			</div>
			<div>
				<div>{{ __('تعداد هزینه') }}</div>
				<div class="mt-1 font-semibold text-slate-700">
					{{ toPersianDigits((mission.expenses || []).length) }}
				</div>
			</div>
		</div>
	</router-link>
</template>

<script setup>
import { computed, inject } from "vue"

import { formatJalaliDateShort, toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")

const props = defineProps({
	mission: {
		type: Object,
		required: true,
	},
})

const statusClassMap = {
	"در انتظار تایید برنامه سفر": "bg-blue-100 text-blue-700",
	"تایید برنامه سفر": "bg-sky-100 text-sky-700",
	"در حال انجام سفر": "bg-amber-100 text-amber-700",
	"در انتظار تایید نهایی سرپرست": "bg-indigo-100 text-indigo-700",
	"نیازمند اصلاح": "bg-orange-100 text-orange-700",
	"تایید نهایی سرپرست": "bg-emerald-100 text-emerald-700",
	ردشده: "bg-rose-100 text-rose-700",
}

const statusStyle = computed(() => statusClassMap[props.mission.status] || "bg-slate-100 text-slate-700")

const missionDateLabel = computed(() => {
	if (props.mission.mission_type === "ساعتی") {
		const missionDate = formatJalaliDateShort(props.mission.hourly_date || props.mission.start_date)
		const fromTime = props.mission.hourly_from_time
			? toPersianDigits(String(props.mission.hourly_from_time).slice(0, 5))
			: "--:--"
		const toTime = props.mission.hourly_to_time
			? toPersianDigits(String(props.mission.hourly_to_time).slice(0, 5))
			: "--:--"
		return `${missionDate} (${fromTime} تا ${toTime})`
	}

	const start = props.mission.start_date
	const end = props.mission.end_date
	if (!start && !end) return __("بدون تاریخ")
	if (start && end && start !== end) {
		return `${formatJalaliDateShort(start)} تا ${formatJalaliDateShort(end)}`
	}
	return formatJalaliDateShort(start || end)
})

function formatAmount(value) {
	const rounded = Math.round(Number(value || 0))
	return `${toPersianDigits(new Intl.NumberFormat("en-US").format(rounded))} ${__("ریال")}`
}

const formattedExpense = computed(() => formatAmount(props.mission.total_expense))
const formattedAllowance = computed(() => formatAmount(props.mission.mission_allowance))
</script>
