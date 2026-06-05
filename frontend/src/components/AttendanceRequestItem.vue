<template>
	<ListItem
		:isTeamRequest="props.isTeamRequest"
		:employee="props.doc.employee"
		:employeeName="props.doc.employee_name"
		>
		<template #left>
			<AttendanceIcon class="h-5 w-5 text-gray-500" />
			<div class="flex flex-col items-start gap-1.5">
				<div class="text-base font-normal text-gray-800">
					{{ title }}
				</div>
				<div class="text-xs font-normal text-gray-500">
					<template v-if="isCheckinRequest">
						<span>{{ props.doc.attendance_dates || getDates(props.doc) }}</span>
						<span class="whitespace-pre"> &middot; </span>
						<span class="whitespace-nowrap">{{ props.doc.formatted_request_time || "--:--" }}</span>
					</template>
					<template v-else>
						<span>{{ props.doc.attendance_dates || getDates(props.doc) }}</span>
					</template>
					<span v-if="props.doc.to_date && !isCheckinRequest">
						<span class="whitespace-pre"> &middot; </span>
						<span class="whitespace-nowrap">{{ __("{0}d", [props.doc.total_attendance_days]) }}</span>
					</span>
				</div>
			</div>
		</template>
		<template #right>
			<Badge variant="outline" :theme="colorMap[status] || 'gray'" :label="__(status)" size="md" />
			<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
		</template>
	</ListItem>
</template>

<script setup>
import { computed } from "vue"
import { Badge, FeatherIcon } from "frappe-ui"

import ListItem from "@/components/ListItem.vue"
import AttendanceIcon from "@/components/icons/AttendanceIcon.vue"
import { getDates } from "@/data/attendance"

const props = defineProps({
	doc: {
		type: Object,
	},
	workflowStateField: {
		type: String,
		required: false,
	},
})

const isCheckinRequest = computed(() => props.doc?.request_mode === "Checkin Request")

const title = computed(() => {
	if (!isCheckinRequest.value) return props.doc.reason
	const logType = props.doc.final_log_type || props.doc.requested_log_type || "IN"
	return logType === "OUT" ? "درخواست خروج" : "درخواست ورود"
})

const status = computed(() => {
	if (isCheckinRequest.value) {
		return props.doc.review_status || (props.doc.docstatus ? "Submitted" : "Draft")
	}
	if (props.workflowStateField) return props.doc[props.workflowStateField]
	return props.doc.docstatus ? "Submitted" : "Draft"
})

const colorMap = {
	Draft: "gray",
	Submitted: "blue",
	Pending: "orange",
	Approved: "green",
	Rejected: "red",
}
</script>
