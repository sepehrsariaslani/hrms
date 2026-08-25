<template>
	<BaseLayout :pageTitle="pageTitle">
		<template #body>
			<div class="w-full max-w-5xl mx-auto mt-7 mb-7 p-4">
				<FormView
					v-if="formFields.data"
					doctype="Employee Advance"
					v-model="employeeAdvance"
					:isSubmittable="true"
					:fields="formFields.data"
					:id="props.id"
					:returnOnCreate="!props.id"
					returnOnCreateRoute="EmployeeAdvanceListView"
					:showAttachmentView="true"
					@validateForm="validateForm"
				>
					<template #headerNotice>
						<div
							class="px-4 pt-4"
							data-tour="form-policy-notice"
						>
							<div
								class="rounded-lg px-3 py-3 text-sm leading-6 whitespace-pre-line hr-accent-soft"
							>
								{{ ADVANCE_POLICY_NOTICE }}
							</div>
						</div>
					</template>
				</FormView>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { createResource } from "frappe-ui"
import { ref, watch, inject, computed } from "vue"
import { useRoute } from "vue-router"

import BaseLayout from "@/components/BaseLayout.vue"
import FormView from "@/components/FormView.vue"

import { getCompanyCurrency } from "@/data/currencies"

const employee = inject("$employee")
const __ = inject("$translate")
const route = useRoute()

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})
const pageTitle = computed(() =>
	props.id ? __("Employee Advance") : __("New Employee Advance")
)

const ADVANCE_POLICY_NOTICE = `سقف پرداختی مساعده در هر ماه حداکثر ۱۰,۰۰۰,۰۰۰ تومان است.
پس از ثبت درخواست، مساعده ابتدا توسط سرپرست و سپس توسط حسابدار بررسی می‌شود و در صورت امکان تایید می‌گردد.
لطفا مبلغ مساعده خود را دقیق ثبت کنید.
پرداخت مساعده از ابتدای ماه تا تاریخ دهم انجام نمی‌شود مگر در شرایط خاص.`

const PURPOSE_HELP_TEXT =
	"در صورتی که ضرورتی دارید، آن را در این فیلد بنویسید تا بررسی درخواست سریع‌تر انجام شود."

// object to store form data
const employeeAdvance = ref({
	employee: employee.data?.name,
	employee_name: employee.data?.employee_name,
	company: employee.data?.company,
	department: employee.data?.department,
})

function getPostingDateFromQuery() {
	const queryDate = String(route.query?.date || "")
	return /^\d{4}-\d{2}-\d{2}$/.test(queryDate) ? queryDate : ""
}

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Employee Advance" },
	transform(data) {
		const fields = getFilteredFields(data)
		return applyFilters(fields)
	},
	onSuccess() {
		setCompanyCurrencyDefaults()
	},
})
formFields.reload()

watch(
	() => employeeAdvance.value.company,
	() => {
		setCompanyCurrencyDefaults()
	},
	{ immediate: true }
)

watch(
	() => employee.data?.name,
	(employeeName) => {
		if (!employeeName || props.id) return
		employeeAdvance.value.employee = employee.data?.name
		employeeAdvance.value.employee_name = employee.data?.employee_name
		employeeAdvance.value.company = employee.data?.company
		employeeAdvance.value.department = employee.data?.department
		const postingDate = getPostingDateFromQuery()
		if (postingDate) {
			employeeAdvance.value.posting_date = postingDate
		}
		setCompanyCurrencyDefaults()
	},
	{ immediate: true }
)

watch(
	() => route.query?.date,
	(value) => {
		if (props.id) return
		const queryDate = String(value || "")
		if (!/^\d{4}-\d{2}-\d{2}$/.test(queryDate)) return
		employeeAdvance.value.posting_date = queryDate
	},
	{ immediate: true }
)

// helper functions
function getFilteredFields(fields) {
	if (!props.id) {
		const minimalFields = new Set(["posting_date", "advance_amount", "purpose"])
		return fields.filter((field) => minimalFields.has(field.fieldname))
	}

	const excludeFields = [
		"naming_series",
		"advance_account",
		"mode_of_payment",
		"currency",
		"exchange_rate",
	]
	return fields.filter((field) => !excludeFields.includes(field.fieldname))
}

function applyFilters(fields) {
	return fields.map((field) => {
		if (field.fieldname === "purpose") {
			field.reqd = 0
			field.label = "توضیحات"
			field.description = PURPOSE_HELP_TEXT
		}
		return field
	})
}

function setCompanyCurrencyDefaults() {
	const company = employeeAdvance.value.company
	const currency = company ? getCompanyCurrency(company) : null
	if (!currency) return

	employeeAdvance.value.currency = currency
	employeeAdvance.value.exchange_rate = 1
}

function validateForm() {
	if (!employeeAdvance.value.purpose?.trim()) {
		employeeAdvance.value.purpose = "درخواست مساعده"
	}

	employeeAdvance.value.employee = employee.data.name
	employeeAdvance.value.employee_name = employee.data.employee_name
	employeeAdvance.value.company = employee.data.company
	employeeAdvance.value.department = employee.data.department
}
</script>
