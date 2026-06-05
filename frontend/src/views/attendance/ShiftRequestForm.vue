<template>
	<BaseLayout :pageTitle="props.id ? __('Shift Request') : __('New Shift Request')">
		<template #body>
			<div class="mt-7 mb-7 p-4">
				<div
					v-if="!props.id"
					class="mb-3 rounded-lg border border-slate-200 bg-white p-3"
				>
					<div class="text-sm font-semibold text-gray-900">ثبت درخواست تغییر شیفت</div>
					<div class="mt-1 text-xs text-gray-600">
						ابتدا روز را انتخاب کنید، سپس اگر لازم بود شیفت جدید (صبح/عصر) را تعیین کنید.
					</div>
					<div class="mt-2 grid grid-cols-2 gap-2">
						<button
							v-for="slot in slotTemplateButtons"
							:key="slot.code"
							type="button"
							class="rounded-lg border px-2 py-2 text-right transition"
							:class="
								selectedSlotCode === slot.code
									? 'border-indigo-400 bg-indigo-50 text-indigo-700'
									: 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
							"
							@click="selectSlotTemplate(slot.code)"
						>
							<div class="text-xs font-semibold">{{ slot.label }}</div>
							<div class="mt-0.5 text-[11px] text-gray-500">{{ slot.timeText }}</div>
						</button>
					</div>
				</div>

				<FormView
					v-if="formFields.data"
					doctype="Shift Request"
					v-model="shiftRequest"
					:isSubmittable="true"
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
import { computed, ref, watch, inject } from "vue"
import { useRoute } from "vue-router"

import BaseLayout from "@/components/BaseLayout.vue"
import FormView from "@/components/FormView.vue"

const employee = inject("$employee")
const __ = inject("$translate")
const route = useRoute()

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

// reactive object to store form data
const shiftRequest = ref({})
const selectedSlotCode = ref(typeof route.query.slot_code === "string" ? route.query.slot_code : "")
const slotTemplates = ref({ Morning: null, Evening: null })

const slotTemplateButtons = computed(() => {
	return [
		{
			code: "Morning",
			label: "صبح",
			timeText: formatSlotTemplateTime(slotTemplates.value.Morning),
		},
		{
			code: "Evening",
			label: "عصر",
			timeText: formatSlotTemplateTime(slotTemplates.value.Evening),
		},
	]
})

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Shift Request" },
	auto: true,
	transform(data) {
		if (props.id) return data
		const fieldOrder = ["from_date", "to_date", "shift_type", "approver"]
		const filtered = data.filter((field) => fieldOrder.includes(field.fieldname))
		const ordered = fieldOrder
			.map((fieldname) => filtered.find((field) => field.fieldname === fieldname))
			.filter(Boolean)

		for (const field of ordered) {
			if (field.fieldname === "from_date") {
				field.label = "تاریخ"
			}
			if (field.fieldname === "to_date") {
				field.label = "تا تاریخ"
			}
			if (field.fieldname === "shift_type") {
				field.label = "شیفت درخواستی"
			}
		}

		return ordered
	},
	onSuccess() {
		applyShiftTypeFieldOptions()
		applyQueryDefaults()
	},
})

createResource({
	url: "hrms.api.get_weekly_shift_slot_templates",
	auto: !props.id,
	onSuccess(data) {
		slotTemplates.value = normalizeSlotTemplates(data || [])
		applyShiftTypeFieldOptions()
		applyQueryDefaults()
	},
})

createResource({
	url: "hrms.api.get_shift_request_approvers",
	auto: !props.id,
	makeParams() {
		return { employee: employee.data?.name }
	},
	onSuccess(data) {
		const approver = formFields.data?.find((field) => field.fieldname === "approver")
		approver.documentList = data?.map((approver) => ({
			label: approver.full_name ? `${approver.name} : ${approver.full_name}` : approver.name,
			value: approver.name,
		}))
		shiftRequest.value.approver = data[0]?.name
	},
})

// form scripts
watch(
	() => shiftRequest.value.employee,
	(employee_id) => {
		if (props.id && employee_id !== employee.data.name) {
			// if employee is not the current user, set form as read only
			setFormReadOnly()
		}
	}
)

watch(
	() => [shiftRequest.value.from_date, shiftRequest.value.to_date],
	([from_date, to_date]) => {
		validateDates(from_date, to_date)
	}
)

watch(
	() => route.query,
	() => {
		selectedSlotCode.value = typeof route.query.slot_code === "string" ? route.query.slot_code : ""
		applyQueryDefaults()
	}
)

// helper functions
function setFormReadOnly() {
	if (shiftRequest.value.approver === employee.data.user_id) return
	formFields.data.map((field) => (field.read_only = true))
}

function validateDates(from_date, to_date) {
	if (!(from_date && to_date)) return

	const error_message = from_date > to_date ? __("To Date cannot be before From Date") : ""

	const from_date_field = formFields.data.find((field) => field.fieldname === "from_date")
	from_date_field.error_message = error_message
}

function validateForm() {
	shiftRequest.value.employee = employee.data.name
	if (shiftRequest.value.from_date && !shiftRequest.value.to_date) {
		shiftRequest.value.to_date = shiftRequest.value.from_date
	}
}

function applyQueryDefaults() {
	if (props.id) return

	const fromDate = typeof route.query.from_date === "string" ? route.query.from_date : ""
	const toDate = typeof route.query.to_date === "string" ? route.query.to_date : ""
	const shiftType = typeof route.query.shift_type === "string" ? route.query.shift_type : ""
	const slotCode = typeof route.query.slot_code === "string" ? route.query.slot_code : ""
	const slotShiftType = getShiftTypeForSlotCode(slotCode)

	if (fromDate && !shiftRequest.value.from_date) {
		shiftRequest.value.from_date = fromDate
	}
	if (toDate && !shiftRequest.value.to_date) {
		shiftRequest.value.to_date = toDate
	}
	if (shiftType && !shiftRequest.value.shift_type) {
		shiftRequest.value.shift_type = shiftType
	}
	if (!shiftRequest.value.shift_type && slotShiftType) {
		shiftRequest.value.shift_type = slotShiftType
	}
	if (slotCode) {
		selectedSlotCode.value = slotCode
	}
}

function normalizeSlotTemplates(templates) {
	const map = { Morning: null, Evening: null }
	for (const template of templates || []) {
		if (!template?.slot_code) continue
		map[template.slot_code] = template
	}
	return map
}

function normalizeTime(value) {
	const text = String(value || "").slice(0, 5)
	return /^\d{2}:\d{2}$/.test(text) ? text : ""
}

function formatSlotTemplateTime(template) {
	if (!template?.start_time || !template?.end_time) return "زمان پیش‌فرض سیستم"
	const start = normalizeTime(template.start_time)
	const end = normalizeTime(template.end_time)
	if (!(start && end)) return "زمان پیش‌فرض سیستم"
	return `${start} تا ${end}`
}

function getShiftTypeForSlotCode(slotCode) {
	if (slotCode === "Morning") return slotTemplates.value.Morning?.shift_type || ""
	if (slotCode === "Evening") return slotTemplates.value.Evening?.shift_type || ""
	return ""
}

function applyShiftTypeFieldOptions() {
	const field = formFields.data?.find((entry) => entry.fieldname === "shift_type")
	if (!field) return

	const options = []
	const seen = new Set()
	for (const code of ["Morning", "Evening"]) {
		const shiftType = getShiftTypeForSlotCode(code)
		if (!(shiftType && !seen.has(shiftType))) continue
		seen.add(shiftType)
		options.push({
			label: code === "Morning" ? `صبح (${shiftType})` : `عصر (${shiftType})`,
			value: shiftType,
		})
	}
	if (options.length) {
		field.documentList = options
	}
}

function selectSlotTemplate(slotCode) {
	selectedSlotCode.value = slotCode
	const shiftType = getShiftTypeForSlotCode(slotCode)
	if (shiftType) {
		shiftRequest.value.shift_type = shiftType
	}
}
</script>
