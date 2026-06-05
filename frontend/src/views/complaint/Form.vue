<template>
	<BaseLayout :pageTitle="pageTitle">
		<template #body>
			<div class="w-full max-w-5xl mx-auto mt-7 mb-7 p-4">
				<FormView
					v-if="formFields.data"
					doctype="Employee Grievance"
					v-model="grievance"
					:isSubmittable="true"
					:returnOnCreate="true"
					returnOnCreateRoute="EmployeeGrievanceListView"
					:fields="formFields.data"
					:id="props.id"
					:showAttachmentView="true"
					@validateForm="validateForm"
				/>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { createResource } from "frappe-ui"
import { inject, ref, computed } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import FormView from "@/components/FormView.vue"

const dayjs = inject("$dayjs")
const __ = inject("$translate")
const sessionEmployee = inject("$employee")
const today = dayjs().format("YYYY-MM-DD")

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})
const pageTitle = computed(() =>
	props.id ? __("Employee Grievance") : __("New Employee Grievance")
)

const grievance = ref({
	date: today,
	status: "Open",
	feedback_type: "انتقاد",
})

const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Employee Grievance" },
	transform(data) {
		return getFilteredFields(data)
	},
	onSuccess() {
		applyDefaults()
		grievanceTypes.reload()
	},
})
formFields.reload()

const grievanceTypes = createResource({
	url: "hrms.api.get_grievance_types",
	onSuccess(data) {
		const grievanceTypeField = formFields.data?.find((field) => field.fieldname === "grievance_type")
		if (!grievanceTypeField) return

		grievanceTypeField.documentList = (data || []).map((row) => ({
			label: row.name,
			value: row.name,
		}))
		if (!grievance.value.grievance_type && grievanceTypeField.documentList.length) {
			grievance.value.grievance_type = grievanceTypeField.documentList[0].value
		}
	},
})

function getFilteredFields(fields) {
	const createVisibleFields = new Set([
		"feedback_type",
		"subject",
		"grievance_type",
		"description",
	])

	const detailVisibleFields = new Set([
		"feedback_type",
		"subject",
		"grievance_type",
		"description",
		"status",
		"cause_of_grievance",
		"resolution_detail",
		"resolved_by",
		"resolution_date",
	])

	const visibleFieldSet = props.id ? detailVisibleFields : createVisibleFields

	return fields.filter((field) => visibleFieldSet.has(field.fieldname))
}

function applyDefaults() {
	grievance.value.date = grievance.value.date || today
	grievance.value.status = grievance.value.status || "Open"
	grievance.value.feedback_type = grievance.value.feedback_type || "انتقاد"
	grievance.value.raised_by = grievance.value.raised_by || sessionEmployee.data.name
	grievance.value.reports_to = grievance.value.reports_to || sessionEmployee.data.reports_to
}

function validateForm() {
	applyDefaults()
}
</script>
