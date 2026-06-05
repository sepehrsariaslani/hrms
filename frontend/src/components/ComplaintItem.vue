<template>
	<ListItem
		:isTeamRequest="props.isTeamRequest"
		:employee="props.doc.raised_by"
		:employeeName="props.doc.employee_name"
	>
		<template #left>
			<ComplaintIcon class="h-5 w-5 text-gray-500" />
			<div class="flex flex-col items-start gap-1.5">
				<div class="text-base font-normal text-gray-800">
					{{ props.doc.subject }}
				</div>
				<div class="text-xs font-normal text-gray-500">
					<span>{{ props.doc.complaint_date }}</span>
					<span class="whitespace-pre"> &middot; </span>
					<span class="whitespace-nowrap">{{ feedbackLabel }}</span>
				</div>
			</div>
		</template>
		<template #right>
			<Badge
				variant="outline"
				:theme="colorMap[status] || 'gray'"
				:label="__(status, null, 'Employee Grievance')"
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
import ComplaintIcon from "@/components/icons/ComplaintIcon.vue"

const __ = inject("$translate")

const props = defineProps({
	doc: {
		type: Object,
	},
	isTeamRequest: {
		type: Boolean,
		default: false,
	},
	workflowStateField: {
		type: String,
		required: false,
	},
})

const status = computed(() => {
	if (props.workflowStateField) return props.doc[props.workflowStateField]
	return props.doc.status || "Open"
})
const feedbackLabel = computed(() => props.doc.feedback_type || props.doc.grievance_type)

const colorMap = {
	Open: "orange",
	Investigated: "blue",
	Resolved: "green",
	Invalid: "red",
}
</script>
