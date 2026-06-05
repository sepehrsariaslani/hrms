<template>
	<BaseLayout :pageTitle="__('فهرست ماموریت‌ها')">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-4">
				<div class="rounded-xl border border-slate-100 bg-white p-4">
					<div class="mb-3 grid grid-cols-2 gap-2 rounded-xl bg-slate-100 p-1 text-xs font-semibold">
						<button
							type="button"
							class="rounded-lg px-3 py-2 transition"
							:class="selectedScope === 'mine' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'"
							@click="selectedScope = 'mine'"
						>
							{{ __('ماموریت‌های من') }}
						</button>
						<button
							type="button"
							class="rounded-lg px-3 py-2 transition"
							:class="selectedScope === 'approval' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'"
							@click="selectedScope = 'approval'"
						>
							{{ __('برای تایید من') }}
						</button>
					</div>
					<div class="mb-3 text-xs text-slate-500">
						{{
							selectedScope === "mine"
								? __("در این بخش می‌توانید سفرهای خودتان را ثبت، ویرایش و پیگیری کنید.")
								: __("در این بخش سفرهای کارمندان زیرمجموعه برای بررسی سرپرست نمایش داده می‌شود.")
						}}
					</div>
					<div class="grid gap-3 sm:grid-cols-3">
						<div class="sm:col-span-2">
							<label class="mb-1 block text-xs text-slate-500">{{ __('جستجو') }}</label>
							<input
								v-model="searchTerm"
								type="text"
								:placeholder="__('عنوان، مقصد یا هدف ماموریت')"
								class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-amber-400"
							/>
						</div>
						<div>
							<label class="mb-1 block text-xs text-slate-500">{{ __('وضعیت') }}</label>
							<SearchableDropdown
								v-model="selectedStatus"
								:options="statusOptions"
								:placeholder="__('فیلتر وضعیت')"
							/>
						</div>
					</div>
				</div>

				<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
					<router-link :to="{ name: 'MissionFormView' }" v-slot="{ navigate }">
						<Button class="w-full py-5 text-base" @click="navigate">
							{{ __('ثبت ماموریت جدید') }}
						</Button>
					</router-link>
					<router-link :to="{ name: 'MissionsDashboard' }" v-slot="{ navigate }">
						<Button variant="outline" class="w-full py-5 text-base" @click="navigate">
							{{ __('بازگشت به داشبورد ماموریت') }}
						</Button>
					</router-link>
				</div>

				<div class="rounded-xl border border-slate-100 bg-white p-4">
					<div class="mb-3 text-xs text-slate-500">
						{{ __('تعداد نتایج') }}: {{ toPersianDigits(filteredMissions.length) }}
					</div>
					<div v-if="filteredMissions.length" class="space-y-2">
						<MissionListItem
							v-for="mission in filteredMissions"
							:key="mission.id"
							:mission="mission"
						/>
					</div>
					<EmptyState
						v-else
						:message="
							selectedScope === 'approval'
								? __('در حال حاضر سفری برای تایید شما وجود ندارد.')
								: __('ماموریتی مطابق فیلتر انتخابی پیدا نشد')
						"
					/>
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import MissionListItem from "@/components/MissionListItem.vue"
import SearchableDropdown from "@/components/SearchableDropdown.vue"
import { missionStatusOptions, myMissions, teamMissions } from "@/data/missions"
import { toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")
const searchTerm = ref("")
const selectedStatus = ref("all")
const selectedScope = ref("mine")
const statusOptions = [
	{ label: __("همه وضعیت‌ها"), value: "all" },
	...missionStatusOptions.map((status) => ({ label: status, value: status })),
]

const scopedMissions = computed(() =>
	selectedScope.value === "approval" ? teamMissions.value : myMissions.value
)

const filteredMissions = computed(() => {
	const keyword = searchTerm.value.trim().toLowerCase()

	return scopedMissions.value.filter((mission) => {
		if (selectedStatus.value !== "all" && mission.status !== selectedStatus.value) {
			return false
		}

		if (!keyword) return true

		const haystack = [mission.title, mission.destination, mission.purpose, mission.notes]
			.filter(Boolean)
			.join(" ")
			.toLowerCase()

		return haystack.includes(keyword)
	})
})
</script>
