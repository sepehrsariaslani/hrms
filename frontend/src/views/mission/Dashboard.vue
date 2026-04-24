<template>
	<BaseLayout :pageTitle="__('ماموریت‌های کاری')">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-4">
				<div class="grid grid-cols-2 gap-3 sm:grid-cols-5">
					<div class="rounded-xl border border-slate-100 bg-white p-4">
						<div class="text-xs text-slate-500">{{ __('کل ماموریت‌ها') }}</div>
						<div class="mt-1 text-lg font-bold text-slate-900">
							{{ toPersianDigits(summary.totalCount) }}
						</div>
					</div>
					<div class="rounded-xl border border-slate-100 bg-white p-4">
						<div class="text-xs text-slate-500">{{ __('ماموریت فعال') }}</div>
						<div class="mt-1 text-lg font-bold text-slate-900">
							{{ toPersianDigits(summary.activeCount) }}
						</div>
					</div>
					<div class="rounded-xl border border-slate-100 bg-white p-4">
						<div class="text-xs text-slate-500">{{ __('منتظر تایید من') }}</div>
						<div class="mt-1 text-lg font-bold text-slate-900">
							{{ toPersianDigits(pendingApprovals) }}
						</div>
					</div>
					<div class="rounded-xl border border-slate-100 bg-white p-4">
						<div class="text-xs text-slate-500">{{ __('جمع هزینه ثبت‌شده') }}</div>
						<div class="mt-1 text-sm font-bold text-slate-900">
							{{ formatAmount(summary.totalExpense) }}
						</div>
					</div>
					<div class="rounded-xl border border-slate-100 bg-white p-4">
						<div class="text-xs text-slate-500">{{ __('مانده علی‌الحساب') }}</div>
						<div
							class="mt-1 text-sm font-bold"
							:class="remainingAllowance >= 0 ? 'text-emerald-700' : 'text-rose-700'"
						>
							{{ formatSignedAmount(remainingAllowance) }}
						</div>
					</div>
				</div>

				<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
					<router-link :to="{ name: 'MissionFormView' }" v-slot="{ navigate }">
						<Button class="w-full py-5 text-base" @click="navigate">
							{{ __('ثبت ماموریت جدید') }}
						</Button>
					</router-link>
					<router-link :to="{ name: 'MissionListView' }" v-slot="{ navigate }">
						<Button variant="outline" class="w-full py-5 text-base" @click="navigate">
							{{ __('مشاهده فهرست ماموریت‌ها') }}
						</Button>
					</router-link>
				</div>

				<div class="rounded-xl border border-slate-100 bg-white p-4">
					<div class="mb-3 flex items-center justify-between">
						<div class="text-sm font-semibold text-slate-800">{{ __('ماموریت‌های اخیر') }}</div>
						<router-link
							:to="{ name: 'MissionListView' }"
							class="text-xs font-medium text-amber-700"
						>
							{{ __('نمایش همه') }}
						</router-link>
					</div>
					<div v-if="recentMissions.length" class="space-y-2">
						<MissionListItem
							v-for="mission in recentMissions"
							:key="mission.id"
							:mission="mission"
						/>
					</div>
					<EmptyState v-else :message="__('هنوز ماموریتی ثبت نشده است')" />
				</div>

			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import MissionListItem from "@/components/MissionListItem.vue"
import { missionTotals, myMissions, teamMissions } from "@/data/missions"
import { toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")

const summary = computed(() => missionTotals.value)
const remainingAllowance = computed(
	() => Number(summary.value.totalAllowance || 0) - Number(summary.value.totalExpense || 0)
)
const pendingApprovals = computed(
	() =>
		(teamMissions.value || []).filter((mission) =>
			["در انتظار تایید برنامه سفر", "در انتظار تایید نهایی سرپرست"].includes(mission.status)
		).length
)

const recentMissions = computed(() => myMissions.value.slice(0, 4))
function formatAmount(value) {
	const amount = Math.round(Number(value || 0))
	return `${toPersianDigits(new Intl.NumberFormat("en-US").format(amount))} ${__("ریال")}`
}

function formatSignedAmount(value) {
	const amount = Number(value || 0)
	const prefix = amount < 0 ? "-" : "+"
	return `${prefix}${formatAmount(Math.abs(amount))}`
}
</script>
