<template>
	<BaseLayout :pageTitle="pageTitle">
		<template #body>
			<div class="w-full max-w-5xl mx-auto mt-7 mb-7 p-4">
				<div v-if="!props.id" class="mb-4 grid grid-cols-2 gap-2 rounded-xl border border-slate-200 bg-white p-2">
					<button
						type="button"
						class="rounded-lg px-3 py-2 text-sm font-semibold transition"
						:class="
							entryType === 'event'
								? 'bg-slate-900 text-white'
								: 'bg-white text-slate-600 hover:bg-slate-50'
						"
						@click="entryType = 'event'"
					>
						{{ __("رویداد") }}
					</button>
					<button
						type="button"
						class="rounded-lg px-3 py-2 text-sm font-semibold transition"
						:class="
							entryType === 'reminder'
								? 'bg-slate-900 text-white'
								: 'bg-white text-slate-600 hover:bg-slate-50'
						"
						@click="entryType = 'reminder'"
					>
						{{ __("یادآور") }}
					</button>
				</div>

				<div v-if="!props.id && entryType === 'reminder'" class="rounded-xl border border-blue-100 bg-blue-50 p-4">
					<div class="text-sm font-semibold text-blue-900">
						{{ __("یادآور برای خودم") }}
					</div>
					<div class="mt-1 text-xs text-blue-700">
						{{ __("این یادآور فقط برای حساب کاربری شما ثبت می‌شود.") }}
					</div>

					<div class="mt-4 space-y-3">
						<div class="rounded-lg border border-blue-200 bg-white px-3 py-2 text-xs text-slate-600">
							{{ __("کاربر مقصد") }}: {{ reminderDoc.user || "-" }}
						</div>

							<div>
								<label class="mb-1 block text-xs font-medium text-slate-600">
									{{ __("زمان یادآوری") }}
								</label>
							<div class="space-y-2">
								<JalaliDatePicker
									:modelValue="reminderDatePart"
									:placeholder="__('انتخاب تاریخ')"
									@update:modelValue="updateReminderDate"
								/>
								<input
									type="time"
									:value="reminderTimePart"
									@input="(event) => updateReminderTime(event.target.value)"
									class="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-gray-500 focus:outline-none focus:ring-0"
								/>
								<div v-if="reminderDateTimeLabel" class="text-xs text-slate-500">
									{{ __("زمان انتخاب‌شده") }}: {{ reminderDateTimeLabel }}
								</div>
								</div>
							</div>

							<div class="rounded-lg border border-blue-200 bg-white px-3 py-3">
								<div class="flex items-center justify-between">
									<label class="text-xs font-medium text-slate-700">
										{{ __("تکرار یادآور") }}
									</label>
									<label class="inline-flex items-center gap-2 text-xs text-slate-600">
										<input
											v-model="reminderRepeatEnabled"
											type="checkbox"
											class="h-4 w-4 rounded border-gray-300 text-slate-900 focus:ring-0"
										/>
										{{ __("فعال") }}
									</label>
								</div>

								<div v-if="reminderRepeatEnabled" class="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
									<div>
										<label class="mb-1 block text-xs font-medium text-slate-600">
											{{ __("بازه تکرار") }}
										</label>
										<select
											v-model="reminderRepeatInterval"
											class="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-gray-500 focus:outline-none focus:ring-0"
										>
											<option value="daily">{{ __("روزانه") }}</option>
											<option value="weekly">{{ __("هفتگی") }}</option>
											<option value="monthly">{{ __("ماهانه") }}</option>
										</select>
									</div>
									<div>
										<label class="mb-1 block text-xs font-medium text-slate-600">
											{{ __("تعداد یادآور") }}
										</label>
										<input
											v-model.number="reminderRepeatCount"
											type="number"
											min="2"
											max="60"
											class="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-gray-500 focus:outline-none focus:ring-0"
										/>
									</div>
								</div>
							</div>

							<div>
								<label class="mb-1 block text-xs font-medium text-slate-600">
									{{ __("توضیحات") }}
							</label>
							<textarea
								v-model="reminderDoc.description"
								rows="3"
								class="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
								:placeholder="__('مثال: پیگیری جلسه یا ارسال گزارش')"
							/>
						</div>
					</div>

					<div class="mt-4 flex gap-2">
						<Button variant="outline" class="w-full py-5" @click="router.back()">
							{{ __("انصراف") }}
						</Button>
						<Button
							variant="solid"
							class="w-full py-5"
							:loading="createReminderDocResource.loading"
							@click="saveReminder"
						>
							{{ __("ثبت یادآور") }}
						</Button>
					</div>
				</div>

				<FormView
					v-else-if="formFields.data"
					doctype="Event"
					v-model="eventDoc"
					:isSubmittable="false"
					:returnOnCreate="true"
					returnOnCreateRoute="EventListView"
					:fields="formFields.data"
					:id="props.id"
					:showAttachmentView="true"
					@validateForm="validateForm"
					@afterSave="handleAfterSave"
				>
					<template #event_participants="{ isFormReadOnly }">
						<div class="rounded-xl border border-slate-100 bg-white p-4">
							<div class="mb-3 flex items-center justify-between">
								<div>
									<div class="text-sm font-semibold text-slate-900">
										{{ __("شرکت‌کنندگان رویداد") }}
									</div>
									<div class="mt-1 text-xs text-slate-500">
										{{ __("افراد یا موجودیت‌های مرتبط (کاربر، کارمند، مشتری، تامین‌کننده و ...) را اضافه کنید.") }}
									</div>
								</div>
								<Button
									v-if="!isFormReadOnly"
									variant="outline"
									size="sm"
									@click="addParticipantRow"
								>
									{{ __("افزودن") }}
								</Button>
							</div>

							<div v-if="eventDoc.event_participants?.length" class="space-y-3">
								<div
									v-for="(row, index) in eventDoc.event_participants"
									:key="row.name || `new-${index}`"
									class="rounded-lg border border-slate-100 p-3"
								>
									<div class="grid grid-cols-1 gap-3 md:grid-cols-2">
										<div>
											<label class="mb-1 block text-xs text-slate-500">
												{{ __("نوع سند مرجع") }}
											</label>
											<SearchableDropdown
												v-model="row.reference_doctype"
												:options="participantDoctypeOptions"
												:placeholder="__('انتخاب نوع')"
												:disabled="isFormReadOnly"
												@update:modelValue="() => handleParticipantDoctypeChange(row)"
											/>
										</div>
										<div>
											<label class="mb-1 block text-xs text-slate-500">
												{{ __("نام سند مرجع") }}
											</label>
											<Link
												:doctype="row.reference_doctype || 'DocType'"
												v-model="row.reference_docname"
												:disabled="isFormReadOnly || !row.reference_doctype"
											/>
										</div>
									</div>
									<div class="mt-2 flex items-center justify-between">
										<div class="text-xs text-slate-500">
											{{ row.email || __("ایمیل به‌صورت خودکار توسط سرور تکمیل می‌شود.") }}
										</div>
										<Button
											v-if="!isFormReadOnly"
											variant="ghost"
											size="sm"
											theme="red"
											@click="removeParticipantRow(index)"
										>
											{{ __("حذف") }}
										</Button>
									</div>
								</div>
							</div>
							<div v-else class="text-xs text-slate-500">
								{{ __("هنوز شرکت‌کننده‌ای اضافه نشده است.") }}
							</div>
						</div>
					</template>
				</FormView>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { Button, createResource, toast } from "frappe-ui"
import { computed, inject, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"

import BaseLayout from "@/components/BaseLayout.vue"
import FormView from "@/components/FormView.vue"
import JalaliDatePicker from "@/components/JalaliDatePicker.vue"
import Link from "@/components/Link.vue"
import SearchableDropdown from "@/components/SearchableDropdown.vue"
import { formatJalaliDateTime } from "@/utils/jalali"

const dayjs = inject("$dayjs")
const user = inject("$user")
const __ = inject("$translate")
const route = useRoute()
const router = useRouter()

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

const defaultEntryType = computed(() =>
	String(route.query?.mode || "").toLowerCase() === "reminder" ? "reminder" : "event"
)
const entryType = ref(defaultEntryType.value)
const pageTitle = computed(() => {
	if (props.id) return __("جزئیات رویداد")
	return entryType.value === "reminder" ? __("ثبت یادآور") : __("ثبت رویداد")
})
const initialParticipantKeys = ref(new Set())
const participantDoctypeOptions = [
	{ label: "کاربر", value: "User" },
	{ label: "کارمند", value: "Employee" },
	{ label: "تامین‌کننده", value: "Supplier" },
	{ label: "مشاور", value: "Consultant" },
	{ label: "مخاطب", value: "Contact" },
]

const eventDoc = ref({
	subject: "",
	event_type: "Private",
	event_category: "Event",
	all_day: 1,
	repeat_this_event: 0,
	repeat_on: "",
	repeat_till: "",
	monday: 0,
	tuesday: 0,
	wednesday: 0,
	thursday: 0,
	friday: 0,
	saturday: 0,
	sunday: 0,
	starts_on: dayjs().startOf("day").format("YYYY-MM-DD HH:mm:ss"),
	ends_on: dayjs().endOf("day").format("YYYY-MM-DD HH:mm:ss"),
	description: "",
	location: "",
	owner: user.data?.name || "",
	event_participants: [],
})

const reminderDoc = ref({
	user: user.data?.name || "",
	remind_at: dayjs().add(1, "hour").second(0).format("YYYY-MM-DD HH:mm:ss"),
	description: "",
})
const reminderDatePart = ref("")
const reminderTimePart = ref("09:00")
const reminderRepeatEnabled = ref(false)
const reminderRepeatInterval = ref("daily")
const reminderRepeatCount = ref(2)

const initialDateFromQuery = computed(() => {
	const queryDate = String(route.query?.date || "")
	return /^\d{4}-\d{2}-\d{2}$/.test(queryDate) ? queryDate : ""
})
const reminderDateTimeLabel = computed(() =>
	formatJalaliDateTime(reminderDoc.value.remind_at)
)

const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Event" },
	transform(data) {
		return getFilteredFields(data)
	},
	onSuccess() {
		applyDefaults()
		updateDateFieldTypes()
		updateRepeatFieldVisibility()
	},
})
formFields.reload()

watch(
	() => user.data?.name,
	() => {
		applyDefaults()
	},
	{ immediate: true }
)

watch(
	() => route.query?.date,
	(value) => {
		if (props.id) return
		const queryDate = String(value || "")
		if (!/^\d{4}-\d{2}-\d{2}$/.test(queryDate)) return
		eventDoc.value.starts_on = `${queryDate} 00:00:00`
		eventDoc.value.ends_on = `${queryDate} 23:59:59`
	},
	{ immediate: true }
)

watch(
	() => `${route.query?.mode || ""}|${route.query?.date || ""}`,
	() => {
		if (props.id) return
		entryType.value = defaultEntryType.value
		applyReminderDefaults()
	},
	{ immediate: true }
)

watch(
	() => user.data?.name,
	(userId) => {
		if (!userId) return
		reminderDoc.value.user = userId
	},
	{ immediate: true }
)

watch(
	() => entryType.value,
	(type) => {
		if (props.id || type !== "reminder") return
		applyReminderDefaults()
	}
)

watch(
	() => eventDoc.value.all_day,
	(isAllDayRaw) => {
		updateDateFieldTypes()
		const isAllDay = Number(isAllDayRaw) === 1 || isAllDayRaw === true
		if (isAllDay) {
			eventDoc.value.starts_on = normalizeDateTime(
				eventDoc.value.starts_on || dayjs().format("YYYY-MM-DD HH:mm:ss")
			)
			eventDoc.value.ends_on = normalizeDateTime(
				eventDoc.value.ends_on || eventDoc.value.starts_on
			)
			eventDoc.value.starts_on = `${String(eventDoc.value.starts_on).slice(0, 10)} 00:00:00`
			eventDoc.value.ends_on = `${String(eventDoc.value.ends_on).slice(0, 10)} 23:59:59`
			return
		}

		const startDate = String(
			eventDoc.value.starts_on || dayjs().format("YYYY-MM-DD HH:mm:ss")
		).slice(0, 10)
		const endDate = String(eventDoc.value.ends_on || startDate).slice(0, 10)
		if (/ 00:00:00$/.test(eventDoc.value.starts_on || "")) {
			eventDoc.value.starts_on = `${startDate} 09:00:00`
		}
		if (/ 23:59:59$/.test(eventDoc.value.ends_on || "")) {
			eventDoc.value.ends_on = `${endDate} 10:00:00`
		}
	},
	{ immediate: true }
)

watch(
	() => eventDoc.value.repeat_this_event,
	(enabledRaw) => {
		const enabled = Number(enabledRaw) === 1 || enabledRaw === true
		if (!enabled) {
			eventDoc.value.repeat_on = ""
			eventDoc.value.repeat_till = ""
			setWeeklyDays(false)
			updateRepeatFieldVisibility()
			return
		}

		if (!eventDoc.value.repeat_on) {
			eventDoc.value.repeat_on = "Weekly"
		}
		if (!eventDoc.value.repeat_till) {
			eventDoc.value.repeat_till = String(eventDoc.value.starts_on || "").slice(0, 10)
		}
		updateRepeatFieldVisibility()
	},
	{ immediate: true }
)

watch(
	() => eventDoc.value.repeat_on,
	(repeatOn) => {
		if (repeatOn !== "Weekly") {
			setWeeklyDays(false)
			updateRepeatFieldVisibility()
			return
		}

		if (!hasAnyWeeklyDaySelected()) {
			const weekdayField = getWeekdayFieldName(eventDoc.value.starts_on)
			if (weekdayField) {
				eventDoc.value[weekdayField] = 1
			}
		}
		updateRepeatFieldVisibility()
	}
)

watch(
	() => props.id,
	() => {
		initialParticipantKeys.value = new Set()
	},
	{ immediate: true }
)

watch(
	() => eventDoc.value?.event_participants,
	(rows) => {
		if (!props.id || initialParticipantKeys.value.size) return
		const keys = getParticipantKeys(rows || [])
		initialParticipantKeys.value = new Set(keys)
	},
	{ deep: true, immediate: true }
)

function getFilteredFields(fields = []) {
	const visible = new Set([
		"subject",
		"event_category",
		"event_type",
		"all_day",
		"repeat_this_event",
		"repeat_on",
		"repeat_till",
		"monday",
		"tuesday",
		"wednesday",
		"thursday",
		"friday",
		"saturday",
		"sunday",
		"starts_on",
		"ends_on",
		"location",
		"description",
		"event_participants",
	])

	return fields
		.filter((field) => visible.has(field.fieldname))
		.map((field) => {
			if (field.fieldname === "subject") {
				field.reqd = 1
			}
			if (field.fieldname === "event_type") {
				field.options = "Public\nPrivate"
				field.default = "Private"
			}
			if (field.fieldname === "event_category") {
				field.options = "Event\nMeeting\nCall\nSent/Received Email\nOther"
				field.default = "Event"
				field.label = __("نوع رویداد")
			}
			if (field.fieldname === "all_day") {
				field.default = "1"
			}
			if (field.fieldname === "repeat_this_event") {
				field.default = "0"
				field.label = __("تکرارپذیر")
			}
			if (field.fieldname === "repeat_on") {
				field.options = "Daily\nWeekly\nMonthly\nYearly"
			}
			if (field.fieldname === "repeat_till") {
				field.hidden = Number(eventDoc.value.repeat_this_event || 0) === 0
			}
			if (
				[
					"monday",
					"tuesday",
					"wednesday",
					"thursday",
					"friday",
					"saturday",
					"sunday",
				].includes(field.fieldname)
			) {
				field.hidden =
					Number(eventDoc.value.repeat_this_event || 0) === 0 ||
					eventDoc.value.repeat_on !== "Weekly"
			}
			if (field.fieldname === "starts_on" || field.fieldname === "ends_on") {
				const isAllDay = Number(eventDoc.value?.all_day ?? 0) === 1
				field.fieldtype = isAllDay ? "Date" : "Datetime"
			}
			return field
		})
}

function updateDateFieldTypes() {
	if (!Array.isArray(formFields.data)) return
	const isAllDay = Number(eventDoc.value?.all_day ?? 0) === 1
	formFields.data.forEach((field) => {
		if (field.fieldname === "starts_on" || field.fieldname === "ends_on") {
			field.fieldtype = isAllDay ? "Date" : "Datetime"
		}
	})
}

function updateRepeatFieldVisibility() {
	if (!Array.isArray(formFields.data)) return
	const isRepeatEnabled = Number(eventDoc.value?.repeat_this_event ?? 0) === 1
	const isWeekly = eventDoc.value?.repeat_on === "Weekly"

	formFields.data.forEach((field) => {
		if (field.fieldname === "repeat_till") {
			field.hidden = !isRepeatEnabled
		}
		if (
			[
				"monday",
				"tuesday",
				"wednesday",
				"thursday",
				"friday",
				"saturday",
				"sunday",
			].includes(field.fieldname)
		) {
			field.hidden = !(isRepeatEnabled && isWeekly)
		}
	})
}

function applyDefaults() {
	eventDoc.value.owner = eventDoc.value.owner || user.data?.name || ""
	eventDoc.value.event_type = eventDoc.value.event_type || "Private"
	eventDoc.value.event_category = eventDoc.value.event_category || "Event"
	eventDoc.value.all_day = Number(eventDoc.value.all_day ?? 1)
	eventDoc.value.repeat_this_event = Number(eventDoc.value.repeat_this_event ?? 0)
	eventDoc.value.repeat_on = eventDoc.value.repeat_on || ""
	eventDoc.value.repeat_till = eventDoc.value.repeat_till || ""
	eventDoc.value.monday = Number(eventDoc.value.monday ?? 0)
	eventDoc.value.tuesday = Number(eventDoc.value.tuesday ?? 0)
	eventDoc.value.wednesday = Number(eventDoc.value.wednesday ?? 0)
	eventDoc.value.thursday = Number(eventDoc.value.thursday ?? 0)
	eventDoc.value.friday = Number(eventDoc.value.friday ?? 0)
	eventDoc.value.saturday = Number(eventDoc.value.saturday ?? 0)
	eventDoc.value.sunday = Number(eventDoc.value.sunday ?? 0)
	const selectedDate = initialDateFromQuery.value
	eventDoc.value.starts_on =
		eventDoc.value.starts_on
		|| (selectedDate ? `${selectedDate} 00:00:00` : dayjs().startOf("day").format("YYYY-MM-DD HH:mm:ss"))
	eventDoc.value.ends_on =
		eventDoc.value.ends_on
		|| (selectedDate ? `${selectedDate} 23:59:59` : dayjs().endOf("day").format("YYYY-MM-DD HH:mm:ss"))
	if (!Array.isArray(eventDoc.value.event_participants)) {
		eventDoc.value.event_participants = []
	}
	applyReminderDefaults()
}

function applyReminderDefaults() {
	if (props.id) return
	reminderRepeatEnabled.value = false
	reminderRepeatInterval.value = "daily"
	reminderRepeatCount.value = 2
	reminderDoc.value.user = user.data?.name || reminderDoc.value.user || ""

	const queryDate = initialDateFromQuery.value
	if (queryDate) {
		reminderDoc.value.remind_at = `${queryDate} 09:00:00`
	}
	if (!reminderDoc.value.remind_at) {
		reminderDoc.value.remind_at = dayjs().add(1, "hour").second(0).format("YYYY-MM-DD HH:mm:ss")
	}
	syncReminderDateTimeParts()
}

function normalizeDateTime(value) {
	if (!value) return ""
	const normalized = String(value).replace("T", " ")
	if (/^\d{4}-\d{2}-\d{2}$/.test(normalized)) {
		return `${normalized} 00:00:00`
	}
	if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(normalized)) {
		return `${normalized}:00`
	}
	return normalized
}

function getDatePartFromDateTime(value) {
	const normalized = normalizeDateTime(value)
	return normalized ? normalized.slice(0, 10) : ""
}

function getTimePartFromDateTime(value) {
	const normalized = normalizeDateTime(value)
	if (!normalized) return ""
	const [, time = ""] = normalized.split(" ")
	return time.slice(0, 5)
}

function buildReminderDateTime(datePart, timePart) {
	if (!datePart) return ""
	const normalizedTime = /^\d{2}:\d{2}$/.test(String(timePart || ""))
		? `${timePart}:00`
		: "00:00:00"
	return `${datePart} ${normalizedTime}`
}

function syncReminderDateTimeParts() {
	reminderDatePart.value = getDatePartFromDateTime(reminderDoc.value.remind_at)
	reminderTimePart.value = getTimePartFromDateTime(reminderDoc.value.remind_at) || "09:00"
	reminderDoc.value.remind_at = buildReminderDateTime(
		reminderDatePart.value,
		reminderTimePart.value
	)
}

function updateReminderDate(datePart) {
	reminderDatePart.value = String(datePart || "").trim()
	reminderDoc.value.remind_at = buildReminderDateTime(
		reminderDatePart.value,
		reminderTimePart.value
	)
}

function updateReminderTime(timePart) {
	reminderTimePart.value = String(timePart || "").trim()
	reminderDoc.value.remind_at = buildReminderDateTime(
		reminderDatePart.value,
		reminderTimePart.value
	)
}

function buildReminderSchedule(remindAt) {
	const normalizedRemindAt = normalizeDateTime(remindAt)
	if (!normalizedRemindAt) return []

	const baseDate = dayjs(normalizedRemindAt)
	if (!baseDate.isValid()) return []

	if (!reminderRepeatEnabled.value) {
		return [normalizedRemindAt]
	}

	const repeatCount = Math.max(2, Math.min(60, Number(reminderRepeatCount.value || 2)))
	const intervalMap = {
		daily: "day",
		weekly: "week",
		monthly: "month",
	}
	const interval = intervalMap[reminderRepeatInterval.value] || "day"

	return Array.from({ length: repeatCount }, (_, index) =>
		baseDate.add(index, interval).format("YYYY-MM-DD HH:mm:ss")
	)
}

function normalizeParticipants() {
	const rows = Array.isArray(eventDoc.value.event_participants)
		? eventDoc.value.event_participants
		: []
	eventDoc.value.event_participants = rows
		.map((row) => ({
			...row,
			reference_doctype: String(row.reference_doctype || "").trim(),
			reference_docname: String(row.reference_docname || "").trim(),
		}))
		.filter((row) => row.reference_doctype && row.reference_docname)
}

function setWeeklyDays(isEnabled) {
	const value = isEnabled ? 1 : 0
	eventDoc.value.monday = value
	eventDoc.value.tuesday = value
	eventDoc.value.wednesday = value
	eventDoc.value.thursday = value
	eventDoc.value.friday = value
	eventDoc.value.saturday = value
	eventDoc.value.sunday = value
}

function hasAnyWeeklyDaySelected() {
	return [
		eventDoc.value.monday,
		eventDoc.value.tuesday,
		eventDoc.value.wednesday,
		eventDoc.value.thursday,
		eventDoc.value.friday,
		eventDoc.value.saturday,
		eventDoc.value.sunday,
	].some((value) => Number(value) === 1)
}

function getWeekdayFieldName(datetimeValue) {
	const date = normalizeDateTime(datetimeValue || dayjs().format("YYYY-MM-DD HH:mm:ss"))
	const weekday = dayjs(date).day()
	const dayMap = {
		0: "sunday",
		1: "monday",
		2: "tuesday",
		3: "wednesday",
		4: "thursday",
		5: "friday",
		6: "saturday",
	}
	return dayMap[weekday]
}

function validateForm() {
	applyDefaults()
	const isAllDay = Number(eventDoc.value.all_day ?? 0) === 1
	const isRepeatEnabled = Number(eventDoc.value.repeat_this_event ?? 0) === 1

	eventDoc.value.starts_on = normalizeDateTime(eventDoc.value.starts_on)
	eventDoc.value.ends_on = normalizeDateTime(eventDoc.value.ends_on)

	if (isAllDay) {
		const startDate = String(
			eventDoc.value.starts_on || dayjs().format("YYYY-MM-DD")
		).slice(0, 10)
		const endDate = String(eventDoc.value.ends_on || startDate).slice(0, 10)
		eventDoc.value.starts_on = `${startDate} 00:00:00`
		eventDoc.value.ends_on = `${endDate} 23:59:59`
	}

	if (
		!eventDoc.value.ends_on ||
		dayjs(eventDoc.value.ends_on).isBefore(dayjs(eventDoc.value.starts_on))
	) {
		eventDoc.value.ends_on = eventDoc.value.starts_on
	}

	if (eventDoc.value.event_category === "Event") {
		eventDoc.value.send_reminder = 1
	} else {
		eventDoc.value.send_reminder = 0
	}

	if (!isRepeatEnabled) {
		eventDoc.value.repeat_on = ""
		eventDoc.value.repeat_till = ""
		setWeeklyDays(false)
	} else {
		if (!eventDoc.value.repeat_on) {
			eventDoc.value.repeat_on = "Weekly"
		}
		if (!eventDoc.value.repeat_till) {
			eventDoc.value.repeat_till = String(eventDoc.value.ends_on || eventDoc.value.starts_on).slice(0, 10)
		}
		if (eventDoc.value.repeat_on === "Weekly" && !hasAnyWeeklyDaySelected()) {
			const weekdayField = getWeekdayFieldName(eventDoc.value.starts_on)
			if (weekdayField) {
				eventDoc.value[weekdayField] = 1
			}
		} else if (eventDoc.value.repeat_on !== "Weekly") {
			setWeeklyDays(false)
		}
	}

	normalizeParticipants()
}

function addParticipantRow() {
	if (!Array.isArray(eventDoc.value.event_participants)) {
		eventDoc.value.event_participants = []
	}
	eventDoc.value.event_participants.push({
		reference_doctype: "",
		reference_docname: "",
		email: "",
	})
}

function removeParticipantRow(index) {
	if (!Array.isArray(eventDoc.value.event_participants)) return
	eventDoc.value.event_participants.splice(index, 1)
}

function handleParticipantDoctypeChange(row) {
	if (!row) return
	row.reference_docname = ""
	row.email = ""
}

function getParticipantKeys(rows = []) {
	return rows
		.map((row) => {
			const doctype = String(row.reference_doctype || "").trim()
			const docname = String(row.reference_docname || "").trim()
			if (!(doctype && docname)) return null
			return `${doctype}::${docname}`
		})
		.filter(Boolean)
}

function getNewParticipants() {
	const currentKeys = new Set(getParticipantKeys(eventDoc.value.event_participants || []))
	const newKeys = [...currentKeys].filter((key) => !initialParticipantKeys.value.has(key))
	return newKeys.map((key) => {
		const [reference_doctype, reference_docname] = key.split("::")
		return { reference_doctype, reference_docname }
	})
}

const createReminderDocResource = createResource({
	url: "frappe.client.insert",
	auto: false,
})

const resolveUserIdResource = createResource({
	url: "frappe.client.get_value",
	auto: false,
})

const createNotificationResource = createResource({
	url: "frappe.client.insert",
	auto: false,
})

async function saveReminder() {
	const targetUser = user.data?.name || String(reminderDoc.value.user || "").trim()
	const remindAt = normalizeDateTime(reminderDoc.value.remind_at)
	const description = String(reminderDoc.value.description || "").trim()

	if (!targetUser) {
		toast({
			title: __("خطا"),
			text: __("شناسه کاربر جاری یافت نشد. لطفا یک بار از حساب خارج و دوباره وارد شوید."),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
		return
	}

	if (!remindAt) {
		toast({
			title: __("خطا"),
			text: __("لطفا زمان یادآوری را مشخص کنید."),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
		return
	}

	if (!description) {
		toast({
			title: __("خطا"),
			text: __("لطفا توضیحات یادآور را وارد کنید."),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
		return
	}

	const schedule = buildReminderSchedule(remindAt)
	if (!schedule.length) {
		toast({
			title: __("خطا"),
			text: __("زمان یادآوری معتبر نیست."),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
		return
	}

	try {
		for (const scheduleTime of schedule) {
			await createReminderDocResource.submit({
				doc: {
					doctype: "Reminder",
					user: targetUser,
					remind_at: scheduleTime,
					description,
				},
			})
		}

		toast({
			title: __("Success"),
			text:
				schedule.length > 1
					? __("{0} یادآور با موفقیت ثبت شد.", [schedule.length])
					: __("یادآور با موفقیت ثبت شد."),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
		router.push({ name: "Notifications" })
	} catch (error) {
		const message =
			(Array.isArray(error?.messages) && error.messages[0])
			|| (typeof error?.message === "string" ? error.message : "")
			|| __("ثبت یادآور ناموفق بود.")
		toast({
			title: __("خطا"),
			text: message,
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
	}
}

async function resolveParticipantUser(referenceDoctype, referenceDocname) {
	if (!referenceDoctype || !referenceDocname) return ""
	if (referenceDoctype === "User") return referenceDocname

	if (referenceDoctype === "Employee") {
		const data = await resolveUserIdResource.fetch({
			doctype: "Employee",
			filters: { name: referenceDocname },
			fieldname: "user_id",
		})
		return data?.user_id || ""
	}

	return ""
}

async function sendParticipantNotifications(savedDocName) {
	const newParticipants = getNewParticipants()
	if (!newParticipants.length) return

	const eventDate = String(eventDoc.value.starts_on || "").slice(0, 10)
	let sentCount = 0
	let failedCount = 0

	for (const participant of newParticipants) {
		const toUser = await resolveParticipantUser(
			participant.reference_doctype,
			participant.reference_docname
		)
		if (!toUser || toUser === user.data?.name) continue

		const message = __(
			"شما برای رویداد {0} در تاریخ {1} اضافه شدید.",
			[eventDoc.value.subject || savedDocName, eventDate || __("نامشخص")]
		)
		try {
			await createNotificationResource.submit({
				doc: {
					doctype: "PWA Notification",
					to_user: toUser,
					from_user: user.data?.name || "",
					message,
					reference_document_type: "Event",
					reference_document_name: savedDocName,
					read: 0,
				},
			})
			sentCount += 1
		} catch (_error) {
			failedCount += 1
		}
	}

	if (sentCount) {
		toast({
			title: __("اعلان ارسال شد"),
			text: __("{0} اعلان برای شرکت‌کنندگان جدید ارسال شد.", [sentCount]),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
	}

	if (failedCount) {
		toast({
			title: __("هشدار اعلان"),
			text: __("ارسال {0} اعلان به دلیل سطح دسترسی یا تنظیمات سرور انجام نشد.", [
				failedCount,
			]),
			icon: "alert-triangle",
			position: "bottom-center",
			iconClasses: "text-amber-500",
		})
	}
}

async function handleAfterSave(payload) {
	try {
		const savedDocName = payload?.doc?.name || props.id
		if (!savedDocName) return
		await sendParticipantNotifications(savedDocName)
		initialParticipantKeys.value = new Set(
			getParticipantKeys(eventDoc.value.event_participants || [])
		)
	} catch (_error) {
		toast({
			title: __("هشدار"),
			text: __("ذخیره رویداد انجام شد اما ارسال اعلان برخی شرکت‌کنندگان ناموفق بود."),
			icon: "alert-triangle",
			position: "bottom-center",
			iconClasses: "text-amber-500",
		})
	}
}
</script>
