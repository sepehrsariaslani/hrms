<template>
	<ListItem
		:isTeamRequest="props.isTeamRequest"
		:employee="props.doc.employee"
		:employeeName="props.doc.employee_name"
	>
		<template #left>
			<AppraisalIcon class="h-5 w-5 text-gray-500" />
			<div class="flex flex-col items-start gap-1.5">
				<div class="text-base font-normal text-gray-800">
					{{ props.doc.appraisal_cycle }}
				</div>
				<div class="text-xs font-normal text-gray-500">
					<span>{{ props.doc.appraisal_dates }}</span>
					<span class="whitespace-pre"> &middot; </span>
					<span class="whitespace-nowrap">{{ __('Final Score') }}: {{ props.doc.formatted_final_score }}</span>
				</div>
			</div>
		</template>
		<template #right>
			<Badge
				variant="outline"
				:theme="colorMap[status] || 'gray'"
				:label="__(status)"
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
import AppraisalIcon from "@/components/icons/AppraisalIcon.vue"

const __ = inject("$translate")

const props = defineProps({
	doc: {
		type: Object,
	},
	isTeamRequest: {
		type: Boolean,
		default: false,
	},
})

const status = computed(() => props.doc.status || "Draft")

const colorMap = {
	Draft: "orange",
	Submitted: "green",
	Cancelled: "red",
}
</script>
