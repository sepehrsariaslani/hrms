<template>
	<ListItem
		:isTeamRequest="props.isTeamRequest"
		:employee="props.doc.employee"
		:employeeName="props.doc.employee_name"
	>
		<template #left>
			<LeaveIcon class="h-5 w-5 text-gray-500" />
			<div class="flex flex-col items-start gap-1.5">
				<div class="text-base font-normal text-gray-800">
					{{ leaveTypeLabel }}
				</div>
				<div class="text-xs font-normal text-gray-500">
					<span>{{ props.doc.leave_dates || getLeaveDates(props.doc) }}</span>
					<span class="whitespace-pre"> &middot; </span>
					<span class="whitespace-nowrap">{{ leaveDurationText }}</span>
				</div>
			</div>
		</template>
		<template #right>
			<Badge variant="outline" :theme="colorMap[status]" :label="__(status, null, 'Leave Application')" size="md" />
			<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
		</template>
	</ListItem>
</template>

<script setup>
import { computed, inject } from "vue"
import { FeatherIcon, Badge } from "frappe-ui"

import ListItem from "@/components/ListItem.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import { getLeaveDates, getLeaveDurationText } from "@/data/leaves"
import { localizeLeaveType } from "@/utils/leaveTypeLabels"

const __ = inject("$translate", (text) => text)

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
	return props.workflowStateField ? props.doc[props.workflowStateField] : props.doc.status
})

const isHourlyLeave = computed(() => props.doc.leave_duration_mode === "ساعتی")

const leaveTypeLabel = computed(() => localizeLeaveType(props.doc.leave_type))

const leaveDurationText = computed(() => {
	if (props.doc.leave_duration_text) return props.doc.leave_duration_text
	const text = getLeaveDurationText(props.doc)
	if (!isHourlyLeave.value) return text
	return __(text)
})

const colorMap = {
	Approved: "green",
	Rejected: "red",
	Open: "orange",
}
</script>
