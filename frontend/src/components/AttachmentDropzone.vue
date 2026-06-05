<template>
	<div class="bg-white rounded-xl border border-gray-100 p-4 space-y-3">
		<label v-if="label" class="block text-xs text-gray-600">{{ label }}</label>

		<div
			class="rounded-lg border-2 border-dashed p-4 text-center cursor-pointer transition"
			:class="[
				dragActive ? 'border-amber-400 bg-amber-50' : 'border-gray-300 hover:border-gray-400',
				disabled ? 'opacity-60 cursor-not-allowed' : '',
			]"
			role="button"
			tabindex="0"
			@click="openPicker"
			@keydown.enter.prevent="openPicker"
			@keydown.space.prevent="openPicker"
			@dragenter.prevent="onDragEnter"
			@dragover.prevent="onDragEnter"
			@dragleave.prevent="onDragLeave"
			@drop.prevent="onDrop"
		>
			<div class="text-sm text-gray-700">
				{{ __('برای انتخاب فایل کلیک کنید یا فایل را اینجا رها کنید') }}
			</div>
			<div class="text-[11px] text-gray-500 mt-1">
				{{ hintText }}
			</div>
		</div>

		<input
			ref="fileInputRef"
			type="file"
			class="hidden"
			:accept="accept"
			:multiple="multiple"
			:disabled="disabled"
			@change="onFileInputChange"
		/>

		<div v-if="files.length" class="space-y-1">
			<div class="text-[11px] text-gray-500">{{ __('فایل‌های انتخاب‌شده') }}</div>
			<div
				v-for="file in files"
				:key="fileKey(file)"
				class="flex items-center justify-between rounded-md bg-gray-50 px-2 py-1 text-xs"
			>
				<span class="truncate max-w-[70%]">{{ file.name }}</span>
				<button
					type="button"
					class="text-rose-600"
					@click.stop="removeSelectedFile(file)"
				>
					{{ __('حذف') }}
				</button>
			</div>
		</div>

		<div v-if="existingFiles.length" class="space-y-1 pt-2 border-t border-gray-100">
			<div class="text-[11px] text-gray-500">{{ __('فایل‌های پیوست‌شده') }}</div>
			<div
				v-for="file in existingFiles"
				:key="file.name"
				class="flex items-center justify-between rounded-md bg-gray-50 px-2 py-1 text-xs"
			>
				<a
					:href="file.file_url"
					target="_blank"
					rel="noopener noreferrer"
					class="truncate max-w-[70%] text-amber-700 underline"
				>
					{{ file.file_name || file.name }}
				</a>
				<button
					v-if="allowExistingRemove"
					type="button"
					class="text-rose-600"
					@click.stop="$emit('remove-existing', file)"
				>
					{{ __('حذف') }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, inject, ref } from "vue"

const props = defineProps({
	modelValue: {
		type: Array,
		default: () => [],
	},
	existingFiles: {
		type: Array,
		default: () => [],
	},
	label: {
		type: String,
		default: "",
	},
	accept: {
		type: String,
		default: "*/*",
	},
	multiple: {
		type: Boolean,
		default: true,
	},
	maxFileSizeMB: {
		type: Number,
		default: 5,
	},
	disabled: {
		type: Boolean,
		default: false,
	},
	allowExistingRemove: {
		type: Boolean,
		default: false,
	},
})

const emit = defineEmits(["update:modelValue", "error", "remove-existing"])

const fileInputRef = ref(null)
const dragActive = ref(false)
const __ = inject("$translate", (text, values = []) => {
	if (!Array.isArray(values) || !values.length) return text
	return text.replace(/\{(\d+)\}/g, (_, idx) => values[Number(idx)] ?? "")
})

const files = computed({
	get: () => props.modelValue || [],
	set: (value) => emit("update:modelValue", value),
})

const hintText = computed(() => {
	const suffix = props.accept === "*/*" ? __("همه نوع فایل") : props.accept
	return `${__("حداکثر حجم هر فایل")}: ${props.maxFileSizeMB}MB · ${suffix}`
})

function openPicker() {
	if (props.disabled) return
	fileInputRef.value?.click()
}

function onDragEnter() {
	if (props.disabled) return
	dragActive.value = true
}

function onDragLeave() {
	dragActive.value = false
}

function onDrop(event) {
	dragActive.value = false
	if (props.disabled) return
	appendFiles(event?.dataTransfer?.files)
}

function onFileInputChange(event) {
	appendFiles(event?.target?.files)
	event.target.value = ""
}

function appendFiles(fileList) {
	const incoming = Array.from(fileList || [])
	if (!incoming.length) return

	const filtered = incoming.filter(validateFile)
	if (!filtered.length) return

	const unique = [...files.value]
	for (const file of filtered) {
		if (!unique.find((existing) => fileKey(existing) === fileKey(file))) {
			unique.push(file)
		}
	}

	files.value = props.multiple ? unique : unique.slice(-1)
}

function validateFile(file) {
	const maxBytes = props.maxFileSizeMB * 1024 * 1024
	if (file.size > maxBytes) {
		emit("error", __("حجم فایل از حد مجاز بیشتر است: {0}", [file.name]))
		return false
	}

	if (props.accept === "*/*") return true
	const accepted = props.accept
		.split(",")
		.map((entry) => entry.trim().toLowerCase())
		.filter(Boolean)

	if (!accepted.length) return true

	const mime = (file.type || "").toLowerCase()
	const name = (file.name || "").toLowerCase()
	const isAllowed = accepted.some((rule) => {
		if (rule === "*/*") return true
		if (rule.endsWith("/*")) {
			const major = rule.slice(0, -1)
			return mime.startsWith(major)
		}
		if (rule.startsWith(".")) return name.endsWith(rule)
		return mime === rule
	})

	if (!isAllowed) {
		emit("error", __("نوع فایل مجاز نیست: {0}", [file.name]))
	}
	return isAllowed
}

function removeSelectedFile(file) {
	files.value = files.value.filter((entry) => fileKey(entry) !== fileKey(file))
}

function fileKey(file) {
	return `${file.name}-${file.size}-${file.lastModified || 0}`
}
</script>
