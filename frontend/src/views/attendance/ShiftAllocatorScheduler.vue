<template>
	<BaseLayout :pageTitle="'تقویم هفتگی تعیین شیفت تیم'">
		<template #body>
				<div class="flex flex-col p-4 gap-4 mb-8">
				<ShiftManagementTabs />
				<!-- بخش هفته و فیلترها (بدون تغییر) -->
				<div class="bg-white rounded-lg p-3 border border-gray-100 flex items-center justify-between">
					<Button variant="subtle" icon="chevron-right" @click="shiftWeek(-1)" />
					<div class="text-sm font-semibold text-gray-900">{{ weekLabel }}</div>
					<Button variant="subtle" icon="chevron-left" @click="shiftWeek(1)" />
				</div>

				<div class="bg-white rounded-lg border border-gray-100 p-3 flex flex-col gap-3">
					<div class="text-sm font-semibold text-gray-900">فیلترها</div>
					<div class="grid grid-cols-1 md:grid-cols-4 gap-2">
						<input
							v-model="employeeFilter"
							type="text"
							placeholder="جستجوی نام کارمند"
							class="rounded border border-gray-300 px-3 py-2 text-sm"
						/>
						<select v-model="designationFilter" class="rounded border border-gray-300 px-3 py-2 text-sm">
							<option value="">همه سمت‌ها</option>
							<option v-for="designation in designationOptions" :key="designation" :value="designation">
								{{ designation }}
							</option>
						</select>
						<select v-model="slotFilter" class="rounded border border-gray-300 px-3 py-2 text-sm">
							<option value="Both">صبح و عصر</option>
							<option value="Morning">فقط صبح</option>
							<option value="Evening">فقط عصر</option>
						</select>
						<label class="rounded border border-gray-300 px-3 py-2 text-sm inline-flex items-center gap-2">
							<input v-model="rotationalOnly" type="checkbox" />
							<span>فقط شیفت چرخشی</span>
						</label>
					</div>
				</div>

				<!-- راهنما و خلاصه وضعیت (بدون تغییر) -->
				<div class="bg-white rounded-lg border border-gray-100 p-3">
					<div class="text-sm font-semibold text-gray-900 mb-2">راهنمای رنگ سمت‌ها</div>
					<div class="flex flex-wrap gap-2">
						<div
							v-for="designation in designationOptions"
							:key="`legend-${designation}`"
							class="rounded px-2 py-1 text-xs font-semibold"
							:class="designationColor(designation).badge"
							:style="designationColor(designation).badgeStyle"
						>
							{{ designation }}
						</div>
					</div>
				</div>

				<div class="bg-white rounded-lg border border-gray-100 p-3">
					<div class="text-sm font-semibold text-gray-900 mb-2">تعداد نیرو در هر روز</div>
					<div class="grid grid-cols-2 md:grid-cols-7 gap-2">
						<div
							v-for="day in weekDays"
							:key="`summary-${day.date}`"
							class="rounded border border-gray-200 px-2 py-1"
						>
							<div class="text-[11px] text-gray-600">{{ day.label }}</div>
							<div class="text-sm font-semibold text-gray-900">
								{{ toPersianDigits(String(getDayCount(day.date))) }} نفر
							</div>
						</div>
					</div>
				</div>

				<!-- بخش اصلی جدول گروه‌بندی شده -->
				<div v-if="contextResource.loading" class="bg-white rounded-lg p-4 text-sm text-gray-600">
					در حال بارگذاری...
				</div>

				<div v-else-if="!groupedEmployees.length" class="bg-white rounded-lg p-4 text-sm text-gray-600">
					کارمندی برای نمایش وجود ندارد.
				</div>

				<div v-else class="bg-white rounded-lg border border-gray-100 overflow-auto">
					<div class="min-w-[980px]">
						<!-- هدر جدول -->
						<div class="grid grid-cols-9 bg-gray-100 border-b border-gray-200 text-xs font-bold text-gray-700">
							<div class="p-3 col-span-2">کارمند / سمت</div>
							<div v-for="day in weekDays" :key="`head-${day.date}`" class="p-3 text-center">
								<div>{{ day.short }}</div>
								<div class="text-[10px] font-normal">{{ day.jalaliDay }}</div>
							</div>
						</div>

						<!-- حلقه‌ی گروه‌ها -->
						<div v-for="group in groupedEmployees" :key="group.designation">
							<!-- تیتر هر گروه -->
							<div class="bg-gray-50 border-b border-gray-200 px-3 py-2 text-xs font-bold text-gray-600 flex items-center gap-2">
								<div
									class="w-2 h-2 rounded-full"
									:class="designationColor(group.designation).dot"
									:style="designationColor(group.designation).dotStyle"
								></div>
								{{ group.designation || "بدون سمت" }} ({{ toPersianDigits(String(group.items.length)) }} نفر)
							</div>

							<!-- کارمندان داخل هر گروه -->
							<div
								v-for="employee in group.items"
								:key="employee.name"
								class="grid grid-cols-9 border-b border-gray-100 last:border-b-0 hover:bg-gray-50/50 transition-colors"
							>
								<div class="p-2 col-span-2 border-l border-gray-100">
									<div class="text-xs font-semibold text-gray-900">{{ employee.employee_name }}</div>
									<div class="mt-1 text-[11px] text-gray-600">
										ساعت نهایی:
										<span
											class="rounded px-1.5 py-0.5 font-semibold"
											:class="hoursBadgeClass(employee.name)"
										>
											{{ toPersianDigits(employeeWeeklyHours(employee.name).toFixed(1)) }}
										</span>
									</div>
								</div>
								<div
									v-for="day in weekDays"
									:key="`${employee.name}-${day.date}`"
									class="p-1 border-l border-gray-100"
								>
									<div
										v-if="isForbidden(employee.name, day.date)"
										class="h-full rounded bg-red-50 border border-red-200 text-red-700 dark:bg-rose-900/35 dark:border-rose-500/50 dark:text-rose-200 text-[10px] flex items-center justify-center py-3"
									>
										ممنوع
									</div>
									<div v-else class="flex flex-col gap-1">
										<button
											v-for="slotCode in displaySlotCodes"
											:key="`${employee.name}-${day.date}-${slotCode}`"
											type="button"
											class="rounded px-1.5 py-1 text-[10px] font-semibold border"
											:class="slotClass(employee, day.date, slotCode)"
											:style="slotStyle(employee, day.date, slotCode)"
											@click="toggleEmployeeSlot(employee, day.date, slotCode)"
										>
											{{ slotCode === "Morning" ? "صبح" : "عصر" }}
										</button>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- جمع ساعات (بدون تغییر) -->
				<div class="bg-white rounded-lg border border-gray-100 p-3">
					<div class="text-sm font-semibold text-gray-900 mb-2">جمع ساعات نهایی</div>
					<div class="grid grid-cols-1 md:grid-cols-2 gap-2">
						<div
							v-for="employee in filteredEmployees"
							:key="`hours-${employee.name}`"
							class="rounded border border-gray-200 px-2 py-1 text-xs flex items-center justify-between"
						>
							<span>{{ employee.employee_name }}</span>
							<span class="font-semibold rounded px-2 py-0.5" :class="hoursBadgeClass(employee.name)">
								{{ toPersianDigits(employeeWeeklyHours(employee.name).toFixed(1)) }} / {{ toPersianDigits(requiredHoursForEmployee(employee.name).toFixed(1)) }} ساعت
							</span>
						</div>
					</div>
				</div>

				<div class="flex gap-2">
					<Button
						variant="solid"
						class="w-full"
						:loading="saving"
						:disabled="!hasChanges || saving"
						@click="saveAndFinalize"
					>
						ثبت نهایی شیفت‌های هفته
					</Button>
					<Button variant="outline" class="w-full" :disabled="saving" @click="loadContext">
						بارگذاری مجدد
					</Button>
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref } from "vue"
import { createResource, toast } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import ShiftManagementTabs from "@/components/ShiftManagementTabs.vue"
import { formatGregorianDate, formatJalaliDate, toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")
const employee = inject("$employee")

const weekStartDate = ref(formatGregorianDate(new Date()))
const employeeFilter = ref("")
const designationFilter = ref("")
const slotFilter = ref("Both")
const rotationalOnly = ref(true)

const employees = ref([])
const finalizationDoc = ref(null)
const slotTemplates = ref({ Morning: null, Evening: null })

const requestedSlotIndex = ref({})
const assignedSlotsByEmployee = ref({})
const initialSlotsByEmployee = ref({})
const forbiddenByEmployee = ref({})

const saving = ref(false)

const isAllocator = computed(() =>
	Boolean(employee.data?.is_shift_allocator || employee.data?.is_shift_allocator_by_role)
)
const allocatorApproverIds = computed(() => {
	const ids = [employee.data?.user_id, employee.data?.name]
	return ids
		.map((value) => String(value || "").trim().toLowerCase())
		.filter(Boolean)
})

const contextResource = createResource({
	url: "hrms.api.weekly_shift.get_weekly_shift_finalization_context",
	auto: false,
	onSuccess(data) {
		if (data?.week_start_date) {
			weekStartDate.value = data.week_start_date
		}

		const scopedEmployees = (data?.team_employees || []).filter(
			(teamEmployee) => isEmployeeManagedByCurrentAllocator(teamEmployee) && isPlanningEmployee(teamEmployee)
		)
		const allowedEmployeeNames = new Set(scopedEmployees.map((item) => item.name))

		employees.value = scopedEmployees
		finalizationDoc.value = data?.finalization || null
		slotTemplates.value = normalizeTemplates(data?.slot_templates || [])
		requestedSlotIndex.value = buildRequestedIndex(employees.value)
		forbiddenByEmployee.value = buildForbiddenMap(employees.value)

		if (finalizationDoc.value?.final_slots?.length) {
			assignedSlotsByEmployee.value = buildAssignedFromFinalization(
				finalizationDoc.value.final_slots,
				allowedEmployeeNames
			)
		} else {
			assignedSlotsByEmployee.value = buildAssignedFromRequested(employees.value)
		}
		initialSlotsByEmployee.value = JSON.parse(JSON.stringify(assignedSlotsByEmployee.value))
	},
})

// کدهای مربوط به API (بدون تغییر)
const upsertFinalizationResource = createResource({ url: "hrms.api.weekly_shift.upsert_weekly_shift_finalization", auto: false })
const finalizeFinalizationResource = createResource({ url: "hrms.api.weekly_shift.finalize_weekly_shift_finalization", auto: false })
const amendFinalizationResource = createResource({ url: "hrms.api.weekly_shift.create_weekly_shift_finalization_amendment", auto: false })

// محاسبات هفته (بدون تغییر)
const weekDays = computed(() => {
	const labels = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
	return labels.map((label, index) => {
		const date = addDays(weekStartDate.value, index)
		return { label, short: label.slice(0, 1), date, jalaliDay: formatJalaliDate(date).split("/").slice(-1)[0] }
	})
})

const weekLabel = computed(() => {
	const from = formatJalaliDate(weekStartDate.value)
	const to = formatJalaliDate(addDays(weekStartDate.value, 6))
	return `${from} - ${to}`
})

const designationOptions = computed(() => {
	const values = new Set()
	for (const employee of employees.value) {
		if (employee.designation) values.add(employee.designation)
	}
	return Array.from(values).sort((a, b) => a.localeCompare(b))
})

const designationColorMap = computed(() => {
	const map = {}
	for (const item of employees.value) {
		if (!(item?.designation && item?.designation_color)) continue
		const color = String(item.designation_color).trim()
		if (!/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(color)) continue
		map[item.designation] = color
	}
	return map
})

const displaySlotCodes = computed(() => {
	if (slotFilter.value === "Morning") return ["Morning"]
	if (slotFilter.value === "Evening") return ["Evening"]
	return ["Morning", "Evening"]
})

// فیلتر اولیه کارمندان (بدون تغییر منطق)
const filteredEmployees = computed(() => {
	return employees.value.filter((employee) => {
		const name = (employee.employee_name || "").toLowerCase()
		const query = employeeFilter.value.trim().toLowerCase()
		const matchesName = !query || name.includes(query)
		const matchesDesignation = designationFilter.value ? employee.designation === designationFilter.value : true
		const matchesRotational = rotationalOnly.value ? isPlanningEmployee(employee) : true
		return matchesName && matchesDesignation && matchesRotational
	})
})

/**
 * اضافه شده: گروه‌بندی کارمندان فیلتر شده بر اساس سمت
 */
const groupedEmployees = computed(() => {
	const groups = {}

	filteredEmployees.value.forEach((employee) => {
		const key = employee.designation || "سایر"
		if (!groups[key]) {
			groups[key] = []
		}
		groups[key].push(employee)
	})

	// تبدیل به آرایه و مرتب‌سازی گروه‌ها و کارمندان
	return Object.keys(groups)
		.sort() // مرتب‌سازی حروف الفبای گروه‌ها
		.map((designation) => ({
			designation,
			items: groups[designation].sort((a, b) => (a.employee_name || "").localeCompare(b.employee_name || "")),
		}))
})

const hasChanges = computed(() => {
	for (const employee of employees.value) {
		const name = employee.name
		const current = (assignedSlotsByEmployee.value[name] || []).join("|")
		const initial = (initialSlotsByEmployee.value[name] || []).join("|")
		if (current !== initial) return true
	}
	return false
})

loadContext()

async function loadContext() {
	await contextResource.fetch({ week_start_date: weekStartDate.value })
}

function shiftWeek(direction) {
	weekStartDate.value = addDays(weekStartDate.value, direction * 7)
	loadContext()
}

// متدهای کمکی (بدون تغییر)
function normalizeTemplates(items) {
	const map = { Morning: null, Evening: null }
	for (const row of items) { if (row?.slot_code) map[row.slot_code] = row }
	return map
}

function slotKey(workDate, slotCode) { return `${workDate}|${slotCode}` }
function splitSlotKey(key) { const [workDate, slotCode] = key.split("|"); return { workDate, slotCode } }

function isEmployeeManagedByCurrentAllocator(teamEmployee) {
	if (!isAllocator.value) return true
	const approver = String(teamEmployee?.shift_request_approver || "").trim().toLowerCase()
	return Boolean(approver && allocatorApproverIds.value.includes(approver))
}

function isPlanningEmployee(teamEmployee) {
	return Boolean(
		teamEmployee?.variable_shift || teamEmployee?.has_rotational_shift || teamEmployee?.needs_shift_registration
	)
}

function buildRequestedIndex(teamEmployees) {
	const index = {}
	for (const employee of teamEmployees) {
		const slots = {}
		for (const slot of employee.plan?.slot_details || []) {
			if (slot?.work_date && slot?.slot_code) slots[slotKey(slot.work_date, slot.slot_code)] = slot
		}
		index[employee.name] = slots
	}
	return index
}

function buildForbiddenMap(teamEmployees) {
	const map = {}
	for (const employee of teamEmployees) { map[employee.name] = employee.forbidden_weekdays || [] }
	return map
}

function buildAssignedFromFinalization(finalSlots, allowedEmployeeNames = null) {
	const map = {}
	for (const slot of finalSlots || []) {
		if (!(slot.employee && slot.work_date && slot.slot_code)) continue
		if (allowedEmployeeNames && !allowedEmployeeNames.has(slot.employee)) continue
		if (!map[slot.employee]) map[slot.employee] = []
		map[slot.employee].push(slotKey(slot.work_date, slot.slot_code))
	}
	for (const name in map) { map[name].sort() }
	return map
}

function buildAssignedFromRequested(teamEmployees) {
	const map = {}
	for (const employee of teamEmployees) {
		const keys = Object.keys(requestedSlotIndex.value[employee.name] || {})
		map[employee.name] = [...keys].sort()
	}
	return map
}

function toWeekday(dateString) {
	const date = new Date(`${dateString}T12:00:00`)
	return (date.getDay() + 6) % 7
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

function isForbidden(employeeName, workDate) { return (forbiddenByEmployee.value[employeeName] || []).includes(toWeekday(workDate)) }
function isRequested(employeeName, workDate, slotCode) { return Boolean((requestedSlotIndex.value[employeeName] || {})[slotKey(workDate, slotCode)]) }
function isAssigned(employeeName, workDate, slotCode) { return (assignedSlotsByEmployee.value[employeeName] || []).includes(slotKey(workDate, slotCode)) }

function toggleEmployeeSlot(employee, workDate, slotCode) {
	if (isForbidden(employee.name, workDate)) return
	const key = slotKey(workDate, slotCode)
	const items = [...(assignedSlotsByEmployee.value[employee.name] || [])]
	const index = items.indexOf(key)
	if (index >= 0) { items.splice(index, 1) } else { items.push(key) }
	items.sort()
	assignedSlotsByEmployee.value = { ...assignedSlotsByEmployee.value, [employee.name]: items }
}

function slotClass(employee, workDate, slotCode) {
	const assigned = isAssigned(employee.name, workDate, slotCode)
	const requested = isRequested(employee.name, workDate, slotCode)
	const palette = designationColor(employee.designation)
	if (assigned && requested) return `${palette.filled} border-transparent`
	if (assigned && !requested) return `${palette.filled} border-dashed border-gray-700 dark:border-slate-300`
	if (!assigned && requested) return "bg-sky-50 text-sky-700 border-sky-300 dark:bg-sky-900/40 dark:text-sky-200 dark:border-sky-500/60"
	return "bg-gray-50 text-gray-500 border-gray-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-600"
}

function slotStyle(employee, workDate, slotCode) {
	const assigned = isAssigned(employee.name, workDate, slotCode)
	const requested = isRequested(employee.name, workDate, slotCode)
	if (!assigned) return null
	const style = designationColor(employee.designation).filledStyle
	if (!style) return null
	if (requested) {
		return {
			backgroundColor: style.backgroundColor,
			color: style.color,
		}
	}
	return style
}

function getDayCount(workDate, designation = "") {
	let count = 0
	for (const employee of filteredEmployees.value) {
		if (designation && employee.designation !== designation) continue
		for (const slotCode of displaySlotCodes.value) {
			if (isAssigned(employee.name, workDate, slotCode)) { count += 1; break }
		}
	}
	return count
}

function hoursForSlot(slotCode) {
	const template = slotTemplates.value[slotCode]
	const start = normalizeTime(template?.start_time)
	const end = normalizeTime(template?.end_time)
	if (!(start && end)) return 8
	const [sh, sm] = start.split(":").map(Number)
	const [eh, em] = end.split(":").map(Number)
	let from = sh * 60 + sm
	let to = eh * 60 + em
	if (to <= from) to += 24 * 60
	return (to - from) / 60
}

function employeeWeeklyHours(employeeName) {
	let total = 0
	for (const key of assignedSlotsByEmployee.value[employeeName] || []) {
		const { slotCode } = splitSlotKey(key)
		total += hoursForSlot(slotCode)
	}
	return total
}

function requiredHoursForEmployee(employeeName) {
	const employee = getEmployeeByName(employeeName)
	const value = Number(employee?.minimum_hours_per_week)
	return (Number.isNaN(value) || value <= 0) ? 48 : value
}

function hoursBadgeClass(employeeName) {
	return employeeWeeklyHours(employeeName) >= requiredHoursForEmployee(employeeName)
		? "bg-green-100 text-green-800 dark:bg-emerald-900/40 dark:text-emerald-200"
		: "bg-yellow-100 text-yellow-800 dark:bg-amber-900/40 dark:text-amber-200"
}

const palette = [
	{
		badge: "bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200",
		filled: "bg-rose-200 text-rose-900 dark:bg-rose-800/55 dark:text-rose-100",
		dot: "bg-rose-500",
	},
	{
		badge: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
		filled: "bg-amber-200 text-amber-900 dark:bg-amber-800/55 dark:text-amber-100",
		dot: "bg-amber-500",
	},
	{
		badge: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200",
		filled: "bg-emerald-200 text-emerald-900 dark:bg-emerald-800/55 dark:text-emerald-100",
		dot: "bg-emerald-500",
	},
	{
		badge: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900/40 dark:text-cyan-200",
		filled: "bg-cyan-200 text-cyan-900 dark:bg-cyan-800/55 dark:text-cyan-100",
		dot: "bg-cyan-500",
	},
	{
		badge: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-200",
		filled: "bg-indigo-200 text-indigo-900 dark:bg-indigo-800/55 dark:text-indigo-100",
		dot: "bg-indigo-500",
	},
	{
		badge: "bg-fuchsia-100 text-fuchsia-800 dark:bg-fuchsia-900/40 dark:text-fuchsia-200",
		filled: "bg-fuchsia-200 text-fuchsia-900 dark:bg-fuchsia-800/55 dark:text-fuchsia-100",
		dot: "bg-fuchsia-500",
	},
]

function hexToRgb(hexColor) {
	const normalized = String(hexColor).replace("#", "")
	if (normalized.length === 3) {
		return {
			r: Number.parseInt(normalized[0] + normalized[0], 16),
			g: Number.parseInt(normalized[1] + normalized[1], 16),
			b: Number.parseInt(normalized[2] + normalized[2], 16),
		}
	}
	if (normalized.length === 6) {
		return {
			r: Number.parseInt(normalized.slice(0, 2), 16),
			g: Number.parseInt(normalized.slice(2, 4), 16),
			b: Number.parseInt(normalized.slice(4, 6), 16),
		}
	}
	return null
}

function rgbaFromHex(hexColor, alpha) {
	const rgb = hexToRgb(hexColor)
	if (!rgb) return ""
	return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`
}

function readableTextFor(hexColor) {
	const rgb = hexToRgb(hexColor)
	if (!rgb) return "#111827"
	const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255
	return luminance > 0.65 ? "#111827" : "#ffffff"
}

function designationColor(designation) {
	const customColor = designationColorMap.value[designation]
	if (customColor) {
		return {
			badge: "",
			filled: "",
			dot: "",
			badgeStyle: {
				backgroundColor: rgbaFromHex(customColor, 0.14),
				color: customColor,
				border: `1px solid ${rgbaFromHex(customColor, 0.35)}`,
			},
			filledStyle: {
				backgroundColor: rgbaFromHex(customColor, 0.22),
				color: readableTextFor(customColor),
				borderColor: customColor,
			},
			dotStyle: { backgroundColor: customColor },
		}
	}
	if (!designation) return {
		badge: "bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200",
		filled: "bg-gray-200 text-gray-800 dark:bg-slate-700 dark:text-slate-100",
		dot: "bg-gray-500",
		badgeStyle: null,
		filledStyle: null,
		dotStyle: null,
	}
	let hash = 0
	for (const char of designation) hash += char.charCodeAt(0)
	const fallback = palette[hash % palette.length]
	return { ...fallback, badgeStyle: null, filledStyle: null, dotStyle: null }
}

function getEmployeeByName(employeeName) { return employees.value.find((item) => item.name === employeeName) }
function defaultRoleForEmployee(employee) { return employee?.default_duty_role || employee?.available_duty_roles?.[0]?.name || "" }

function buildFinalSlotsPayload() {
	const rows = []
	for (const [employeeName, slotKeys] of Object.entries(assignedSlotsByEmployee.value)) {
		const employee = getEmployeeByName(employeeName)
		for (const key of slotKeys || []) {
			const { workDate, slotCode } = splitSlotKey(key)
			const requested = (requestedSlotIndex.value[employeeName] || {})[key]
			const template = slotTemplates.value[slotCode] || slotTemplates.value.Morning || slotTemplates.value.Evening || {}
			rows.push({
				employee: employeeName, work_date: workDate, slot_code: slotCode,
				shift_type: requested?.shift_type || template.shift_type || "",
				start_time: normalizeTime(requested?.start_time || template.start_time),
				end_time: normalizeTime(requested?.end_time || template.end_time),
				duty_role: requested?.duty_role || defaultRoleForEmployee(employee),
				is_manual: requested ? 0 : 1, source_plan: requested ? employee?.plan?.name : "",
				source_slot: requested?.name || "", was_requested: requested ? 1 : 0,
			})
		}
	}
	return rows
}

function showSuccessToast(text) {
	toast({
		title: "موفق",
		text,
		icon: "check-circle",
		position: "bottom-center",
		iconClasses: "text-green-500",
	})
}

function showErrorToast(text) {
	toast({
		title: "خطا",
		text,
		icon: "alert-circle",
		position: "bottom-center",
		iconClasses: "text-red-500",
	})
}

function extractErrorMessage(error, fallbackMessage) {
	if (Array.isArray(error?.messages) && error.messages.length) return error.messages[0]
	if (typeof error?.message === "string" && error.message.trim()) return error.message
	return fallbackMessage
}

async function ensureDraftBeforeEdit() {
	const current = finalizationDoc.value
	if (!(current?.name && Number(current.docstatus) === 1)) return current?.name || ""

	const confirmMessage =
		"این شیفت قبلا ثبت نهایی شده است. مطمئن هستید می‌خواهید آن را ویرایش کنید؟ با تایید شما یک نسخه اصلاحی ساخته می‌شود."
	const isConfirmed = typeof window === "undefined" ? true : window.confirm(confirmMessage)
	if (!isConfirmed) return null

	const amendment = await amendFinalizationResource.fetch({ source_finalization_name: current.name })
	finalizationDoc.value = amendment
	return amendment?.name || ""
}

async function saveAndFinalize() {
	saving.value = true
	try {
		const editableName = await ensureDraftBeforeEdit()
		if (editableName === null) return

		const saved = await upsertFinalizationResource.fetch({
			payload: { name: editableName || undefined, week_start_date: weekStartDate.value, final_slots: buildFinalSlotsPayload() },
		})
		await finalizeFinalizationResource.fetch({ finalization_name: saved.name })
		showSuccessToast("شیفت‌های نهایی هفته ثبت شد")
		await loadContext()
	} catch (error) {
		showErrorToast(extractErrorMessage(error, "ثبت نهایی شیفت‌ها با خطا مواجه شد"))
	} finally {
		saving.value = false
	}
}

function addDays(dateString, days) {
	const date = new Date(`${dateString}T12:00:00`)
	date.setDate(date.getDate() + days)
	return formatGregorianDate(date)
}
</script>
