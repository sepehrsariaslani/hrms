<template>
	<BaseLayout :pageTitle="__('رویدادها')">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-4">
				<div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
					<div class="rounded-xl border border-slate-100 bg-white p-4">
						<div class="text-xs text-slate-500">{{ __("کل رویدادها") }}</div>
						<div class="mt-1 text-lg font-bold text-slate-900">
							{{ toPersianDigits(totalEvents) }}
						</div>
					</div>
					<div class="rounded-xl border border-slate-100 bg-white p-4">
						<div class="text-xs text-slate-500">{{ __("رویدادهای آینده") }}</div>
						<div class="mt-1 text-lg font-bold text-slate-900">
							{{ toPersianDigits(upcomingCount) }}
						</div>
					</div>
					<div class="rounded-xl border border-slate-100 bg-white p-4">
						<div class="text-xs text-slate-500">{{ __("امروز") }}</div>
						<div class="mt-1 text-lg font-bold text-slate-900">
							{{ toPersianDigits(todayCount) }}
						</div>
					</div>
					<div class="rounded-xl border border-slate-100 bg-white p-4">
						<div class="text-xs text-slate-500">{{ __("این هفته") }}</div>
						<div class="mt-1 text-lg font-bold text-slate-900">
							{{ toPersianDigits(thisWeekCount) }}
						</div>
					</div>
				</div>

				<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
					<router-link :to="{ name: 'EventFormView' }" v-slot="{ navigate }">
						<Button class="w-full py-5 text-base" @click="navigate">
							{{ __("ثبت رویداد جدید") }}
						</Button>
					</router-link>
					<router-link :to="{ name: 'EventListView' }" v-slot="{ navigate }">
						<Button variant="outline" class="w-full py-5 text-base" @click="navigate">
							{{ __("مشاهده فهرست رویدادها") }}
						</Button>
					</router-link>
				</div>

				<div class="rounded-xl border border-slate-100 bg-white p-4">
					<div class="mb-3 flex items-center justify-between">
						<div class="text-sm font-semibold text-slate-800">{{ __("رویدادهای آینده") }}</div>
						<router-link :to="{ name: 'EventListView' }" class="text-xs font-medium text-amber-700">
							{{ __("نمایش همه") }}
						</router-link>
					</div>

					<div v-if="upcomingRows.length" class="space-y-2">
						<router-link
							v-for="event in upcomingRows"
							:key="event.name"
							:to="{ name: 'EventDetailView', params: { id: event.name } }"
							class="block rounded-xl border border-slate-100 px-4 py-3 transition hover:border-amber-200 hover:bg-amber-50/40"
						>
							<div class="flex items-start justify-between gap-3">
								<div class="min-w-0">
									<p class="truncate text-sm font-semibold text-slate-900">
										{{ event.subject || __("رویداد بدون عنوان") }}
									</p>
									<p class="mt-1 text-xs text-slate-500">
										{{ eventDateLabel(event) }}
									</p>
								</div>
								<span class="rounded-full bg-blue-50 px-2.5 py-1 text-[11px] font-semibold text-blue-700">
									{{ __(event.event_type || "Private") }}
								</span>
							</div>
							<p v-if="event.location" class="mt-2 text-[11px] text-slate-500">
								{{ __("Location") }}: {{ event.location }}
							</p>
						</router-link>
					</div>
					<EmptyState v-else :message="__('رویدادی برای نمایش وجود ندارد')" />
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, onMounted } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import {
	myEvents,
	myEventsResource,
	upcomingEvents,
	thisWeekEventsCount,
	todayEventsCount,
} from "@/data/events"
import { formatJalaliDateShort, formatJalaliTime, toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")

const totalEvents = computed(() => myEvents.value.length)
const upcomingCount = computed(() => upcomingEvents.value.length)
const todayCount = computed(() => todayEventsCount.value)
const thisWeekCount = computed(() => thisWeekEventsCount.value)
const upcomingRows = computed(() => upcomingEvents.value.slice(0, 8))

onMounted(() => {
	myEventsResource.reload()
})

function eventDateLabel(event) {
	const startsOn = event?.starts_on
	if (!startsOn) return __("No date")

	const endsOn = event?.ends_on || startsOn
	const startDate = formatJalaliDateShort(startsOn)
	const endDate = formatJalaliDateShort(endsOn)
	const startTime = formatJalaliTime(startsOn)
	const endTime = formatJalaliTime(endsOn)

	if (event?.all_day) {
		if (startDate === endDate) return `${startDate} (${__("All Day")})`
		return `${startDate} → ${endDate} (${__("All Day")})`
	}

	if (startDate === endDate) return `${startDate} ${startTime}${endTime ? ` تا ${endTime}` : ""}`
	return `${startDate} ${startTime} → ${endDate}${endTime ? ` ${endTime}` : ""}`
}
</script>
