<template>
	<BaseLayout :pageTitle="props.id ? __('Shift Assignment') : __('New Shift Assignment')">
		<template #body>
			<div class="mt-7 mb-7 p-4">
				<div
					v-if="props.id"
					class="mb-3 rounded-lg border border-slate-200 bg-white p-3"
				>
					<div class="text-sm font-semibold text-gray-900">جزئیات شیفت ثبت‌شده</div>
					<div class="mt-1 text-xs text-gray-600">
						این رکورد بر اساس تایید نهایی شیفت نمایش داده می‌شود و فقط قابل مشاهده است.
					</div>
				</div>
				<FormView
					v-if="formFields.data"
					doctype="Shift Assignment"
					v-model="shiftAssignment"
					:isSubmittable="!props.id"
					:fields="formFields.data"
					:id="props.id"
					@validateForm="validateForm"
				/>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { createResource } from "frappe-ui"
import { ref, watch, inject } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import FormView from "@/components/FormView.vue"

const employee = inject("$employee")
const __ = inject("$translate")

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

// reactive object to store form data
const shiftAssignment = ref({})

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Shift Assignment" },
	auto: true,
	transform(data) {
		const createFieldOrder = ["shift_type", "start_date", "end_date", "shift_location"]
		const detailFieldOrder = [
			"employee",
			"employee_name",
			"company",
			"department",
			"shift_type",
			"shift_location",
			"start_date",
			"end_date",
			"status",
			"weekly_shift_finalization",
			"weekly_shift_finalization_slot",
			"shift_request",
			"shift_schedule_assignment",
		]
		const fieldOrder = props.id ? detailFieldOrder : createFieldOrder
		const selected = fieldOrder
			.map((fieldname) => data.find((field) => field.fieldname === fieldname))
			.filter(Boolean)

		for (const field of selected) {
			if (["start_date", "end_date"].includes(field.fieldname)) {
				field.label = field.fieldname === "start_date" ? "تاریخ شروع" : "تاریخ پایان"
			}
			if (field.fieldname === "shift_type") {
				field.label = "شیفت"
			}
			if (field.fieldname === "weekly_shift_finalization") {
				field.label = "برنامه نهایی‌سازی هفتگی"
			}
			if (field.fieldname === "weekly_shift_finalization_slot") {
				field.label = "اسلات نهایی‌سازی هفتگی"
			}
			if (props.id) {
				field.read_only = true
			}
		}

		return selected
	},
})

// form scripts
watch(
	() => shiftAssignment.value.employee,
	(employee_id) => {
		if (props.id && employee_id !== employee.data.name) {
			// if employee is not the current user, set form as read only
			setFormReadOnly()
		}
	}
)

watch(
	() => [shiftAssignment.value.start_date, shiftAssignment.value.end_date],
	([start_date, end_date]) => {
		validateDates(start_date, end_date)
	}
)

// helper functions
function setFormReadOnly() {
	if (!formFields.data) return
	formFields.data.forEach((field) => {
		field.read_only = true
	})
}

function validateDates(start_date, end_date) {
	if (!(start_date && end_date)) return

	const error_message = start_date > end_date ? __("End Date cannot be before Start Date") : ""

	const start_date_field = formFields.data.find((field) => field.fieldname === "start_date")
	start_date_field.error_message = error_message
}

function validateForm() {
	shiftAssignment.value.employee = employee.data.name
	if (shiftAssignment.value.start_date && !shiftAssignment.value.end_date) {
		shiftAssignment.value.end_date = shiftAssignment.value.start_date
	}
}
</script>
