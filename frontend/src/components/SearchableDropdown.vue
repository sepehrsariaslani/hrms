<template>
	<div ref="rootRef" class="relative">
		<button
			type="button"
			class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm text-right bg-white flex items-center justify-between"
			:class="disabled ? 'opacity-60 cursor-not-allowed' : 'hover:border-gray-300'"
			:disabled="disabled"
			@click="toggleOpen"
		>
			<span class="truncate" :class="selectedLabel ? 'text-gray-800' : 'text-gray-400'">
				{{ selectedLabel || placeholder }}
			</span>
			<span class="text-gray-400 text-xs">{{ isOpen ? "▲" : "▼" }}</span>
		</button>

		<div
			v-if="isOpen"
			class="absolute z-50 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg overflow-hidden"
		>
			<div class="p-2 border-b border-gray-100">
				<div class="relative">
					<input
						v-model="searchQuery"
						type="text"
						class="w-full rounded-md border border-gray-200 px-3 py-2 pl-9 text-sm"
						:placeholder="__('جستجو...')"
						@keydown.esc.prevent="close"
					/>
					<button
						v-if="searchQuery"
						type="button"
						class="absolute left-1 top-1/2 -translate-y-1/2 w-7 h-7 rounded text-gray-500 hover:bg-gray-100"
						:title="__('پاک کردن جستجو')"
						@click="searchQuery = ''"
					>
						×
					</button>
				</div>
			</div>

			<div class="max-h-56 overflow-auto py-1">
				<button
					v-for="option in filteredOptions"
					:key="String(option.value)"
					type="button"
					class="w-full text-right px-3 py-2 text-sm hover:bg-amber-50 flex items-center justify-between"
					@click="selectOption(option.value)"
				>
					<span class="truncate">{{ option.label }}</span>
					<span v-if="isSelected(option.value)" class="text-amber-600">✓</span>
				</button>
				<div v-if="!filteredOptions.length" class="px-3 py-2 text-xs text-gray-500">
					{{ __("نتیجه‌ای پیدا نشد") }}
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, inject, onBeforeUnmount, onMounted, ref } from "vue"

const props = defineProps({
	modelValue: {
		type: [String, Number],
		default: "",
	},
	options: {
		type: Array,
		default: () => [],
	},
	placeholder: {
		type: String,
		default: "",
	},
	labelKey: {
		type: String,
		default: "label",
	},
	valueKey: {
		type: String,
		default: "value",
	},
	disabled: {
		type: Boolean,
		default: false,
	},
	includeEmptyOption: {
		type: Boolean,
		default: false,
	},
	emptyLabel: {
		type: String,
		default: "",
	},
})

const emit = defineEmits(["update:modelValue"])
const __ = inject("$translate", (text) => text)

const rootRef = ref(null)
const isOpen = ref(false)
const searchQuery = ref("")

const normalizedOptions = computed(() => {
	const mapped = (props.options || []).map((option) => {
		if (option && typeof option === "object") {
			const label = option[props.labelKey] ?? option.label ?? option.value ?? ""
			const value = option[props.valueKey] ?? option.value ?? option.label ?? ""
			return {
				label: String(label || value || ""),
				value,
			}
		}
		return {
			label: String(option ?? ""),
			value: option,
		}
	})

	if (props.includeEmptyOption) {
		mapped.unshift({ label: props.emptyLabel || "", value: "" })
	}

	return mapped
})

const filteredOptions = computed(() => {
	const query = searchQuery.value.trim().toLowerCase()
	if (!query) return normalizedOptions.value
	return normalizedOptions.value.filter((option) => {
		return (
			String(option.label || "")
				.toLowerCase()
				.includes(query) ||
			String(option.value || "")
				.toLowerCase()
				.includes(query)
		)
	})
})

const selectedLabel = computed(() => {
	const match = normalizedOptions.value.find(
		(option) => String(option.value ?? "") === String(props.modelValue ?? "")
	)
	if (match) return match.label
	if (props.modelValue === null || props.modelValue === undefined || props.modelValue === "") {
		return ""
	}
	return String(props.modelValue)
})

function isSelected(value) {
	return String(value ?? "") === String(props.modelValue ?? "")
}

function selectOption(value) {
	emit("update:modelValue", value ?? "")
	close()
}

function toggleOpen() {
	if (props.disabled) return
	isOpen.value = !isOpen.value
	if (!isOpen.value) searchQuery.value = ""
}

function close() {
	isOpen.value = false
	searchQuery.value = ""
}

function onDocumentClick(event) {
	if (!isOpen.value) return
	if (!rootRef.value?.contains(event.target)) {
		close()
	}
}

onMounted(() => {
	document.addEventListener("mousedown", onDocumentClick)
})

onBeforeUnmount(() => {
	document.removeEventListener("mousedown", onDocumentClick)
})
</script>
