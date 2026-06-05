<template>
	<BaseLayout :pageTitle="pageTitle">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-4">
				<div v-if="!canManage" class="bg-white rounded p-4 text-sm text-gray-600">
					{{ __("You are not allowed to manage newsletters.") }}
				</div>

				<template v-else>
					<div class="bg-white rounded p-4 grid grid-cols-1 gap-3">
						<div>
							<label class="block text-xs text-gray-600 mb-1">{{ __("Title") }}</label>
							<input
								v-model="form.title"
								type="text"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
								:placeholder="__('Type newsletter title')"
							/>
						</div>

						<div>
							<label class="block text-xs text-gray-600 mb-1">{{ __("Summary") }}</label>
							<textarea
								v-model="form.summary"
								rows="2"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
								:placeholder="__('Write a short summary for employees')"
							/>
						</div>

						<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
							<div>
								<label class="block text-xs text-gray-600 mb-1">{{ __("Schedule Publish Time") }}</label>
								<div class="grid grid-cols-1 gap-2">
									<JalaliDatePicker v-model="form.scheduled_publish_date" :minDate="todayDate" />
									<input
										v-model="form.scheduled_publish_time"
										type="time"
										class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
									/>
								</div>
							</div>
							<div>
								<label class="block text-xs text-gray-600 mb-1">{{ __("Expiry Time") }}</label>
								<div class="grid grid-cols-1 gap-2">
									<JalaliDatePicker v-model="form.expires_on_date" :minDate="todayDate" />
									<input
										v-model="form.expires_on_time"
										type="time"
										class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
									/>
								</div>
							</div>
						</div>

						<div>
							<label class="block text-xs text-gray-600 mb-1">{{ __("Audience Scope") }}</label>
							<select
								v-model="form.audience_mode"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
							>
								<option value="All Employees">{{ __("All Employees") }}</option>
								<option value="By Role">{{ __("By Role") }}</option>
								<option value="Specific Employees">{{ __("Specific Employees") }}</option>
							</select>
						</div>

						<div v-if="form.audience_mode === 'By Role'" class="rounded border border-gray-200 p-3">
							<div class="text-xs text-gray-600 mb-2">{{ __("Select Roles") }}</div>
							<div class="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-40 overflow-y-auto">
								<label
									v-for="role in roleOptions"
									:key="role.value"
									class="inline-flex items-center gap-2 text-sm text-gray-700"
								>
									<input
										type="checkbox"
										:checked="form.target_roles.includes(role.value)"
										@change="toggleSelection('target_roles', role.value)"
									/>
									{{ role.label }}
								</label>
							</div>

							<div class="mt-3 border-t border-gray-200 pt-3">
								<div class="text-xs text-gray-600 mb-2">
									{{ __("Employees in selected roles") }} ({{ toPersianDigits(roleMatchedEmployees.length) }})
								</div>
								<div v-if="!form.target_roles.length" class="text-xs text-gray-500">
									{{ __("Select at least one role to preview employees.") }}
								</div>
								<div v-else class="grid grid-cols-1 gap-2">
									<div
										v-for="group in roleEmployeeGroups"
										:key="group.role"
										class="rounded border border-gray-100 p-2"
									>
										<div class="text-xs font-semibold text-gray-800">
											{{ group.role_label }} · {{ toPersianDigits(group.employees.length) }}
										</div>
										<div v-if="group.employees.length" class="text-[11px] text-gray-600 mt-1">
											{{ group.employees.map((row) => row.employee_name || row.name).join("، ") }}
										</div>
										<div v-else class="text-[11px] text-gray-500 mt-1">
											{{ __("No employees found for this role.") }}
										</div>
									</div>
								</div>
							</div>

							<div class="mt-3 border-t border-gray-200 pt-3">
								<div class="flex items-center justify-between gap-2 mb-1">
									<div class="text-xs text-gray-600">{{ __("Exclude Employees") }}</div>
									<div class="text-[11px] text-gray-500">
										{{ __("Excluded") }}: {{ toPersianDigits(form.excluded_employees.length) }}
									</div>
								</div>
								<div class="text-[11px] text-gray-500 mb-2">
									{{ __("Exclude specific employees from selected roles.") }}
								</div>
								<div v-if="!roleMatchedEmployees.length" class="text-xs text-gray-500">
									{{ __("No employees available for exclusion.") }}
								</div>
								<div v-else class="grid grid-cols-1 gap-2 max-h-56 overflow-y-auto">
									<label
										v-for="employee in roleMatchedEmployees"
										:key="`exclude-${employee.name}`"
										class="inline-flex items-center gap-2 text-sm text-gray-700"
									>
										<input
											type="checkbox"
											:checked="form.excluded_employees.includes(employee.name)"
											@change="toggleSelection('excluded_employees', employee.name)"
										/>
										{{ employee.employee_name || employee.name }}
									</label>
								</div>
							</div>
						</div>

						<div v-if="form.audience_mode === 'Specific Employees'" class="rounded border border-gray-200 p-3">
							<div class="text-xs text-gray-600 mb-2">{{ __("Select Employees") }}</div>
							<input
								v-model="employeeSearch"
								type="text"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full mb-2"
								:placeholder="__('Search employee')"
							/>
							<div class="grid grid-cols-1 gap-2 max-h-56 overflow-y-auto">
								<label
									v-for="employee in filteredEmployees"
									:key="employee.name"
									class="inline-flex items-center gap-2 text-sm text-gray-700"
								>
									<input
										type="checkbox"
										:checked="form.target_employees.includes(employee.name)"
										@change="toggleSelection('target_employees', employee.name)"
									/>
									{{ employee.employee_name || employee.name }}
								</label>
							</div>
						</div>
					</div>

					<div class="bg-white rounded p-4 grid grid-cols-1 gap-3">
						<div>
							<label class="block text-xs text-gray-600 mb-1">{{ __("Cover Image") }}</label>
							<input
								type="file"
								accept="image/*"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
								@change="selectCoverImage"
							/>
						</div>
						<div>
							<label class="block text-xs text-gray-600 mb-1">{{ __("Cover Caption") }}</label>
							<input
								v-model="form.cover_caption"
								type="text"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
								:placeholder="__('Type image caption')"
							/>
						</div>
						<div v-if="coverPreview" class="rounded border border-gray-200 p-2">
							<img :src="coverPreview" alt="cover-preview" class="w-full max-h-64 object-cover rounded" />
							<div v-if="form.cover_caption" class="text-xs text-gray-600 mt-2">
								{{ form.cover_caption }}
							</div>
						</div>
						<div>
							<label class="block text-xs text-gray-600 mb-1">{{ __("Additional Images") }}</label>
							<input
								type="file"
								multiple
								accept="image/*"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
								@change="selectAdditionalImages"
							/>
							<div v-if="additionalImageNames.length" class="text-xs text-gray-600 mt-2">
								{{ additionalImageNames.join("، ") }}
							</div>
						</div>
					</div>

					<div class="bg-white rounded p-4">
						<div class="text-xs text-gray-600 mb-2">{{ __("Body Content") }}</div>
						<TextEditor
							:content="form.content"
							@change="(value) => (form.content = value)"
							:placeholder="__('Start writing your announcement...')"
							:bubbleMenu="true"
							:fixedMenu="true"
							editor-class="min-h-[280px] px-3 py-3 text-sm"
						/>
					</div>

					<div class="bg-white rounded p-4 grid grid-cols-1 gap-3">
						<div class="flex items-center justify-between gap-2">
							<div class="text-sm font-semibold text-gray-900">{{ __("Poll Components") }}</div>
							<Button variant="outline" size="sm" @click="addPoll">
								{{ __("Add Poll") }}
							</Button>
						</div>
						<div v-if="!form.polls.length" class="text-xs text-gray-500">
							{{ __("No poll added yet.") }}
						</div>
						<div
							v-for="(poll, pollIndex) in form.polls"
							:key="poll.local_id"
							class="rounded border border-gray-200 p-3"
						>
							<div class="flex items-center justify-between gap-2 mb-2">
								<div class="text-xs text-gray-500">
									{{ __("Poll") }} #{{ toPersianDigits(pollIndex + 1) }}
								</div>
								<Button variant="ghost" size="sm" @click="removePoll(pollIndex)">
									{{ __("Remove") }}
								</Button>
							</div>

							<input
								v-model="poll.question"
								type="text"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
								:placeholder="__('Type poll question')"
							/>

							<div class="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-2">
								<label class="inline-flex items-center gap-2 text-xs text-gray-700">
									<input v-model="poll.allow_multiple" type="checkbox" />
									{{ __("Allow multiple choices") }}
								</label>
								<label class="inline-flex items-center gap-2 text-xs text-gray-700">
									<input v-model="poll.is_private" type="checkbox" />
									{{ __("Private poll") }}
								</label>
								<label class="inline-flex items-center gap-2 text-xs text-gray-700">
									<input
										v-model="poll.show_voters"
										type="checkbox"
										:disabled="poll.is_private"
									/>
									{{ __("Show who voted") }}
								</label>
							</div>

							<div class="mt-2 grid grid-cols-1 gap-2">
								<div class="text-xs text-gray-600">{{ __("Poll options") }}</div>
								<div
									v-for="(option, optionIndex) in poll.options"
									:key="`${poll.local_id}-opt-${option.local_id}`"
									class="flex items-center gap-2"
								>
									<input
										v-model="option.option_text"
										type="text"
										class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm flex-1"
										:placeholder="`${__('Option')} ${toPersianDigits(optionIndex + 1)}`"
									/>
									<Button variant="ghost" size="sm" @click="removePollOption(pollIndex, optionIndex)">
										{{ __("Remove") }}
									</Button>
								</div>
								<Button variant="outline" size="sm" @click="addPollOption(pollIndex)">
									{{ __("Add option") }}
								</Button>
							</div>

							<div class="mt-2 rounded border border-dashed border-gray-300 p-2 bg-gray-50">
								<div class="text-[11px] text-gray-500">{{ __("Poll token for content") }}</div>
								<div class="text-xs text-gray-800 mt-1">
									{{ pollToken(poll) || __("Save newsletter first to generate poll token.") }}
								</div>
								<div class="flex gap-2 mt-2">
									<Button
										size="sm"
										variant="outline"
										:disabled="!pollToken(poll)"
										@click="insertPollTokenIntoBody(poll)"
									>
										{{ __("Insert token to body end") }}
									</Button>
								</div>
							</div>
						</div>
					</div>

					<div class="bg-white rounded p-4">
						<label class="inline-flex items-center gap-2 text-sm text-gray-700">
							<input v-model="form.send_push_notification" type="checkbox" />
							{{ __("Send push notification on publish") }}
						</label>
					</div>

					<ErrorMessage :message="errorMessage" />

					<div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
						<Button
							variant="outline"
							class="py-5 text-base w-full"
							:loading="saveResource.loading || isUploading"
							@click="submitForm('Draft')"
						>
							{{ __("Save Draft") }}
						</Button>
						<Button
							variant="outline"
							class="py-5 text-base w-full"
							:loading="saveResource.loading || isUploading"
							@click="submitForm('Scheduled')"
						>
							{{ __("Schedule Newsletter") }}
						</Button>
						<Button
							variant="solid"
							class="py-5 text-base w-full"
							:loading="saveResource.loading || isUploading"
							@click="submitForm('Published')"
						>
							{{ __("Publish Now") }}
						</Button>
					</div>
				</template>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, onBeforeUnmount, ref, watch } from "vue"
import { useRouter } from "vue-router"
import { createResource, ErrorMessage, TextEditor, toast } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import { FileAttachment } from "@/composables"
import JalaliDatePicker from "@/components/JalaliDatePicker.vue"
import { employees as employeesResource } from "@/data/employees"
import {
	extractErrorMessage,
	isNewsletterManager,
	normalizeNewsletter,
	normalizeStringArray,
	toDateTimeInput,
	toServerDateTime,
} from "@/data/newsletters"
import dayjs from "@/utils/dayjs"
import { toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")
const user = inject("$user")
const router = useRouter()

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

const form = ref({
	name: "",
	title: "",
	summary: "",
	content: "",
	cover_image: "",
	cover_caption: "",
	scheduled_publish_date: "",
	scheduled_publish_time: "09:00",
	expires_on_date: "",
	expires_on_time: "23:59",
	audience_mode: "All Employees",
	target_roles: [],
	target_employees: [],
	excluded_employees: [],
	polls: [],
	send_push_notification: true,
})

const roleOptions = ref([])
const employeeOptions = ref([])
const employeeSearch = ref("")
const coverFile = ref(null)
const coverPreview = ref("")
const additionalImageFiles = ref([])
const additionalImageNames = ref([])
const errorMessage = ref("")
const isUploading = ref(false)
let localPollCounter = 0

const canManage = computed(() => isNewsletterManager(user.data))
const todayDate = computed(() => dayjs().format("YYYY-MM-DD"))
const pageTitle = computed(() =>
	props.id ? __("Edit Newsletter") : __("Create Newsletter")
)
const roleLabelByValue = computed(() => {
	const pairs = roleOptions.value.map((row) => [row.value, row.label || row.value])
	return Object.fromEntries(pairs)
})
const filteredEmployees = computed(() => {
	const search = employeeSearch.value.trim().toLowerCase()
	if (!search) return employeeOptions.value
	return employeeOptions.value.filter((row) => {
		const name = String(row.employee_name || "").toLowerCase()
		const id = String(row.name || "").toLowerCase()
		return name.includes(search) || id.includes(search)
	})
})
const roleEmployeeGroups = computed(() => {
	return (form.value.target_roles || []).map((role) => ({
		role,
		role_label: roleLabel(role),
		employees: employeeOptions.value.filter((employee) => employee.roles.includes(role)),
	}))
})
const roleMatchedEmployees = computed(() => {
	const byName = new Map()
	for (const group of roleEmployeeGroups.value) {
		for (const employee of group.employees) {
			if (!byName.has(employee.name)) byName.set(employee.name, employee)
		}
	}
	return Array.from(byName.values())
})

const detailResource = createResource({
	url: "hrms.api.newsletter.get_newsletter_detail",
	auto: false,
})

const audienceOptionsResource = createResource({
	url: "hrms.api.newsletter.get_newsletter_audience_options",
	auto: false,
	onSuccess(data) {
		roleOptions.value = normalizeRoleOptions(data?.role_options || data?.roles || [])
		employeeOptions.value = (data?.employees || []).map((row) => ({
			name: row.name || row.employee,
			employee_name: row.employee_name || row.employee || row.name,
			designation: row.designation || "",
			roles: extractEmployeeRoles(row),
		}))
	},
	onError() {
		loadFallbackAudienceOptions()
	},
})

const saveResource = createResource({
	url: "hrms.api.newsletter.upsert_newsletter",
	auto: false,
})

if (props.id) {
	loadNewsletter(props.id)
}

watch(
	canManage,
	(allowed) => {
		if (allowed) audienceOptionsResource.reload()
	},
	{ immediate: true }
)

watch(
	roleMatchedEmployees,
	(rows) => {
		const validEmployeeNames = new Set(rows.map((row) => row.name))
		form.value.excluded_employees = (form.value.excluded_employees || []).filter((employee) =>
			validEmployeeNames.has(employee)
		)
	},
	{ deep: true }
)

function loadNewsletter(newsletterName) {
	detailResource.fetch(
		{ newsletter_name: newsletterName, include_report: 1 },
		{
			onSuccess(data) {
				applyNewsletter(data?.newsletter || data)
			},
			onError(error) {
				errorMessage.value = extractErrorMessage(error, __("Failed to load newsletter details."))
			},
		}
	)
}

function applyNewsletter(data) {
	const newsletter = normalizeNewsletter(data || {})
	const scheduled = splitDateTimeInput(newsletter.scheduled_publish_at)
	const expires = splitDateTimeInput(newsletter.expires_on)

	form.value = {
		name: newsletter.name || "",
		title: newsletter.title || "",
		summary: newsletter.summary || "",
		content: newsletter.content || "",
		cover_image: newsletter.cover_image || "",
		cover_caption: newsletter.cover_caption || "",
		scheduled_publish_date: scheduled.date,
		scheduled_publish_time: scheduled.time || "09:00",
		expires_on_date: expires.date,
		expires_on_time: expires.time || "23:59",
		audience_mode: newsletter.audience_mode || "All Employees",
		target_roles: newsletter.target_roles || [],
		target_employees: newsletter.target_employees || [],
		excluded_employees: newsletter.excluded_employees || [],
		polls: normalizePolls(newsletter.polls || []),
		send_push_notification: newsletter.send_push_notification !== false,
	}
	coverPreview.value = newsletter.cover_image || ""
}

function selectCoverImage(event) {
	const file = event?.target?.files?.[0]
	if (!file) return

	if (coverPreview.value?.startsWith("blob:")) {
		URL.revokeObjectURL(coverPreview.value)
	}

	coverFile.value = file
	coverPreview.value = URL.createObjectURL(file)
}

function selectAdditionalImages(event) {
	const files = Array.from(event?.target?.files || [])
	additionalImageFiles.value = files
	additionalImageNames.value = files.map((file) => file.name)
}

function toggleSelection(fieldname, value) {
	const selectedValues = new Set(form.value[fieldname] || [])
	if (selectedValues.has(value)) selectedValues.delete(value)
	else selectedValues.add(value)
	form.value[fieldname] = Array.from(selectedValues)
}

function submitForm(status) {
	if (!canManage.value) return
	errorMessage.value = ""

	const validationError = validateForm(status)
	if (validationError) {
		errorMessage.value = validationError
		return
	}

	const payload = {
		name: form.value.name || undefined,
		title: form.value.title?.trim(),
		summary: form.value.summary?.trim() || "",
		content: form.value.content || "",
		cover_image: form.value.cover_image || "",
		cover_caption: form.value.cover_caption || "",
		scheduled_publish_at: toServerDateTimeFromParts(
			form.value.scheduled_publish_date,
			form.value.scheduled_publish_time
		),
		expires_on: toServerDateTimeFromParts(
			form.value.expires_on_date,
			form.value.expires_on_time
		),
		audience_mode: form.value.audience_mode,
		target_roles: form.value.audience_mode === "By Role" ? form.value.target_roles : [],
		target_employees:
			form.value.audience_mode === "Specific Employees"
				? form.value.target_employees
				: [],
		excluded_employees:
			form.value.audience_mode === "By Role" ? form.value.excluded_employees : [],
		polls: serializePollsPayload(form.value.polls || []),
		send_push_notification: form.value.send_push_notification ? 1 : 0,
		status,
	}

	saveResource.submit(
		{
			payload: JSON.stringify(payload),
		},
		{
			onSuccess: async (data) => {
				const saved = normalizeNewsletter(data || {})
				form.value.name = saved.name || form.value.name
				form.value.polls = normalizePolls(saved.polls || form.value.polls || [])

				await uploadSelectedImages(saved.name || form.value.name)
				successToast(status)

				if (!props.id && (saved.name || form.value.name)) {
					router.replace({
						name: "NewsletterEditView",
						params: { id: saved.name || form.value.name },
					})
					return
				}

				if (status === "Published") {
					router.push({ name: "NewslettersDashboard" })
				}
			},
			onError(error) {
				errorMessage.value = extractErrorMessage(error, __("Failed to save newsletter."))
			},
		}
	)
}

function validateForm(status) {
	if (!form.value.title?.trim()) return __("Title is required.")
	if (!form.value.content?.trim()) return __("Content is required.")

	if (status === "Scheduled") {
		if (!form.value.scheduled_publish_date) return __("Schedule publish time is required.")
		const scheduleDatetime = toServerDateTimeFromParts(
			form.value.scheduled_publish_date,
			form.value.scheduled_publish_time
		)
		if (!scheduleDatetime) return __("Schedule publish time is required.")
		if (dayjs(scheduleDatetime).isBefore(dayjs())) {
			return __("Schedule publish time must be in the future.")
		}
	}

	if (form.value.audience_mode === "By Role" && !form.value.target_roles.length) {
		return __("Please select at least one role.")
	}

	if (
		form.value.audience_mode === "Specific Employees" &&
		!form.value.target_employees.length
	) {
		return __("Please select at least one employee.")
	}

	for (const poll of form.value.polls || []) {
		const question = String(poll.question || "").trim()
		if (!question) continue
		const validOptions = (poll.options || [])
			.map((row) => String(row.option_text || "").trim())
			.filter(Boolean)
		if (validOptions.length < 2) {
			return __("Each poll must have at least two options.")
		}
	}

	return ""
}

function splitDateTimeInput(value) {
	const input = toDateTimeInput(value)
	if (!input) return { date: "", time: "" }

	const [datePart, timePart = ""] = input.split("T")
	return {
		date: datePart || "",
		time: String(timePart || "").slice(0, 5),
	}
}

function toServerDateTimeFromParts(datePart, timePart) {
	if (!datePart) return ""
	const normalizedTime = String(timePart || "00:00").slice(0, 5)
	return toServerDateTime(`${datePart}T${normalizedTime}`)
}

function extractEmployeeRoles(row = {}) {
	const roleList = new Set()
	normalizeStringArray(row?.roles).forEach((role) => roleList.add(role))
	normalizeStringArray(row?.user_roles).forEach((role) => roleList.add(role))
	normalizeStringArray(row?.assigned_roles).forEach((role) => roleList.add(role))

	if (row?.role) roleList.add(row.role)
	if (row?.designation) roleList.add(row.designation)
	if (row?.designation_name) roleList.add(row.designation_name)

	return Array.from(roleList).filter(Boolean)
}

function normalizeRoleOptions(options = []) {
	const sourceRows = Array.isArray(options) ? options : []
	const roleMap = new Map()

	for (const row of sourceRows) {
		if (typeof row !== "string") continue
		const value = String(row || "").trim()
		if (!value) continue
		roleMap.set(value, __(value))
	}

	for (const row of sourceRows) {
		if (!row || typeof row !== "object") continue
		const value = String(row.value || row.role || "").trim()
		if (!value) continue
		const translatedLabel = __(value)
		const serverLabel = String(row.label || row.role_label || "").trim()
		const label = translatedLabel !== value ? translatedLabel : serverLabel || value
		roleMap.set(value, label)
	}

	return Array.from(roleMap.entries())
		.map(([value, label]) => ({ value, label }))
		.sort((a, b) => a.label.localeCompare(b.label, "fa"))
}

function roleLabel(role) {
	return roleLabelByValue.value[role] || __(role) || role
}

function normalizePolls(rows = []) {
	return (rows || []).map((row, index) => ({
		local_id: nextPollLocalId(index),
		name: row.name || "",
		question: row.question || "",
		allow_multiple: Boolean(row.allow_multiple),
		is_private: Boolean(row.is_private),
		show_voters: row.is_private ? false : row.show_voters !== false,
		options: normalizePollOptions(row.options || []),
	}))
}

function normalizePollOptions(options = []) {
	const rows = (options || [])
		.map((option, index) => ({
			local_id: nextPollLocalId(index),
			option_text: String(option.option_text || option.value || option.label || "").trim(),
		}))
		.filter((row) => row.option_text)

	if (rows.length >= 2) return rows
	return [
		{ local_id: nextPollLocalId(0), option_text: rows[0]?.option_text || "" },
		{ local_id: nextPollLocalId(1), option_text: rows[1]?.option_text || "" },
	]
}

function serializePollsPayload(polls = []) {
	return (polls || [])
		.map((poll) => ({
			name: poll.name || undefined,
			question: String(poll.question || "").trim(),
			allow_multiple: poll.allow_multiple ? 1 : 0,
			is_private: poll.is_private ? 1 : 0,
			show_voters: poll.is_private ? 0 : poll.show_voters ? 1 : 0,
			options: (poll.options || [])
				.map((option) => ({
					option_text: String(option.option_text || "").trim(),
				}))
				.filter((option) => option.option_text),
		}))
		.filter((poll) => poll.question)
}

function nextPollLocalId(seed = 0) {
	localPollCounter += 1
	return `poll-${Date.now()}-${seed}-${localPollCounter}`
}

function addPoll() {
	form.value.polls = [
		...(form.value.polls || []),
		{
			local_id: nextPollLocalId(),
			name: "",
			question: "",
			allow_multiple: false,
			is_private: false,
			show_voters: true,
			options: normalizePollOptions([]),
		},
	]
}

function removePoll(pollIndex) {
	const polls = [...(form.value.polls || [])]
	polls.splice(pollIndex, 1)
	form.value.polls = polls
}

function addPollOption(pollIndex) {
	const poll = form.value.polls?.[pollIndex]
	if (!poll) return
	poll.options = [
		...(poll.options || []),
		{
			local_id: nextPollLocalId(),
			option_text: "",
		},
	]
}

function removePollOption(pollIndex, optionIndex) {
	const poll = form.value.polls?.[pollIndex]
	if (!poll) return
	const options = [...(poll.options || [])]
	if (options.length <= 2) return
	options.splice(optionIndex, 1)
	poll.options = options
}

function pollToken(poll) {
	const name = String(poll?.name || "").trim()
	if (!name) return ""
	return `[[POLL:${name}]]`
}

function insertPollTokenIntoBody(poll) {
	const token = pollToken(poll)
	if (!token) return
	const previousContent = String(form.value.content || "").trim()
	form.value.content = previousContent ? `${previousContent}\n<p>${token}</p>` : `<p>${token}</p>`
	toast({
		title: __("Success"),
		text: __("Poll token inserted at the end of body content."),
		icon: "check-circle",
		position: "bottom-center",
		iconClasses: "text-green-500",
	})
}

async function loadFallbackAudienceOptions() {
	try {
		if (!employeesResource.data) await employeesResource.reload()
	} catch (_error) {
		// fallback تلاش می‌کند در صورت امکان گزینه‌ها را پر کند
	}

	const fallbackEmployees = (employeesResource.data || []).map((row) => ({
		name: row.name,
		employee_name: row.employee_name || row.name,
		designation: row.designation || "",
		roles: extractEmployeeRoles(row),
	}))

	if (!fallbackEmployees.length) return

	employeeOptions.value = fallbackEmployees
	roleOptions.value = normalizeRoleOptions(
		Array.from(new Set(fallbackEmployees.flatMap((row) => row.roles || []).filter(Boolean)))
	)
}

async function uploadSelectedImages(newsletterName) {
	if (!newsletterName) return
	if (!coverFile.value && !additionalImageFiles.value.length) return

	isUploading.value = true
	try {
		if (coverFile.value) {
			const coverUpload = await new FileAttachment(coverFile.value).upload(
				"HR Newsletter",
				newsletterName,
				"cover_image"
			)
			form.value.cover_image = coverUpload?.file_url || form.value.cover_image
			coverFile.value = null
		}

		for (const file of additionalImageFiles.value) {
			await new FileAttachment(file).upload("HR Newsletter", newsletterName, "attachments")
		}
		additionalImageFiles.value = []
		additionalImageNames.value = []
	} finally {
		isUploading.value = false
	}
}

function successToast(status) {
	const messageMap = {
		Draft: __("Newsletter draft saved."),
		Scheduled: __("Newsletter scheduled successfully."),
		Published: __("Newsletter published successfully."),
	}
	toast({
		title: __("Success"),
		text: messageMap[status] || __("Newsletter saved successfully."),
		icon: "check-circle",
		position: "bottom-center",
		iconClasses: "text-green-500",
	})
}

onBeforeUnmount(() => {
	if (coverPreview.value?.startsWith("blob:")) {
		URL.revokeObjectURL(coverPreview.value)
	}
})
</script>
