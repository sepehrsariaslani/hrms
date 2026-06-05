<template>
	<ListItem :employee="props.doc.owner" :employeeName="props.doc.owner">
		<template #left>
			<EventIcon class="h-5 w-5 text-gray-500" />
			<div class="flex flex-col items-start gap-1.5 min-w-0">
				<div class="text-base font-normal text-gray-800 truncate max-w-[200px] sm:max-w-[320px]">
					{{ props.doc.subject || __("Untitled Event") }}
				</div>
				<div class="text-xs font-normal text-gray-500">
					<span>{{ eventDateLabel }}</span>
					<span v-if="eventTypeLabel" class="whitespace-pre"> &middot; </span>
					<span v-if="eventTypeLabel" class="whitespace-nowrap">{{ eventTypeLabel }}</span>
				</div>
			</div>
		</template>
		<template #right>
			<Badge
				variant="outline"
				:theme="badgeTheme"
				:label="badgeLabel"
				size="md"
			/>
			<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
		</template>
	</ListItem>
</template>

<script setup>
import { computed, inject } from "vue"
import { Badge, FeatherIcon } from "frappe-ui"

import ListItem from "@/components/ListItem.vue"
import EventIcon from "@/components/icons/EventIcon.vue"
import { formatJalaliDateShort, formatJalaliTime } from "@/utils/jalali"

const __ = inject("$translate")
const dayjs = inject("$dayjs")

const props = defineProps({
	doc: {
		type: Object,
	},
})

const eventTypeLabel = computed(() => {
	const type = props.doc?.event_type
	if (!type) return ""
	return __(type)
})

const eventDateLabel = computed(() => {
	const startsOn = props.doc?.starts_on
	if (!startsOn) return __("No date")

	const endsOn = props.doc?.ends_on
	const isAllDay = Boolean(props.doc?.all_day)
	const startDate = formatJalaliDateShort(startsOn)
	const endDate = endsOn ? formatJalaliDateShort(endsOn) : startDate

	if (isAllDay) {
		if (startDate === endDate) return `${startDate} (${__("All Day")})`
		return `${startDate} → ${endDate} (${__("All Day")})`
	}

	const startTime = formatJalaliTime(startsOn) || "--:--"
	const endTime = endsOn ? formatJalaliTime(endsOn) : ""
	if (startDate === endDate) {
		const timeLabel = endTime ? `${startTime} تا ${endTime}` : startTime
		return `${startDate} ${timeLabel}`
	}
	return `${startDate} ${startTime} → ${endDate}${endTime ? ` ${endTime}` : ""}`
})

const badgeLabel = computed(() => {
	const startsOn = props.doc?.starts_on
	if (!startsOn) return __("Planned")
	if (dayjs(startsOn).isBefore(dayjs(), "minute")) return __("Done")
	if (dayjs(startsOn).isSame(dayjs(), "day")) return __("Today")
	return __("Upcoming")
})

const badgeTheme = computed(() => {
	if (badgeLabel.value === __("Today")) return "orange"
	if (badgeLabel.value === __("Done")) return "gray"
	return "blue"
})
</script>
