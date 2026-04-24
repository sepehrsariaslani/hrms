<template>
	<div class="flex flex-col bg-white rounded mt-5 overflow-auto" v-if="props.items?.length">
		<div
			v-for="group in displayedGroups"
			:key="group.key"
			class="border-b last:border-b-0"
		>
			<div
				v-if="props.groupBy !== 'none'"
				class="px-3.5 py-2 text-xs font-semibold tracking-wide text-gray-500 bg-gray-50"
			>
				{{ group.label }}
			</div>
			<div
				class="flex flex-row p-3.5 items-center justify-between border-t cursor-pointer first:border-t-0"
				v-for="link in group.items"
				:key="`${group.key}-${link.name}`"
				@click="openRequestModal(link)"
			>
				<component
					:is="props.component || link.component"
					:doc="link"
					:workflowStateField="link.workflow_state_field"
					:isTeamRequest="props.teamRequests"
				/>
			</div>
		</div>

		<div v-if="hasMore" class="p-3 flex justify-center">
			<Button variant="outline" @click="loadMore">
				{{ __("نمایش بیشتر +") }}
			</Button>
		</div>

		<router-link
			v-if="props.addListButton"
			:to="{ name: props.listButtonRoute }"
			v-slot="{ navigate }"
		>
			<Button
				variant="ghost"
				@click="navigate"
				class="w-full !text-gray-600 py-6 text-sm border-none bg-white hover:bg-white"
			>
				{{ __("View List") }}
			</Button>
		</router-link>
	</div>
	<EmptyState :message="emptyStateMessage || __('You have no requests')" v-else />

	<ion-modal
		ref="modal"
		:is-open="isRequestModalOpen"
		@didDismiss="closeRequestModal"
		:initial-breakpoint="1"
		:breakpoints="[0, 1]"
	>
		<RequestActionSheet
			:fields="fieldsMap[selectedRequest?.doctype]" 
			v-model="selectedRequest"
		/>
	</ion-modal>
</template>

<script setup>
import { computed, ref, inject, watch } from "vue"
import { IonModal } from "@ionic/vue"
import RequestActionSheet from "@/components/RequestActionSheet.vue"

import {
	LEAVE_FIELDS,
	EXPENSE_CLAIM_FIELDS,
	ATTENDANCE_REQUEST_FIELDS,
	COMPLAINT_FIELDS,
	SHIFT_REQUEST_FIELDS,
	SHIFT_FIELDS,
} from "@/data/config/requestSummaryFields"

const __ = inject("$translate")
const props = defineProps({
	component: {
		type: Object,
	},
	items: {
		type: Array,
	},
	teamRequests: {
		type: Boolean,
		default: false,
	},
	addListButton: {
		type: Boolean,
		default: false,
	},
	listButtonRoute: {
		type: String,
		default: "",
	},
	emptyStateMessage: {
		type: String,
		default: "",
	},
	groupBy: {
		type: String,
		default: "none",
	},
})

const fieldsMap = {
	"Leave Application": LEAVE_FIELDS,
	"Expense Claim": EXPENSE_CLAIM_FIELDS,
	"Attendance Request": ATTENDANCE_REQUEST_FIELDS,
	"Employee Grievance": COMPLAINT_FIELDS,
	"Shift Request": SHIFT_REQUEST_FIELDS,
	"Shift Assignment": SHIFT_FIELDS,
}

const isRequestModalOpen = ref(false)
const selectedRequest = ref(null)
const PAGE_SIZE = 5
const visibleCount = ref(PAGE_SIZE)

const groupedItems = computed(() => {
	const items = props.items || []
	if (props.groupBy === "none") {
		return [{ key: "all", label: __("All Requests"), items }]
	}

	const groups = new Map()
	items.forEach((item) => {
		const groupValue = getGroupValue(item)
		if (!groups.has(groupValue)) {
			groups.set(groupValue, [])
		}
		groups.get(groupValue).push(item)
	})

	return Array.from(groups.entries()).map(([key, items]) => ({
		key,
		label: key,
		items,
	}))
})

const displayedGroups = computed(() => {
	let remaining = visibleCount.value
	const visibleGroups = []

	for (const group of groupedItems.value) {
		if (remaining <= 0) break
		const items = group.items.slice(0, remaining)
		if (items.length) {
			visibleGroups.push({
				...group,
				items,
			})
			remaining -= items.length
		}
	}

	return visibleGroups
})

const hasMore = computed(() => (props.items?.length || 0) > visibleCount.value)

watch(
	() => [props.items?.length || 0, props.groupBy],
	() => {
		visibleCount.value = PAGE_SIZE
	}
)

function loadMore() {
	visibleCount.value += PAGE_SIZE
}

function getGroupValue(item) {
	if (props.groupBy === "doctype") {
		return __(item?.doctype || "Other")
	}
	if (props.groupBy === "status") {
		return __(
			item?.[item?.workflow_state_field] ||
				item?.status ||
				item?.approval_status ||
				item?.review_status ||
				"Unknown"
		)
	}
	return __("Other")
}

const openRequestModal = async (request) => {
	selectedRequest.value = request
	isRequestModalOpen.value = true
}

const closeRequestModal = async () => {
	isRequestModalOpen.value = false
	selectedRequest.value = null
}
</script>
