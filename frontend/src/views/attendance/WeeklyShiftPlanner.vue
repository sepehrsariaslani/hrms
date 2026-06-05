<template>
	<BaseLayout :pageTitle="'برنامه شیفت هفتگی'">
		<template #body>
			<div class="flex flex-col p-4 gap-4 mb-8">
				<div class="bg-white rounded-lg p-3 border border-gray-100 flex items-center justify-between">
					<Button variant="subtle" icon="chevron-right" @click="shiftWeek(-1)" />
					<div class="text-sm font-semibold text-gray-900">
						{{ weekLabel }}
					</div>
					<Button variant="subtle" icon="chevron-left" @click="shiftWeek(1)" />
				</div>

				<div
					v-if="manageableEmployees.length > 1"
					class="bg-white rounded-lg p-3 border border-gray-100 flex flex-col gap-2"
				>
					<div class="text-xs text-gray-600">کارمند</div>
					<SearchableDropdown
						v-model="selectedEmployee"
						:options="manageableEmployeeOptions"
						placeholder="انتخاب کارمند"
						:disabled="isLoading"
						@update:modelValue="onEmployeeChange"
					/>
				</div>

				<div class="bg-white rounded-lg p-3 border border-gray-100">
					<div class="flex items-center justify-between mb-2">
						<div class="text-xs text-gray-600">وضعیت</div>
						<div class="text-xs font-semibold" :class="statusClass">{{ statusLabel }}</div>
					</div>
					<div class="text-xs text-gray-600">
						حداقل {{ toPersianDigits(String(rules.required_days_per_week || 6)) }} روز و
						{{ toPersianDigits(String(rules.minimum_hours_per_week || 48)) }} ساعت در هفته
					</div>
					<div
						v-if="rules.official_holidays_in_week"
						class="mt-1 text-[11px] text-amber-700"
					>
						این هفته {{ toPersianDigits(String(rules.official_holidays_in_week)) }} تعطیلی رسمی ثبت شده و
						حداقل ساعت/روز به صورت خودکار کاهش یافته است.
					</div>
					<div class="mt-2 text-xs text-gray-700">
						روز انتخاب‌شده: {{ toPersianDigits(String(selectedDaysCount)) }}
						|
						ساعات کل: {{ toPersianDigits(totalHours.toFixed(1)) }}
					</div>
					<div
						v-if="hasFinalizedAssignments && !planDoc"
						class="mt-1 text-[11px] text-emerald-700"
					>
						برنامه این هفته توسط تعیین‌کننده شیفت نهایی شده و فقط قابل مشاهده است.
					</div>
				</div>

				<div
					v-if="hasFinalizedAssignments"
					class="bg-white rounded-lg p-3 border border-emerald-200"
				>
					<div class="text-sm font-semibold text-gray-900">شیفت‌های تاییدشده این هفته</div>
					<div class="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
						<div
							v-for="item in finalizedShiftRows"
							:key="item.key"
							class="rounded border border-gray-200 px-2.5 py-2"
						>
							<div class="text-xs font-semibold text-gray-900">
								{{ item.dateLabel }}
							</div>
							<div class="mt-1 text-[11px] text-gray-600">
								{{ item.slotLabel }}
							</div>
							<router-link
								v-if="canRequestShiftChange"
								:to="buildShiftChangeRequestRoute(item)"
								class="mt-2 inline-flex items-center rounded border border-gray-300 px-2 py-1 text-[11px] font-medium text-gray-700 hover:bg-gray-50"
							>
								درخواست تغییر همین شیفت
							</router-link>
						</div>
					</div>
				</div>

				<div v-if="isLoading" class="bg-white rounded-lg p-4 text-sm text-gray-600">
					در حال بارگذاری...
				</div>

				<div v-else class="flex flex-col gap-3">
					<!-- Mobile -->
					<div class="md:hidden bg-white rounded-lg border border-gray-100 overflow-hidden">
						<div class="grid grid-cols-3 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-700">
							<div class="p-2">روز</div>
							<div class="p-2">صبح</div>
							<div class="p-2">عصر</div>
						</div>
						<div
							v-for="day in weekDays"
							:key="`mobile-${day.date}`"
							class="grid grid-cols-3 border-b border-gray-100 last:border-b-0"
						>
							<div class="p-2 text-xs text-gray-800 border-l border-gray-100">
								<div>{{ day.label }}</div>
								<div class="text-gray-500">{{ day.jalali }}</div>
								<div
									v-if="isForbiddenDate(day.date)"
									class="mt-1 text-[11px] text-red-700 bg-red-50 dark:text-rose-200 dark:bg-rose-900/40 rounded px-1.5 py-0.5 inline-block"
								>
									روز ممنوع
								</div>
							</div>
							<div class="p-2 border-l border-gray-100">
								<label class="inline-flex items-center gap-2 text-xs">
									<input
										type="checkbox"
										:checked="Boolean(getSlot(day.date, 'Morning'))"
										:disabled="!isEditable || isForbiddenDate(day.date)"
										@change="toggleSlot(day.date, 'Morning', $event.target.checked)"
									/>
									<span>می‌توانم صبح باشم</span>
								</label>
								<div v-if="isEditable && getSlot(day.date, 'Morning')" class="mt-1">
									<select
										:value="getSlot(day.date, 'Morning').duty_role"
										:disabled="!isEditable"
										class="w-full rounded border border-gray-300 px-2 py-1 text-xs"
										@change="updateDutyRole(day.date, 'Morning', $event.target.value)"
									>
										<option value="">انتخاب نقش قابل انجام</option>
										<option v-for="role in employeeDutyRoles" :key="role.name" :value="role.name">
											{{ role.role_name }}
										</option>
									</select>
								</div>
							</div>
							<div class="p-2">
								<label class="inline-flex items-center gap-2 text-xs">
									<input
										type="checkbox"
										:checked="Boolean(getSlot(day.date, 'Evening'))"
										:disabled="!isEditable || isForbiddenDate(day.date)"
										@change="toggleSlot(day.date, 'Evening', $event.target.checked)"
									/>
									<span>می‌توانم عصر باشم</span>
								</label>
								<div v-if="isEditable && getSlot(day.date, 'Evening')" class="mt-1">
									<select
										:value="getSlot(day.date, 'Evening').duty_role"
										:disabled="!isEditable"
										class="w-full rounded border border-gray-300 px-2 py-1 text-xs"
										@change="updateDutyRole(day.date, 'Evening', $event.target.value)"
									>
										<option value="">انتخاب نقش قابل انجام</option>
										<option v-for="role in employeeDutyRoles" :key="role.name" :value="role.name">
											{{ role.role_name }}
										</option>
									</select>
								</div>
							</div>
						</div>
					</div>

					<!-- Desktop (Google Calendar style weekly board) -->
					<div class="hidden md:block bg-white rounded-xl border border-gray-100 overflow-hidden">
						<div class="overflow-x-auto">
							<div class="min-w-[1080px]">
								<div
									class="grid bg-gray-50 border-b border-gray-200"
									style="grid-template-columns: 170px repeat(7, minmax(0, 1fr));"
								>
									<div class="p-3 text-xs font-semibold text-gray-600 border-l border-gray-200">ساعت / روز</div>
									<div
										v-for="day in weekDays"
										:key="`desktop-head-${day.date}`"
										class="p-3 border-l border-gray-200"
									>
										<div class="text-xs font-semibold text-gray-900">{{ day.label }}</div>
										<div class="text-[11px] text-gray-500 mt-0.5">{{ day.jalali }}</div>
										<div
											v-if="isForbiddenDate(day.date)"
											class="mt-1 inline-block text-[10px] text-red-700 bg-red-50 dark:text-rose-200 dark:bg-rose-900/40 rounded px-1.5 py-0.5"
										>
											روز ممنوع
										</div>
									</div>
								</div>

								<div
									v-for="slotCode in desktopSlotCodes"
									:key="`desktop-row-${slotCode}`"
									class="grid border-b border-gray-100 last:border-b-0"
									style="grid-template-columns: 170px repeat(7, minmax(0, 1fr));"
								>
									<div class="p-3 border-l border-gray-100 bg-gray-50/50">
										<div class="text-sm font-semibold text-gray-900">{{ slotLabel(slotCode) }}</div>
										<div class="text-xs text-gray-500 mt-1">{{ slotTimeText(slotCode) }}</div>
									</div>

									<div
										v-for="day in weekDays"
										:key="`desktop-cell-${slotCode}-${day.date}`"
										class="p-2 border-l border-gray-100"
									>
										<button
											type="button"
											class="w-full rounded-lg border px-2 py-2 text-right transition"
											:class="desktopCellClass(day.date, slotCode)"
											:disabled="!isEditable || isForbiddenDate(day.date)"
											@click="toggleSlotFromCalendar(day.date, slotCode)"
										>
											<div class="flex items-center justify-between">
												<span class="text-xs font-semibold">{{ slotLabel(slotCode) }}</span>
												<span v-if="getSlot(day.date, slotCode)" class="text-[11px]">✓</span>
											</div>
											<div class="text-[11px] mt-1">
												{{ cellHintText(day.date, slotCode) }}
											</div>
										</button>

										<div v-if="isEditable && getSlot(day.date, slotCode)" class="mt-2">
											<select
												:value="getSlot(day.date, slotCode).duty_role"
												:disabled="!isEditable"
												class="w-full rounded border border-gray-300 px-2 py-1 text-xs bg-white"
												@click.stop
												@change="updateDutyRole(day.date, slotCode, $event.target.value)"
											>
												<option value="">انتخاب نقش قابل انجام</option>
												<option v-for="role in employeeDutyRoles" :key="role.name" :value="role.name">
													{{ role.role_name }}
												</option>
											</select>
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<div v-if="isEditable" class="flex gap-2">
					<Button
						variant="solid"
						class="w-full"
						:disabled="!isEditable"
						:loading="saveResource.loading"
						@click="saveDraft"
					>
						ذخیره پیش‌نویس
					</Button>
					<Button
						variant="solid"
						theme="green"
						class="w-full"
						:disabled="!isEditable"
						:loading="submitResource.loading"
						@click="submitPlan"
					>
						ارسال برای تایید
					</Button>
				</div>

				<Button
					v-if="planDoc && planDoc.docstatus === 1"
					variant="outline"
					class="w-full"
					:loading="amendResource.loading"
					@click="createAmendment"
				>
					ایجاد نسخه اصلاحی
				</Button>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue"
import { createResource, toast } from "frappe-ui"
import { useRoute } from "vue-router"

import BaseLayout from "@/components/BaseLayout.vue"
import SearchableDropdown from "@/components/SearchableDropdown.vue"
import { formatGregorianDate, formatJalaliDate, toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")
const route = useRoute()

const selectedEmployee = ref(
	typeof route.query.employee === "string" ? route.query.employee : ""
)
const currentEmployee = ref("")
const weekStartDate = ref(
	typeof route.query.week_start_date === "string"
		? route.query.week_start_date
		: formatGregorianDate(new Date())
)
const planDoc = ref(null)
const slots = ref([])
const confirmedSlots = ref([])
const manageableEmployees = ref([])
const employeeDutyRoles = ref([])
const rules = ref({ required_days_per_week: 6, minimum_hours_per_week: 48 })
const slotTemplates = ref({ Morning: null, Evening: null })
const isLoading = ref(false)
const defaultDutyRole = ref("")
const forbiddenWeekdays = ref([])
const desktopSlotCodes = ["Morning", "Evening"]

const weekDays = computed(() => {
	const labels = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
	return labels.map((label, index) => {
		const date = addDays(weekStartDate.value, index)
		return {
			label,
			date,
			jalali: formatJalaliDate(date),
		}
	})
})

const weekLabel = computed(() => {
	const from = formatJalaliDate(weekStartDate.value)
	const to = formatJalaliDate(addDays(weekStartDate.value, 6))
	return `${from} - ${to}`
})

const manageableEmployeeOptions = computed(() =>
	(manageableEmployees.value || []).map((employee) => ({
		label: employee.employee_name || employee.name,
		value: employee.name,
	}))
)

const effectiveSlots = computed(() => {
	// Once allocator finalizes weekly shifts, employee should only see finalized slots.
	if (confirmedSlots.value.length > 0) {
		return [...confirmedSlots.value].sort((left, right) => {
			if (left.work_date === right.work_date) {
				return String(left.slot_code).localeCompare(String(right.slot_code))
			}
			return String(left.work_date).localeCompare(String(right.work_date))
		})
	}

	const slotMap = new Map()
	for (const slot of confirmedSlots.value) {
		slotMap.set(`${slot.work_date}::${slot.slot_code}`, slot)
	}
	for (const slot of slots.value) {
		slotMap.set(`${slot.work_date}::${slot.slot_code}`, slot)
	}
	return [...slotMap.values()].sort((left, right) => {
		if (left.work_date === right.work_date) {
			return String(left.slot_code).localeCompare(String(right.slot_code))
		}
		return String(left.work_date).localeCompare(String(right.work_date))
	})
})

const hasFinalizedAssignments = computed(() => confirmedSlots.value.length > 0)
const canRequestShiftChange = computed(() =>
	Boolean(hasFinalizedAssignments.value && selectedEmployee.value && selectedEmployee.value === currentEmployee.value)
)

const finalizedShiftRows = computed(() =>
	effectiveSlots.value.map((slot) => ({
		key: `${slot.work_date}-${slot.slot_code}`,
		workDate: slot.work_date,
		dateLabel: formatJalaliDate(slot.work_date, { withWeekday: true }),
		slotCode: slot.slot_code,
		slotLabel: slotLabel(slot.slot_code),
		shiftType: slot.shift_type || "",
	}))
)

const selectedDaysCount = computed(() => {
	const dates = new Set(effectiveSlots.value.map((slot) => slot.work_date))
	return dates.size
})

const totalHours = computed(() => {
	return effectiveSlots.value.reduce(
		(sum, slot) => sum + calculateHours(slot.start_time, slot.end_time),
		0
	)
})

const isEditable = computed(() => {
	if (planDoc.value) return planDoc.value.docstatus === 0
	if (hasFinalizedAssignments.value) return false
	return true
})

const statusLabel = computed(() => {
	if (!planDoc.value && hasFinalizedAssignments.value) {
		return "نهایی شده توسط تعیین‌کننده شیفت"
	}
	if (!planDoc.value) return "پیش‌نویس"
	return __(planDoc.value.status)
})

const statusClass = computed(() => {
	if (!planDoc.value && hasFinalizedAssignments.value) return "text-emerald-700"
	if (!planDoc.value) return "text-gray-700"
	const status = planDoc.value.status
	if (status === "Approved") return "text-green-700"
	if (status === "Rejected") return "text-red-700"
	if (status === "Submitted") return "text-blue-700"
	if (status === "Replaced") return "text-amber-700"
	return "text-gray-700"
})

function showSuccessToast(text) {
	toast({
		title: "موفق",
		text,
		icon: "check-circle",
		position: "bottom-center",
		iconClasses: "text-green-500",
	})
}

const contextResource = createResource({
	url: "hrms.api.weekly_shift.get_weekly_shift_context",
	auto: false,
	onSuccess(data) {
		weekStartDate.value = data.week_start_date
		manageableEmployees.value = data.manageable_employees || []
		currentEmployee.value = data.current_employee || currentEmployee.value
		if (!selectedEmployee.value) {
			selectedEmployee.value = data.employee
		}
		rules.value = data.rules || rules.value
		slotTemplates.value = normalizeSlotTemplates(data.slot_templates || [])
		defaultDutyRole.value = data.default_duty_role || ""
		forbiddenWeekdays.value = data.forbidden_weekdays || []
		employeeDutyRoles.value = data.employee_duty_roles || []
		if (data.plan) {
			planDoc.value = data.plan
			slots.value = normalizeSlots(data.plan.slot_details || [])
		} else {
			planDoc.value = null
			slots.value = []
		}
	},
})

const saveResource = createResource({
	url: "hrms.api.weekly_shift.upsert_weekly_shift_plan",
	auto: false,
	onSuccess(data) {
		planDoc.value = data
		slots.value = normalizeSlots(data.slot_details || [])
		showSuccessToast("پیش‌نویس ذخیره شد")
	},
})

const submitResource = createResource({
	url: "hrms.api.weekly_shift.submit_weekly_shift_plan",
	auto: false,
	onSuccess(data) {
		planDoc.value = data
		slots.value = normalizeSlots(data.slot_details || [])
		showSuccessToast("برنامه هفتگی ارسال شد")
	},
})

const amendResource = createResource({
	url: "hrms.api.weekly_shift.create_weekly_shift_plan_amendment",
	auto: false,
	onSuccess(data) {
		planDoc.value = data
		slots.value = normalizeSlots(data.slot_details || [])
		showSuccessToast("نسخه اصلاحی ایجاد شد")
	},
})

const assignedShiftsResource = createResource({
	url: "hrms.api.get_shifts",
	auto: false,
})

loadContext()

async function loadContext() {
	isLoading.value = true
	try {
		await contextResource.fetch({
			week_start_date: weekStartDate.value,
			employee: selectedEmployee.value || undefined,
		})
		await loadConfirmedShifts()
	} finally {
		isLoading.value = false
	}
}

function shiftWeek(direction) {
	weekStartDate.value = addDays(weekStartDate.value, direction * 7)
	loadContext()
}

function onEmployeeChange() {
	loadContext()
}

function normalizeSlotTemplates(templates) {
	const map = { Morning: null, Evening: null }
	for (const template of templates) {
		map[template.slot_code] = template
	}
	return map
}

function normalizeSlots(slotDetails) {
	return (slotDetails || [])
		.filter((slot) => slot?.work_date && slot?.slot_code)
		.map((slot) => ({
			work_date: slot.work_date,
			slot_code: slot.slot_code,
			shift_type: slot.shift_type || "",
			start_time: normalizeTime(slot.start_time),
			end_time: normalizeTime(slot.end_time),
			duty_role: slot.duty_role || defaultDutyRole.value || employeeDutyRoles.value[0]?.name || "",
		}))
}

async function loadConfirmedShifts() {
	if (!selectedEmployee.value) {
		confirmedSlots.value = []
		return
	}

	try {
		await assignedShiftsResource.fetch({
			employee: selectedEmployee.value,
		})
		confirmedSlots.value = normalizeConfirmedShiftAssignments(assignedShiftsResource.data || [])
	} catch {
		confirmedSlots.value = []
	}
}

function normalizeConfirmedShiftAssignments(assignments) {
	const weekEndDate = addDays(weekStartDate.value, 6)
	const unique = new Map()

	for (const assignment of assignments || []) {
		const assignmentStart = String(assignment?.start_date || "")
		const assignmentEnd = String(assignment?.end_date || assignmentStart || "")
		if (!(assignmentStart && assignmentEnd)) continue

		let currentDate = assignmentStart > weekStartDate.value ? assignmentStart : weekStartDate.value
		const maxDate = assignmentEnd < weekEndDate ? assignmentEnd : weekEndDate
		if (currentDate > maxDate) continue

		while (currentDate <= maxDate) {
			const slotCode = inferSlotCodeFromShift(assignment)
			const key = `${currentDate}::${slotCode}`
			if (!unique.has(key)) {
				unique.set(key, {
					work_date: currentDate,
					slot_code: slotCode,
					shift_type: assignment.shift_type || "",
					start_time: normalizeTime(assignment.start_time),
					end_time: normalizeTime(assignment.end_time),
					duty_role: "",
				})
			}
			currentDate = addDays(currentDate, 1)
		}
	}

	return [...unique.values()].sort((left, right) => {
		if (left.work_date === right.work_date) {
			return String(left.slot_code).localeCompare(String(right.slot_code))
		}
		return String(left.work_date).localeCompare(String(right.work_date))
	})
}

function inferSlotCodeFromShift(shift) {
	const shiftName = String(shift?.shift_type || "").toLowerCase()
	if (shiftName.includes("morning") || shiftName.includes("صبح")) return "Morning"
	if (shiftName.includes("evening") || shiftName.includes("عصر")) return "Evening"

	const startMinutes = parseTimeToMinutes(shift?.start_time)
	if (startMinutes === null) return "Morning"
	return startMinutes < 15 * 60 ? "Morning" : "Evening"
}

function parseTimeToMinutes(value) {
	const normalized = normalizeTime(value)
	if (!normalized) return null
	const [hourText = "", minuteText = ""] = normalized.split(":")
	const hour = Number(hourText)
	const minute = Number(minuteText)
	if (!Number.isFinite(hour) || !Number.isFinite(minute)) return null
	return hour * 60 + minute
}

function getEditableSlot(workDate, slotCode) {
	return slots.value.find((slot) => slot.work_date === workDate && slot.slot_code === slotCode)
}

function getSlot(workDate, slotCode) {
	return effectiveSlots.value.find((slot) => slot.work_date === workDate && slot.slot_code === slotCode)
}

function toggleSlot(workDate, slotCode, checked) {
	if (!isEditable.value) return
	if (isForbiddenDate(workDate)) return
	const existing = getEditableSlot(workDate, slotCode)
	if (checked && !existing) {
		const template = slotTemplates.value[slotCode] || slotTemplates.value.Morning || slotTemplates.value.Evening || {}
		slots.value.push({
			work_date: workDate,
			slot_code: slotCode,
			shift_type: template.shift_type || "",
			start_time: normalizeTime(template.start_time),
			end_time: normalizeTime(template.end_time),
			duty_role: defaultDutyRole.value || employeeDutyRoles.value[0]?.name || "",
		})
	} else if (!checked && existing) {
		slots.value = slots.value.filter(
			(slot) => !(slot.work_date === workDate && slot.slot_code === slotCode)
		)
	}
}

function updateDutyRole(workDate, slotCode, dutyRole) {
	const slot = getEditableSlot(workDate, slotCode)
	if (!slot) return
	slot.duty_role = dutyRole
}

function slotLabel(slotCode) {
	return slotCode === "Morning" ? "شیفت صبح" : "شیفت عصر"
}

function buildShiftChangeRequestRoute(slot) {
	return {
		name: "ShiftRequestFormView",
		query: {
			from_date: slot.workDate,
			to_date: slot.workDate,
			slot_code: slot.slotCode,
			shift_type: slot.shiftType || "",
		},
	}
}

function slotTimeText(slotCode) {
	const template = slotTemplates.value[slotCode] || {}
	const start = normalizeTime(template.start_time)
	const end = normalizeTime(template.end_time)
	if (!(start && end)) {
		return slotCode === "Morning" ? "زمان پیش‌فرض صبح" : "زمان پیش‌فرض عصر"
	}
	return `${toPersianDigits(start)} تا ${toPersianDigits(end)}`
}

function toggleSlotFromCalendar(workDate, slotCode) {
	const exists = Boolean(getSlot(workDate, slotCode))
	toggleSlot(workDate, slotCode, !exists)
}

function cellHintText(workDate, slotCode) {
	if (isForbiddenDate(workDate)) return "در این روز امکان حضور ندارید"
	if (getSlot(workDate, slotCode)) return isEditable.value ? "برای لغو، دوباره کلیک کنید" : "ثبت شده"
	if (!isEditable.value) return "ثبت نشده"
	return "برای انتخاب کلیک کنید"
}

function desktopCellClass(workDate, slotCode) {
	if (isForbiddenDate(workDate)) {
		return "bg-red-50 border-red-200 text-red-700 dark:bg-rose-900/35 dark:border-rose-500/50 dark:text-rose-200 cursor-not-allowed opacity-70"
	}

	if (getSlot(workDate, slotCode)) {
		return "bg-blue-50 border-blue-300 text-blue-800 dark:bg-sky-900/35 dark:border-sky-500/60 dark:text-sky-200 ring-1 ring-blue-100 dark:ring-sky-400/40"
	}

	return "bg-white border-gray-200 text-gray-600 dark:bg-slate-900/70 dark:border-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800/80 hover:border-slate-300 dark:hover:border-slate-500"
}

function isForbiddenDate(dateString) {
	const date = new Date(`${dateString}T12:00:00`)
	const jsWeekday = date.getDay()
	const weekday = (jsWeekday + 6) % 7
	return forbiddenWeekdays.value.includes(weekday)
}

function normalizeTime(value) {
	if (!value) return ""
	const match = String(value).trim().match(/^(\d{1,2}):(\d{2})/)
	if (!match) return ""
	const hours = Number(match[1])
	const minutes = Number(match[2])
	if (Number.isNaN(hours) || Number.isNaN(minutes)) return ""
	if (hours < 0 || hours > 23 || minutes < 0 || minutes > 59) return ""
	return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`
}

function calculateHours(startTime, endTime) {
	if (!(startTime && endTime)) return 0
	const [sh, sm] = normalizeTime(startTime).split(":").map(Number)
	const [eh, em] = normalizeTime(endTime).split(":").map(Number)
	if ([sh, sm, eh, em].some((v) => Number.isNaN(v))) return 0

	let start = sh * 60 + sm
	let end = eh * 60 + em
	if (end <= start) end += 24 * 60
	return (end - start) / 60
}

async function saveDraft() {
	await saveResource.fetch({
		payload: {
			name: planDoc.value?.name,
			employee: selectedEmployee.value,
			week_start_date: weekStartDate.value,
			slots: slots.value,
		},
	})
}

async function submitPlan() {
	if (!planDoc.value?.name) {
		await saveDraft()
	}
	if (!planDoc.value?.name) return
	await submitResource.fetch({ plan_name: planDoc.value.name })
}

async function createAmendment() {
	if (!planDoc.value?.name) return
	await amendResource.fetch({ source_plan_name: planDoc.value.name })
}

function addDays(dateString, days) {
	const date = new Date(`${dateString}T12:00:00`)
	date.setDate(date.getDate() + days)
	return formatGregorianDate(date)
}

watch(
	() => [route.query.employee, route.query.week_start_date],
	([employee, weekStart]) => {
		const employeeFromQuery = typeof employee === "string" ? employee : ""
		const weekFromQuery =
			typeof weekStart === "string" && weekStart ? weekStart : weekStartDate.value

		if (employeeFromQuery && selectedEmployee.value !== employeeFromQuery) {
			selectedEmployee.value = employeeFromQuery
		}
		if (weekFromQuery && weekStartDate.value !== weekFromQuery) {
			weekStartDate.value = weekFromQuery
		}

		loadContext()
	}
)
</script>
