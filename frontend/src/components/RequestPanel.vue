<template>
	<div class="w-full">
		<TabButtons
			:buttons="TAB_BUTTONS"
			v-model="activeTab"
		/>
		<div class="mt-3 flex items-center gap-2 text-sm text-gray-600">
			<span>{{ __("Group By") }}</span>
			<select
				v-model="groupBy"
				class="rounded-md border border-gray-200 bg-white px-2 py-1 text-sm text-gray-700"
			>
				<option
					v-for="option in GROUP_OPTIONS"
					:key="option.value"
					:value="option.value"
				>
					{{ option.label }}
				</option>
			</select>
		</div>

		<RequestList
			v-if="activeTab == 'My Requests'"
			:items="myRequests"
			:groupBy="groupBy"
		/>
		<RequestList
			v-else-if="activeTab == 'Team Requests'"
			:items="teamRequests"
			:teamRequests="true"
			:groupBy="groupBy"
		/>
	</div>
</template>

<script setup>
import { ref, inject, onMounted, computed, markRaw } from "vue"

import TabButtons from "@/components/TabButtons.vue"
import RequestList from "@/components/RequestList.vue"

import { myAttendanceRequests, myShiftRequests, teamShiftRequests, teamAttendanceRequests } from "@/data/attendance"
import { myClaims, teamClaims } from "@/data/claims"
import { myComplaints, teamComplaints } from "@/data/complaints"
import { myLeaves, teamLeaves } from "@/data/leaves"

import AttendanceRequestItem from "@/components/AttendanceRequestItem.vue"
import ComplaintItem from "@/components/ComplaintItem.vue"
import ExpenseClaimItem from "@/components/ExpenseClaimItem.vue"
import LeaveRequestItem from "@/components/LeaveRequestItem.vue"
import ShiftRequestItem from "@/components/ShiftRequestItem.vue"

import { useListUpdate } from "@/composables/realtime"

const __ = inject("$translate")
const activeTab = ref("My Requests")
const groupBy = ref("none")
const socket = inject("$socket")

const TAB_BUTTONS = ["My Requests", "Team Requests"] // __("My Requests"), __("Team Requests")
const GROUP_OPTIONS = [
	{ label: __("None"), value: "none" },
	{ label: __("Request Type"), value: "doctype" },
	{ label: __("Status"), value: "status" },
]

const myRequests = computed(() =>
	updateRequestDetails(myLeaves, myClaims, myShiftRequests, myAttendanceRequests, myComplaints)
)

const teamRequests = computed(() =>
	updateRequestDetails(
		teamLeaves,
		teamClaims,
		teamShiftRequests,
		teamAttendanceRequests,
		teamComplaints
	)
)

function updateRequestDetails(leaves, claims, shiftRequests, attendanceRequests, complaints) {
	const requests = [leaves, claims, shiftRequests, attendanceRequests, complaints].reduce(
		(acc, resource) => acc.concat(resource?.data || []),
		[]
	)

	const componentMap = {
		"Leave Application": LeaveRequestItem,
		"Expense Claim": ExpenseClaimItem,
		"Shift Request": ShiftRequestItem,
		"Attendance Request": AttendanceRequestItem,
		"Employee Grievance": ComplaintItem,
	}
	requests.forEach((request) => {
		request.component = markRaw(componentMap[request.doctype])
	})

	return getSortedRequests(requests)
}

function getSortedRequests(list) {
	// Show newest requests first by last update timestamp.
	return list
		.sort((a, b) => {
			return new Date(getLastUpdatedAt(b)) - new Date(getLastUpdatedAt(a))
		})
}

function getLastUpdatedAt(request) {
	return (
		request.modified ||
		request.creation ||
		request.posting_date ||
		request.from_date ||
		"1970-01-01"
	)
}

onMounted(() => {
	useListUpdate(socket, "Leave Application", () => teamLeaves.reload())
	useListUpdate(socket, "Expense Claim", () => teamClaims.reload())
	useListUpdate(socket, "Shift Request", () => teamShiftRequests.reload())
	useListUpdate(socket, "Attendance Request", () => teamAttendanceRequests.reload())
	useListUpdate(socket, "Employee Grievance", () => {
		myComplaints.reload()
		teamComplaints.reload()
	})
})
</script>
