<template>
	<div
		v-if="document?.doc"
		class="bg-white w-full flex flex-col items-center justify-center pb-5 max-h-[calc(100vh-5rem)]"
	>
		<!-- Header -->
		<div
			class="w-full flex flex-row gap-2 pt-8 pb-5 border-b justify-center items-center sticky top-0 z-[100]"
		>
			<span class="text-gray-900 font-bold text-lg text-center">
				{{ __(document?.doctype) }}
			</span>
			<FeatherIcon
				v-if="props.showOpenForm"
				name="external-link"
				class="h-4 w-4 text-gray-500 cursor-pointer"
				@click="openFormView"
			/>
		</div>

		<!-- Request Summary -->
		<div class="w-full p-4 overflow-auto">
			<div class="flex flex-col items-center justify-center gap-5">
				<div
					v-for="field in fieldsWithValues"
					:key="field.fieldname"
					:class="[
						['Small Text', 'Text', 'Long Text', 'Table', 'geolocation'].includes(
							field.fieldtype
						)
							? 'flex-col'
							: 'flex-row items-center justify-between',
						'flex w-full',
					]"
				>
					<div class="text-gray-600 text-base">{{ __(field.label, null, props.modelValue?.doctype) }}</div>
					<component
						v-if="field.fieldtype === 'Table'"
						:is="field.component"
						:doc="document?.doc"
					/>
					<FormattedField
						v-else
						:value="field.value"
						:fieldtype="field.fieldtype"
						:fieldname="field.fieldname"
					/>
				</div>

				<!-- Attachments -->
				<div
					class="flex flex-col gap-2 w-full"
					v-if="attachedFiles?.data?.length"
				>
					<div class="text-gray-600 text-base">{{ __('Attachments') }}</div>
					<ul class="w-full flex flex-col items-center gap-2">
						<li
							class="bg-gray-100 rounded p-2 w-full"
							v-for="(file, index) in attachedFiles.data"
							:key="index"
						>
							<div
								class="flex flex-row items-center justify-between text-gray-700 text-sm"
							>
								<span class="grow" @click="showFilePreview(file)">
									{{ file.file_name || file.name }}
								</span>
							</div>
						</li>
					</ul>
				</div>
			</div>
		</div>

		<!-- Actions -->
		<div
			v-if="canReviewCheckinRequest"
			class="flex w-full flex-row items-center justify-between gap-2 sticky bottom-0 border-t z-[100] p-4"
		>
			<Button
				@click="reviewCheckinRequest({ action: 'reject' })"
				class="w-full py-5"
				variant="subtle"
				theme="red"
				:loading="isReviewing"
			>
				{{ __("رد") }}
			</Button>
			<Button
				@click="editAndApproveCheckinRequest"
				class="w-full py-5"
				variant="outline"
				:loading="isReviewing"
			>
				{{ __("ویرایش و تایید") }}
			</Button>
			<Button
				@click="reviewCheckinRequest({ action: 'approve' })"
				class="w-full py-5"
				variant="solid"
				theme="green"
				:loading="isReviewing"
			>
				{{ __("تایید") }}
			</Button>
		</div>

		<WorkflowActionSheet
			v-else-if="workflow?.hasWorkflow"
			:doc="document.doc"
			:workflow="workflow"
			view="actionSheet"
		/>

		<div
			v-else-if="
				!isCheckinAttendanceRequest &&
				approvalDoctypes.includes(document?.doc?.doctype) &&
				['Open', 'Draft'].includes(document?.doc?.[approvalField]) &&
				hasPermission('approval')
			"
			class="flex w-full flex-row items-center justify-between gap-3 sticky bottom-0 border-t z-[100] p-4"
		>
			<Button
				@click="updateDocumentStatus({ status: 'Rejected' })"
				class="w-full py-5"
				variant="subtle"
				theme="red"
			>
				<template #prefix>
					<FeatherIcon name="x" class="w-4" />
				</template>
				{{ __("Reject") }}
			</Button>

			<Button
				@click="updateDocumentStatus({ status: 'Approved' })"
				class="w-full py-5"
				variant="solid"
				theme="green"
			>
				<template #prefix>
					<FeatherIcon name="check" class="w-4" />
				</template>
				{{ __("Approve") }}
			</Button>
		</div>

		<div
			v-else-if="
				document?.doc?.docstatus === 0 &&
				((document?.doc?.doctype === 'Attendance Request' && !isCheckinAttendanceRequest) ||
					['Approved', 'Rejected'].includes(document?.doc?.[approvalField])) &&
				hasPermission('submit')
			"
			class="flex w-full flex-row items-center justify-between gap-3 sticky bottom-0 border-t z-[100] p-4"
		>
			<Button
				@click="updateDocumentStatus({ docstatus: 1 })"
				class="w-full py-5"
				variant="solid"
			>
				{{ __("Submit") }}
			</Button>
		</div>

		<div
			v-else-if="document?.doc?.docstatus === 1 && hasPermission('cancel')"
			class="flex w-full flex-row items-center justify-between gap-3 sticky bottom-0 border-t z-[100] p-4"
		>
			<Button
				@click="updateDocumentStatus({ docstatus: 2 })"
				class="w-full py-5"
				variant="subtle"
				theme="red"
			>
				<template #prefix>
					<FeatherIcon name="x" class="w-4" />
				</template>
				{{ __("Cancel") }}
			</Button>
		</div>

		<Dialog v-model="showEditApproveDialog">
			<template #body-title>
				<h2 class="text-lg font-bold">{{ __("ویرایش و تایید درخواست") }}</h2>
			</template>
			<template #body-content>
				<div class="flex flex-col gap-3 text-sm">
					<label class="flex flex-col gap-1">
						<span class="text-gray-700">{{ __("نوع ورود/خروج") }}</span>
						<select
							v-model="editApproveForm.logType"
							class="w-full rounded border border-gray-300 px-3 py-2"
						>
							<option value="IN">{{ __("ورود") }}</option>
							<option value="OUT">{{ __("خروج") }}</option>
						</select>
					</label>
					<label class="flex flex-col gap-1">
						<span class="text-gray-700">{{ __("ساعت") }}</span>
						<input
							v-model="editApproveForm.time"
							type="time"
							step="1"
							class="w-full rounded border border-gray-300 px-3 py-2"
						/>
					</label>
				</div>
			</template>
			<template #actions>
				<div class="flex flex-row gap-3">
					<Button
						class="w-full py-5"
						variant="outline"
						@click="showEditApproveDialog = false"
					>
						{{ __("انصراف") }}
					</Button>
					<Button
						class="w-full py-5"
						variant="solid"
						theme="green"
						:loading="isReviewing"
						@click="confirmEditAndApprove"
					>
						{{ __("تایید") }}
					</Button>
				</div>
			</template>
		</Dialog>

		<!-- File Preview Modal -->
		<ion-modal
			ref="modal"
			:is-open="showPreviewModal"
			@didDismiss="showPreviewModal = false"
		>
			<FilePreviewModal :file="selectedFile" />
		</ion-modal>
	</div>
</template>

<script setup>
import { computed, inject, ref, defineAsyncComponent, onMounted } from "vue"
import { IonModal, modalController } from "@ionic/vue"
import { useRouter } from "vue-router"
import {
	toast,
	createDocumentResource,
	createResource,
	FeatherIcon,
	Dialog,
} from "frappe-ui"

import FormattedField from "@/components/FormattedField.vue"
import FilePreviewModal from "@/components/FilePreviewModal.vue"
import WorkflowActionSheet from "@/components/WorkflowActionSheet.vue"

import { getCompanyCurrency } from "@/data/currencies"
import { settings } from "@/data/settings"
import { formatCurrency } from "@/utils/formatters"
import { localizeLeaveType } from "@/utils/leaveTypeLabels"

import useWorkflow from "@/composables/workflow"

const __ = inject("$translate")
const employee = inject("$employee")

const props = defineProps({
	fields: {
		type: Array,
		required: true,
	},
	showOpenForm: {
		type: Boolean,
		default: true,
	},
	modelValue: {
		type: Object,
		required: true,
	},
})
const router = useRouter()

let showPreviewModal = ref(false)
let selectedFile = ref({})
let workflow = ref(null)
const isReviewing = ref(false)
const showEditApproveDialog = ref(false)
const editApproveForm = ref({
	logType: "IN",
	time: "",
})

function showFilePreview(fileObj) {
	selectedFile.value = fileObj
	showPreviewModal.value = true
}

const document = createDocumentResource({
	doctype: props.modelValue.doctype,
	name: props.modelValue.name,
	auto: true,
	onSuccess(doc) {
		attachedFiles.reload()
	},
})

const attachedFiles = createResource({
	url: "hrms.api.get_attachments",
	params: {
		dt: props.modelValue.doctype,
		dn: props.modelValue.name,
	},
})

const docPermissions = createResource({
	url: "frappe.client.get_doc_permissions",
	params: { doctype: props.modelValue.doctype, docname: props.modelValue.name },
	auto: true,
})

const permittedWriteFields = createResource({
	url: "hrms.api.get_permitted_fields_for_write",
	params: { doctype: props.modelValue.doctype },
	auto: true,
})

const sessionEmployee = inject("$employee")

function hasPermission(action) {
	if (action === "approval" && props.modelValue.doctype === "Leave Application"){
		// prevent self leave approval
		const isSelfLeave = document?.doc?.employee === sessionEmployee?.data?.name 
		if (isSelfLeave && settings.data?.prevent_self_leave_approval)
			return false
		return permittedWriteFields.data?.includes(approvalField.value)
	}
	return docPermissions.data?.permissions[action]
}

const currency = computed(() => {
	let docCurrency = document?.doc?.currency

	if (!docCurrency && document?.doc?.company) {
		docCurrency = getCompanyCurrency(document?.doc?.company)
	}
	return docCurrency
})

const LOG_TYPE_LABEL_MAP = {
	IN: "ورود",
	OUT: "خروج",
}

const REVIEW_STATUS_LABEL_MAP = {
	Pending: "در انتظار بررسی",
	Approved: "تایید شده",
	Rejected: "رد شده",
}

const REQUEST_MODE_LABEL_MAP = {
	"Legacy Attendance": "درخواست حضور (قدیمی)",
	"Checkin Request": "درخواست ورود/خروج",
}

function localizeFieldValue(fieldname, value) {
	if (value === null || value === undefined) return value

	if (props.modelValue.doctype === "Leave Application" && fieldname === "leave_type") {
		return localizeLeaveType(value)
	}

	if (props.modelValue.doctype !== "Attendance Request") return value

	if (["requested_log_type", "reviewed_log_type"].includes(fieldname)) {
		return LOG_TYPE_LABEL_MAP[value] || value
	}
	if (fieldname === "review_status") {
		return REVIEW_STATUS_LABEL_MAP[value] || value
	}
	if (fieldname === "request_mode") {
		return REQUEST_MODE_LABEL_MAP[value] || value
	}
	return value
}

const fieldsWithValues = computed(() => {
	return props.fields.filter((field) => {
		if (field.fieldtype === "Currency") {
			field.value = formatCurrency(
				document.doc?.[field.fieldname],
				currency.value
			)
		} else {
			if (field.fieldtype === "Table") {
				// dynamically loading child table component as per config
				// does not work with @ alias due to vite's import analysis
				field.component = defineAsyncComponent(() =>
					import(`../components/${field.componentName}.vue`)
				)
			}
				const value =
					document?.doc?.[field.fieldname] || props.modelValue[field.fieldname]
				field.value = localizeFieldValue(field.fieldname, value)
			}

		return field.value
	})
})

const approvalField = computed(() => {
	return props.modelValue.doctype === "Expense Claim"
		? "approval_status"
		: "status"
})
const approvalDoctypes = ["Leave Application", "Expense Claim", "Shift Request"]

const isCheckinAttendanceRequest = computed(() => {
	return (
		props.modelValue.doctype === "Attendance Request" &&
		document?.doc?.request_mode === "Checkin Request"
	)
})

const canReviewCheckinRequest = computed(() => {
	if (!isCheckinAttendanceRequest.value) return false
	if (document?.doc?.docstatus !== 0) return false
	if ((document?.doc?.review_status || "Pending") !== "Pending") return false
	return document?.doc?.shift_request_approver === employee?.data?.user_id
})

const getSuccessMessage = ({ status = "", docstatus = 0 }) => {
	if (status) {
		return __("{0} successfully!", [__(status)])
	} else if (docstatus) {
		return __("Document {0} successfully!", [
			docstatus === 1 ? __("submitted") : __("cancelled")]
		)
	}
}

const getFailureMessage = ({ status = "", docstatus = 0 }) => {
	if (status) {
		return __("{0} failed!", [status === __("Approved") ? __("Approval") : __("Rejection")])
	} else if (docstatus) {
		return __('Document {0} failed!', [docstatus === 1 ? __("submission") : __("cancellation")])
	}
}

const updateDocumentStatus = ({ status = "", docstatus = 0 }) => {
	let updateValues = {}

	if (status) updateValues[approvalField.value] = status
	if (docstatus) updateValues.docstatus = docstatus

	document.setValue.submit(
		{ ...updateValues },
		{
			onSuccess() {
				if (docstatus !== 0) modalController.dismiss()

				toast({
					title: __("Success"),
					text: getSuccessMessage({ status, docstatus }),
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			},
			onError() {
				toast({
					title: __("Error"),
					text: getFailureMessage({ status, docstatus }),
					icon: "alert-circle",
					position: "bottom-center",
					iconClasses: "text-red-500",
				})
			},
		}
	)
}

const reviewCheckinRequest = ({ action, reviewed_time = null, reviewed_log_type = null }) => {
	if (!document?.doc?.name) return

	isReviewing.value = true
	createResource({
		url: "hrms.api.review_attendance_checkin_request",
		onSuccess() {
			isReviewing.value = false
			document.reload()
			toast({
				title: __("Success"),
				text: __("Request {0} successfully!", [action === "approve" ? __("approved") : __("rejected")]),
				icon: "check-circle",
				position: "bottom-center",
				iconClasses: "text-green-500",
			})
			modalController.dismiss()
		},
		onError(error) {
			isReviewing.value = false
			toast({
				title: __("Error"),
				text: error?.messages?.[0] || error?.message || __("امکان بررسی درخواست وجود ندارد"),
				icon: "alert-circle",
				position: "bottom-center",
				iconClasses: "text-red-500",
			})
		},
	}).submit({
		name: document.doc.name,
		action,
		reviewed_time,
		reviewed_log_type,
	})
}

const editAndApproveCheckinRequest = () => {
	const currentLogType = (document?.doc?.reviewed_log_type || document?.doc?.requested_log_type || "IN").toUpperCase()
	const currentTime = document?.doc?.reviewed_time || document?.doc?.requested_time || ""
	editApproveForm.value = {
		logType: ["IN", "OUT"].includes(currentLogType) ? currentLogType : "IN",
		time: String(currentTime).slice(0, 8),
	}
	showEditApproveDialog.value = true
}

const confirmEditAndApprove = () => {
	const normalizedLogType = (editApproveForm.value.logType || "").toUpperCase()
	if (!["IN", "OUT"].includes(normalizedLogType)) {
		toast({
			title: __("Error"),
			text: __("نوع ورود/خروج باید ورود یا خروج باشد"),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
		return
	}

	const reviewedTime = (editApproveForm.value.time || "").trim()
	if (!reviewedTime) {
		toast({
			title: __("Error"),
			text: __("ساعت را وارد کنید"),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
		return
	}

	showEditApproveDialog.value = false
	reviewCheckinRequest({
		action: "approve",
		reviewed_log_type: normalizedLogType,
		reviewed_time: reviewedTime,
	})
}

const openFormView = () => {
	modalController.dismiss()
	router.push({
		name: `${props.modelValue.doctype.replace(/\s+/g, "")}DetailView`,
		params: { id: props.modelValue.name },
	})
}

onMounted(() => {
	workflow.value = useWorkflow(props.modelValue.doctype)
})

</script>

<style scoped>
ion-modal {
	--height: 100%;
}
</style>
