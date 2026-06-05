<template>
	<component
		v-if="!props.hideHeader"
		:is="props.embedded ? 'div' : IonHeader"
		:class="props.embedded ? '' : 'ion-no-border'"
	>
		<div class="w-full max-w-7xl mx-auto" :class="props.embedded ? 'px-0' : 'px-0 md:px-4'">
			<div
				class="flex flex-row items-center justify-between"
				:class="
					props.embedded
						? 'sticky top-0 z-10 rounded-xl border border-slate-200 bg-white/95 px-3 py-3 backdrop-blur md:px-4 md:py-4'
						: 'bg-white shadow-sm py-4 px-3 border-b md:rounded-b-xl'
				"
				data-tour="list-header"
			>
				<div class="flex flex-row items-center" data-tour="list-header-title">
					<Button variant="ghost" class="!px-1 mr-1 hover:bg-white" @click="router.back()">
						<FeatherIcon name="chevron-left" class="h-5 w-5" />
					</Button>
					<h2 class="text-xl font-semibold text-gray-900">{{ pageTitle }}</h2>
				</div>

				<div class="flex flex-row gap-2">
					<Button
						id="show-filter-modal"
						icon="filter"
						variant="subtle"
						data-tour="list-filter-button"
						:class="[
							areFiltersApplied
								? '!border !border-gray-800 !bg-white !text-gray-900 !font-semibold'
								: '',
						]"
					/>
					<router-link
						v-if="canCreate && props.doctype != 'Employee Checkin'"
						:to="{ name: formViewRoute }"
						v-slot="{ navigate }"
					>
						<Button variant="solid" class="mr-2" data-tour="list-new-button" @click="navigate">
							<template #prefix>
								<FeatherIcon name="plus" class="w-4" />
							</template>
							{{ __("New", null, props.doctype) }}
						</Button>
					</router-link>
				</div>
			</div>
		</div>
	</component>

	<component :is="props.embedded ? 'div' : IonContent">
		<ion-refresher v-if="!props.embedded" slot="fixed" @ionRefresh="handleRefresh($event)">
			<ion-refresher-content></ion-refresher-content>
		</ion-refresher>

		<div
			class="flex flex-col items-center w-full max-w-7xl mx-auto"
			:class="props.embedded ? 'mt-4 mb-7 px-0' : 'mb-7 p-4 h-full overflow-y-auto'"
			ref="scrollContainer"
			@scroll="() => handleScroll()"
		>
			<div class="w-full">
				<TabButtons
					v-if="props.tabButtons && !props.hideTabs"
					class="mt-5"
					data-tour="list-tabs"
					:buttons="props.tabButtons"
					v-model="activeTab"
				/>

				<div
					class="flex flex-col bg-white rounded mt-5"
					data-tour="records-list"
					v-if="!documents.loading && documents.data?.length"
				>
					<div
						class="p-3.5 items-center justify-between border-b cursor-pointer"
						v-for="link in documents.data"
						:key="link.name"
					>
						<component
							v-if="props.doctype === 'Employee Checkin'"
							:is="listItemComponent[doctype]"
							:doc="link"
							:isTeamRequest="isTeamRequest"
							:workflowStateField="workflowStateField"
							@click="openRequestModal(link)"
						/>
						<router-link
							v-else
							:to="{ name: detailViewRoute, params: { id: link.name } }"
							v-slot="{ navigate }"
						>
							<component
								:is="listItemComponent[doctype]"
								:doc="link"
								:isTeamRequest="isTeamRequest"
								:workflowStateField="workflowStateField"
								@click="navigate"
							/>
						</router-link>
					</div>
				</div>
				<EmptyState
					:message="__('No {0} found', [props.doctype?.toLowerCase()])"
					v-else-if="!documents.loading"
				/>

				<!-- Loading Indicator -->
				<div v-if="documents.loading" class="flex mt-2 items-center justify-center">
					<LoadingIndicator class="w-8 h-8 text-gray-800" />
				</div>
			</div>
		</div>

		<CustomIonModal v-if="!props.hideHeader" trigger="show-filter-modal">
			<!-- Filter Action Sheet -->
			<template #actionSheet>
				<ListFiltersActionSheet
					:filterConfig="filterConfig"
					@applyFilters="applyFilters"
					@clearFilters="clearFilters"
					v-model:filters="filterMap"
				/>
			</template>
		</CustomIonModal>
	</component>

	<ion-modal
		ref="modal"
		:is-open="isRequestModalOpen"
		@didDismiss="closeRequestModal"
		:initial-breakpoint="1"
		:breakpoints="[0, 1]"
	>
		<RequestActionSheet
			:fields="EMPLOYEE_CHECKIN_FIELDS"
			:showOpenForm="false"
			v-model="selectedRequest"
		/>
	</ion-modal>
</template>

<script setup>
import { useRouter } from "vue-router"
import { inject, ref, markRaw, watch, computed, reactive, onMounted } from "vue"
import {
	modalController,
	IonHeader,
	IonContent,
	IonModal,
	IonRefresher,
	IonRefresherContent,
} from "@ionic/vue"

import { FeatherIcon, createResource, LoadingIndicator, debounce } from "frappe-ui"

import TabButtons from "@/components/TabButtons.vue"
import EmployeeCheckinItem from "@/components/EmployeeCheckinItem.vue"
import AttendanceRequestItem from "@/components/AttendanceRequestItem.vue"
import ShiftRequestItem from "@/components/ShiftRequestItem.vue"
import ShiftAssignmentItem from "@/components/ShiftAssignmentItem.vue"
import LeaveRequestItem from "@/components/LeaveRequestItem.vue"
import ExpenseClaimItem from "@/components/ExpenseClaimItem.vue"
import EmployeeAdvanceItem from "@/components/EmployeeAdvanceItem.vue"
import ComplaintItem from "@/components/ComplaintItem.vue"
import EventItem from "@/components/EventItem.vue"
import ListFiltersActionSheet from "@/components/ListFiltersActionSheet.vue"
import CustomIonModal from "@/components/CustomIonModal.vue"
import RequestActionSheet from "@/components/RequestActionSheet.vue"
import { EMPLOYEE_CHECKIN_FIELDS } from "@/data/config/requestSummaryFields"
import { formatJalaliTime } from "@/utils/jalali"

import useWorkflow from "@/composables/workflow"
import { useListUpdate } from "@/composables/realtime"

const __ = inject("$translate")
const props = defineProps({
	doctype: {
		type: String,
		required: true,
	},
	fields: {
		type: Array,
		required: true,
	},
	groupBy: {
		type: String,
		required: false,
	},
	filterConfig: {
		type: Array,
		required: true,
	},
	tabButtons: {
		type: Array,
		required: false,
	},
	pageTitle: {
		type: String,
		required: true,
	},
	embedded: {
		type: Boolean,
		required: false,
		default: false,
	},
	forceShowCreateButton: {
		type: Boolean,
		required: false,
		default: false,
	},
	hideHeader: {
		type: Boolean,
		required: false,
		default: false,
	},
	hideTabs: {
		type: Boolean,
		required: false,
		default: false,
	},
})

const getButtonKey = (tab) => tab?.key ?? tab

const listItemComponent = {
	"Employee Checkin": markRaw(EmployeeCheckinItem),
	"Attendance Request": markRaw(AttendanceRequestItem),
	"Shift Request": markRaw(ShiftRequestItem),
	"Shift Assignment": markRaw(ShiftAssignmentItem),
	"Leave Application": markRaw(LeaveRequestItem),
	"Expense Claim": markRaw(ExpenseClaimItem),
	"Employee Advance": markRaw(EmployeeAdvanceItem),
	"Employee Grievance": markRaw(ComplaintItem),
	Event: markRaw(EventItem),
}

const router = useRouter()
const socket = inject("$socket")
const employee = inject("$employee")
const user = inject("$user")
const filterMap = reactive({})
const activeTab = ref(props.tabButtons ? getButtonKey(props.tabButtons[0]) : undefined)
const areFiltersApplied = ref(false)
const appliedFilters = ref([])
const workflowStateField = ref(null)
const isRequestModalOpen = ref(false)
const selectedRequest = ref(null)

// infinite scroll
const scrollContainer = ref(null)
const hasNextPage = ref(true)
const listOptions = ref({
	doctype: props.doctype,
	fields: props.fields,
	group_by: props.groupBy,
	order_by: `\`tab${props.doctype}\`.modified desc`,
	page_length: 50,
})

// computed properties
const isTeamRequest = computed(() => {
	return props.tabButtons && activeTab.value === getButtonKey(props.tabButtons[1])
})

const formViewRoute = computed(() => {
	return `${props.doctype.replace(/\s+/g, "")}FormView`
})

const detailViewRoute = computed(() => {
	return `${props.doctype.replace(/\s+/g, "")}DetailView`
})
const canCreate = computed(() => {
	return Boolean(props.forceShowCreateButton || createPermission?.data?.has_permission)
})

const APPROVER_FIELD_MAP = {
	"Attendance Request": "shift_request_approver",
	"Shift Request": "approver",
	"Leave Application": "leave_approver",
	"Expense Claim": "expense_approver",
	"Employee Advance": "expense_approver",
	"Employee Grievance": "reports_to",
}

const OWNER_FIELD_MAP = {
	"Employee Grievance": "raised_by",
	Event: "owner",
}

const defaultFilters = computed(() => {
	const filters = []

	if (isTeamRequest.value) {
		const approverField = APPROVER_FIELD_MAP[props.doctype]
		if (approverField) {
			const approverValue =
				props.doctype === "Employee Grievance"
					? employee.data?.name
					: employee.data?.user_id
			if (approverValue) {
				filters.push([props.doctype, approverField, "=", approverValue])
			}
			if (props.doctype === "Employee Grievance" && employee.data?.name) {
				filters.push([props.doctype, "raised_by", "!=", employee.data.name])
			}
		} else if (employee.data?.name) {
			filters.push([props.doctype, "employee", "!=", employee.data.name])
		}
	} else {
		if (props.doctype === "Event") {
			// Event permissions already scope visible records; don't force owner-only filter.
			return filters
		}

		const ownerField = OWNER_FIELD_MAP[props.doctype] || "employee"
		const ownerValue = employee.data?.name
		if (ownerValue) {
			filters.push([props.doctype, ownerField, "=", ownerValue])
		}
	}

	return filters
})

const isDefaultFilterReady = computed(() => {
	if (isTeamRequest.value) {
		const approverField = APPROVER_FIELD_MAP[props.doctype]
		if (approverField) {
			if (props.doctype === "Employee Grievance") {
				return Boolean(employee.data?.name)
			}
			return Boolean(employee.data?.user_id)
		}
		return Boolean(employee.data?.name)
	}

	if (props.doctype === "Event") {
		return true
	}

	return Boolean(employee.data?.name)
})

// resources
const documents = createResource({
	url: "frappe.desk.reportview.get",
	onSuccess: (data) => {
		if (data.values?.length < listOptions.value.page_length) {
			hasNextPage.value = false
		}
	},
	transform(data) {
		if (data.length === 0) {
			return []
		}

		// convert keys and values arrays to docs object
		const fields = data["keys"]
		const values = data["values"]
		const docs = values.map((value) => {
			const doc = {}
			fields.forEach((field, index) => {
				doc[field] = value[index]
			})
			return doc
		})

		let pagedData
		if (!documents.params.start || documents.params.start === 0) {
			pagedData = docs
		} else {
			pagedData = documents.data.concat(docs)
		}

		return pagedData
	},
})

const createPermission = createResource({
	url: "frappe.client.has_permission",
	params: { doctype: props.doctype, docname: "", perm_type: "create" },
	auto: true,
})

// helper functions
const openRequestModal = async (request) => {
	selectedRequest.value = request
	selectedRequest.value.doctype = "Employee Checkin"
	selectedRequest.value.date = request.time
	selectedRequest.value.formatted_time = formatJalaliTime(request.time, { withSeconds: true })
	selectedRequest.value.formatted_latitude = `${Number(request.latitude).toFixed(5)}°`
	selectedRequest.value.formatted_longitude = `${Number(request.longitude).toFixed(5)}°`
	isRequestModalOpen.value = true
}

const closeRequestModal = async () => {
	isRequestModalOpen.value = false
	selectedRequest.value = null
}

function initializeFilters() {
	props.filterConfig.forEach((filter) => {
		filterMap[filter.fieldname] = {
			condition: "=",
			value: null,
		}
	})

	appliedFilters.value = []
}
initializeFilters()

function prepareFilters() {
	let condition = ""
	let value = ""
	appliedFilters.value = []

	for (const fieldname in filterMap) {
		condition = filterMap[fieldname].condition
		// accessing .value because autocomplete returns an object instead of value
		if (typeof condition === "object" && condition !== null) {
			condition = condition.value
		}

		value = filterMap[fieldname].value
		if (condition && value) appliedFilters.value.push([props.doctype, fieldname, condition, value])
	}
}

function applyFilters() {
	prepareFilters()
	fetchDocumentList()
	modalController.dismiss()
	areFiltersApplied.value = appliedFilters.value.length ? true : false
}

function clearFilters() {
	initializeFilters()
	fetchDocumentList()
	modalController.dismiss()
	areFiltersApplied.value = false
}

function fetchDocumentList(start = 0) {
	if (!isDefaultFilterReady.value) return

	if (start === 0) {
		hasNextPage.value = true
	}

	const filters = [[props.doctype, "docstatus", "!=", "2"]]
	filters.push(...defaultFilters.value)

	if (appliedFilters.value) filters.push(...appliedFilters.value)

	if (
		workflowStateField.value
		&& !listOptions.value.fields.includes(workflowStateField.value)
	) {
		listOptions.value.fields.push(workflowStateField.value)
	}

	documents.submit({
		...listOptions.value,
		start: start || 0,
		filters: filters,
	})
}

const handleScroll = debounce(() => {
	if (!hasNextPage.value) return

	const { scrollTop, scrollHeight, clientHeight } = scrollContainer.value
	const scrollPercentage = (scrollTop / (scrollHeight - clientHeight)) * 100

	if (scrollPercentage >= 90) {
		const start = documents.params.start + listOptions.value.page_length
		fetchDocumentList(start)
	}
}, 500)

const handleRefresh = (event) => {
	setTimeout(() => {
		fetchDocumentList()
		event.target.complete()
	}, 500)
}

watch(
	() => activeTab.value,
	(_value) => {
		fetchDocumentList()
	}
)

watch(
	[() => employee.data?.name, () => employee.data?.user_id, () => user.data?.name],
	() => {
		if (isDefaultFilterReady.value) {
			fetchDocumentList()
		}
	},
	{ immediate: true }
)

onMounted(async () => {
	const workflow = useWorkflow(props.doctype)
	await workflow.workflowDoc.promise
	workflowStateField.value = workflow.getWorkflowStateField()
	fetchDocumentList()

	useListUpdate(socket, props.doctype, () => fetchDocumentList())
})
</script>
