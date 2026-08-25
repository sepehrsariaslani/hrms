<template>
	<div
		v-if="showField"
		class="flex flex-col gap-1.5"
		:data-tour="props.fieldname ? `field-${props.fieldname}` : null"
	>
		<!-- Label -->
		<span
			v-if="!['Check', 'Section Break', 'Column Break'].includes(props.fieldtype)"
			:class="[
				// mark field as mandatory
				props.reqd ? `after:content-['_*'] after:text-red-600` : ``,
				`block text-sm leading-5 text-gray-700`,
			]"
		>
			{{ props.label }}
		</span>
		<span
			v-if="
				props.description &&
				!['Check', 'Section Break', 'Column Break'].includes(props.fieldtype)
			"
			class="text-xs leading-5 text-gray-500 -mt-1"
		>
			{{ props.description }}
		</span>

		<!-- Select or Link field with predefined options -->
		<Autocomplete
			v-if="props.fieldtype === 'Select' || props.documentList"
			:class="isReadOnly ? 'pointer-events-none' : ''"
			:placeholder="__('Select {0}', [props.label])"
			:options="selectionList"
			:modelValue="modelValue"
			v-bind="$attrs"
			:disabled="isReadOnly"
			@update:modelValue="(v) => emit('update:modelValue', v?.value)"
		/>

		<!-- Link field -->
		<Link
			v-else-if="props.fieldtype === 'Link'"
			:doctype="props.options"
			:modelValue="modelValue"
			:filters="props.linkFilters"
			:disabled="isReadOnly"
			@update:modelValue="(v) => emit('update:modelValue', v)"
		/>

		<!-- Text -->
		<Input
			v-else-if="['Text Editor', 'Small Text', 'Text', 'Long Text'].includes(props.fieldtype)"
			type="textarea"
			:value="modelValue"
			:placeholder="__('Enter {0}', [props.label])"
			@input="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
			class="h-15"
		/>

		<!-- Check -->
		<Input
			v-else-if="props.fieldtype === 'Check'"
			type="checkbox"
			:label="props.label"
			:value="modelValue"
			@input="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
			class="rounded-sm text-gray-800"
		/>

		<!-- Data field -->
		<Input
			v-else-if="props.fieldtype === 'Data'"
			type="text"
			:value="modelValue"
			@input="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
		/>

		<!-- Read only currency field -->
		<Input
			v-else-if="props.fieldtype === 'Currency' && isReadOnly"
			type="text"
			:value="modelValue"
			@input="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
		/>

		<!-- Editable currency field -->
		<PersianNumberInput
			v-else-if="props.fieldtype === 'Currency'"
			:modelValue="modelValue"
			@update:modelValue="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
		/>

		<!-- Float/Int field -->
		<Input
			v-else-if="isNumberType"
			type="number"
			:value="modelValue"
			@input="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
			v-bind="$attrs"
			:disabled="isReadOnly"
		/>

		<!-- Section Break -->
		<div
			v-else-if="props.fieldtype === 'Section Break'"
			:class="props.addSectionPadding ? 'mt-2' : ''"
		>
			<h2
				v-if="props.label"
				class="text-base font-semibold text-gray-800"
				:class="props.addSectionPadding ? 'pt-4' : ''"
			>
				{{ props.label }}
			</h2>
		</div>

		<!-- Date -->
		<JalaliDatePicker
			v-else-if="props.fieldtype === 'Date'"
			:modelValue="modelValue"
			:placeholder="__('Select {0}', [props.label])"
			@update:modelValue="(v) => emit('update:modelValue', v)"
			@change="(v) => emit('change', v)"
			:disabled="isReadOnly"
			:minDate="props.minDate"
			:maxDate="props.maxDate"
		/>

		<!-- Time -->
		<input
			v-else-if="props.fieldtype === 'Time'"
			type="time"
			:value="modelValue || ''"
			@input="(event) => emit('update:modelValue', event.target.value)"
			@change="(event) => emit('change', event.target.value)"
			v-bind="$attrs"
			:disabled="isReadOnly"
			class="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-gray-500 focus:outline-none focus:ring-0 disabled:bg-gray-100 disabled:text-gray-500"
		/>

		<!-- Datetime -->
		<div
			v-else-if="props.fieldtype === 'Datetime'"
			class="flex flex-col gap-2"
		>
			<JalaliDatePicker
				:modelValue="getDatetimeDatePart(modelValue)"
				:placeholder="__('Select {0}', [props.label])"
				:disabled="isReadOnly"
				@update:modelValue="updateDatetimeDate"
				@change="(v) => emit('change', v)"
			/>
			<input
				type="time"
				:value="getDatetimeTimePart(modelValue)"
				@input="(event) => updateDatetimeTime(event.target.value)"
				@change="(event) => emit('change', event.target.value)"
				v-bind="$attrs"
				:disabled="isReadOnly"
				class="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-gray-500 focus:outline-none focus:ring-0 disabled:bg-gray-100 disabled:text-gray-500"
			/>
			<div v-if="modelValue" class="text-xs text-gray-500">
				{{ formatDateTimeField(modelValue) }}
			</div>
		</div>

		<ErrorMessage :message="props.errorMessage" />
	</div>
</template>

<script setup>
import { Autocomplete, ErrorMessage, Input } from "frappe-ui"
import { computed, onMounted, inject } from "vue"

import Link from "@/components/Link.vue"
import JalaliDatePicker from "@/components/JalaliDatePicker.vue"
import PersianNumberInput from "@/components/PersianNumberInput.vue"
import { formatJalaliDateTime } from "@/utils/jalali"

const __ = inject("$translate")

const props = defineProps({
	fieldtype: String,
	fieldname: String,
	modelValue: [String, Number, Boolean, Array, Object],
	default: [String, Number, Boolean, Array, Object],
	label: String,
	description: String,
	options: [String, Array],
	linkFilters: Object,
	documentList: Array,
	readOnly: [Boolean, Number],
	reqd: [Boolean, Number],
	hidden: {
		type: [Boolean, Number],
		default: false,
	},
	errorMessage: String,
	minDate: String,
	maxDate: String,
	addSectionPadding: {
		type: Boolean,
		default: true,
	},
})

const emit = defineEmits(["change", "update:modelValue"])
const dayjs = inject("$dayjs")

const showField = computed(() => {
	if (props.readOnly && !isLayoutField.value && !props.modelValue) return false

	return props.fieldtype !== "Table" && !props.hidden
})

const isNumberType = computed(() => {
	return ["Int", "Float"].includes(props.fieldtype)
})

const isLayoutField = computed(() => {
	return ["Section Break", "Column Break"].includes(props.fieldtype)
})

const isReadOnly = computed(() => {
	return Boolean(props.readOnly)
})

const formatDateTimeField = (value) => formatJalaliDateTime(value)

function getDatetimeDatePart(value) {
	if (!value) return ""
	return String(value).split(/[T ]/)[0]
}

function getDatetimeTimePart(value) {
	if (!value) return ""
	const [, time = ""] = String(value).split(/[T ]/)
	return time.slice(0, 5)
}

function buildDatetimeValue(datePart, timePart) {
	if (!datePart) return ""
	const normalizedTime = timePart ? `${timePart.slice(0, 5)}:00` : "00:00:00"
	return `${datePart} ${normalizedTime}`
}

function updateDatetimeDate(datePart) {
	const datetimeValue = buildDatetimeValue(
		datePart,
		getDatetimeTimePart(props.modelValue)
	)
	emit("update:modelValue", datetimeValue)
	emit("change", datetimeValue)
}

function updateDatetimeTime(timePart) {
	const datePart = getDatetimeDatePart(props.modelValue) || dayjs().format("YYYY-MM-DD")
	const datetimeValue = buildDatetimeValue(datePart, timePart)
	emit("update:modelValue", datetimeValue)
	emit("change", datetimeValue)
}

const selectionList = computed(() => {
	if (props.fieldtype === "Link" && props.documentList) {
		return props.documentList
	} else if (props.fieldtype == "Select" && props.options) {
		const options = props.options.split("\n")
		return options.map((option) => ({
			label: __(option),
			value: option,
		}))
	}

	return []
})

function setDefaultValue() {
	// set default values
	if (props.modelValue) return

	if (props.default) {
		if (props.fieldtype === "Check") {
			emit("update:modelValue", props.default === "1" ? true : false)
		} else if (props.fieldtype === "Date" && props.default === "Today") {
			emit("update:modelValue", dayjs().format("YYYY-MM-DD"))
		} else if (isNumberType.value) {
			emit("update:modelValue", parseFloat(props.default || 0))
		} else {
			emit("update:modelValue", props.default)
		}
	} else {
		props.fieldtype === "Check" ? emit("update:modelValue", false) : emit("update:modelValue", "")
	}
}

onMounted(() => {
	setDefaultValue()
})
</script>
