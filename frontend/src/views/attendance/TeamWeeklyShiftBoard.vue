<template>
        <BaseLayout :pageTitle="'تقویم هفتگی تیم'">
                <template #body>
                        <div class="flex flex-col p-4 gap-4 mb-8 relative">
                                <ShiftManagementTabs />
                                
                                <!-- بخش بالا (نمایشگر هفته) - چاپ نمی‌شود -->
                                <div class="no-print bg-white rounded-lg p-3 border border-gray-100 flex items-center justify-between">
                                        <Button variant="subtle" icon="chevron-right" @click="shiftWeek(-1)" />
                                        <div class="text-sm font-semibold text-gray-900">{{ weekLabel }}</div>
                                        <Button variant="subtle" icon="chevron-left" @click="shiftWeek(1)" />
                                </div>

                                <div v-if="!isAllocator" class="no-print bg-white rounded-lg border border-gray-100 p-4 text-sm text-gray-700">
                                        این ابزار مخصوص تعیین‌کننده شیفت است. برای مدیریت و نهایی‌سازی برنامه هفتگی، کاربر باید
                                        فیلد <strong>تخصیص‌دهنده شیفت</strong> داشته باشد.
                                </div>

                                <template v-else>
                                        <!-- فیلترها - چاپ نمی‌شود -->
                                        <div class="no-print bg-white rounded-lg border border-gray-100 p-3">
                                                <div class="text-sm font-semibold text-gray-900 mb-2">فیلترها</div>
                                                <div class="grid grid-cols-1 md:grid-cols-4 gap-2">
                                                        <input
                                                                v-model="employeeFilter"
                                                                type="text"
                                                                placeholder="جستجوی کارمند"
                                                                class="rounded border border-gray-300 px-3 py-2 text-sm"
                                                        />
                                                        <select v-model="roleFilter" class="rounded border border-gray-300 px-3 py-2 text-sm">
                                                                <option value="">همه نقش‌ها</option>
                                                                <option v-for="role in roleOptions" :key="role" :value="role">
                                                                        {{ roleLabel(role) }}
                                                                </option>
                                                        </select>
                                                        <select v-model="slotFilter" class="rounded border border-gray-300 px-3 py-2 text-sm">
                                                                <option value="Both">صبح و عصر</option>
                                                                <option value="Morning">فقط صبح</option>
                                                                <option value="Evening">فقط عصر</option>
                                                        </select>
                                                        <label class="rounded border border-gray-300 px-3 py-2 text-sm inline-flex items-center gap-2">
                                                                <input v-model="planningOnly" type="checkbox" />
                                                                <span>فقط شیفت متغیر / برنامه‌ریزی‌شونده</span>
                                                        </label>
                                                </div>
                                        </div>

                                        <!-- خلاصه ساعات - چاپ نمی‌شود -->
                                        <div class="no-print bg-white rounded-lg border border-gray-100 p-3">
                                                <div class="text-sm font-semibold text-gray-900 mb-2">ساعت هر کارمند در این هفته</div>
                                                <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
                                                        <div
                                                                v-for="member in filteredEmployees"
                                                                :key="`sum-${member.name}`"
                                                                class="rounded border border-gray-200 px-2 py-1 text-xs flex items-center justify-between"
                                                        >
                                                                <span>{{ member.employee_name }}</span>
                                                                <span class="font-semibold rounded px-2 py-0.5" :class="hoursBadgeClass(member.name)">
                                                                        {{ toPersianDigits(employeeHours(member.name).toFixed(1)) }} /
                                                                        {{ toPersianDigits(requiredHours(member.name).toFixed(1)) }} ساعت
                                                                </span>
                                                        </div>
                                                </div>
                                        </div>

                                        <div v-if="contextResource.loading" class="no-print bg-white rounded-lg border border-gray-100 p-4 text-sm text-gray-600">
                                                در حال بارگذاری...
                                        </div>

                                        <!-- این بخش (جدول) چاپ می‌شود -->
                                        <div v-else class="print-area bg-white rounded-xl border border-gray-100 overflow-hidden">
                                                
                                                <!-- عنوانی که فقط در حالت چاپ نمایش داده می‌شود -->
                                                <div class="print-only-title">
                                                        برنامه هفتگی شیفت تیم ({{ weekLabel }})
                                                </div>

                                                <div class="overflow-x-auto print-overflow-visible">
                                                        <div class="min-w-[1400px] print-min-w-full">
                                                                
                                                                <!-- هدر جدول -->
                                                                <div class="schedule-grid bg-gray-50 border-b border-gray-200">
                                                                        <!-- ستون کارمندان (در چاپ مخفی می‌شود) -->
                                                                        <div class="p-3 text-xs font-semibold text-gray-700 border-l border-gray-200 hide-on-print">
                                                                                کارمندان قابل تخصیص
                                                                        </div>
                                                                        <!-- روزهای هفته -->
                                                                        <div
                                                                                v-for="day in weekDays"
                                                                                :key="`head-${day.date}`"
                                                                                class="p-3 border-l border-gray-200"
                                                                        >
                                                                                <div class="text-xs font-semibold text-gray-900">{{ day.label }}</div>
                                                                                <div class="text-[11px] text-gray-500">{{ day.jalali }}</div>
                                                                        </div>
                                                                </div>

                                                                <!-- بدنه جدول -->
                                                                <div class="schedule-grid">
                                                                        <!-- ستون درگ و دراپ (در چاپ مخفی می‌شود) -->
                                                                        <div class="p-3 border-l border-gray-100 bg-gray-50/60 hide-on-print">
                                                                                <div class="text-xs text-gray-600 mb-2">کارمندان قابل تخصیص (کشیدن و رها کردن)</div>
                                                                                <div class="flex flex-col gap-2 max-h-[700px] overflow-y-auto pr-1">
                                                                                        <div
                                                                                                v-for="member in filteredEmployees"
                                                                                                :key="`pool-${member.name}`"
                                                                                                draggable="true"
                                                                                                class="rounded border border-gray-200 bg-white px-2 py-1.5 text-xs cursor-grab"
                                                                                                @dragstart="startDragEmployee(member)"
                                                                                        >
                                                                                                <div class="font-semibold text-gray-900">{{ member.employee_name }}</div>
                                                                                                <div class="text-[11px] text-gray-500">{{ member.designation || 'بدون سمت' }}</div>
                                                                                        </div>
                                                                                </div>
                                                                        </div>

                                                                        <!-- ستون شیفت‌های هر روز -->
                                                                        <div
                                                                                v-for="day in weekDays"
                                                                                :key="`day-${day.date}`"
                                                                                class="p-2 border-l border-gray-100"
                                                                        >
                                                                                <div class="flex flex-col gap-2">
                                                                                        <div v-for="slotCode in displaySlotCodes" :key="`${day.date}-${slotCode}`" class="rounded border border-gray-200">
                                                                                                <div class="px-2 py-1 border-b border-gray-200 bg-gray-50 text-[11px] text-gray-700 font-semibold text-center">
                                                                                                        {{ slotLabel(slotCode) }} - {{ slotTimeText(slotCode) }}
                                                                                                </div>
                                                                                                <div class="p-1.5 flex flex-col gap-1.5">
                                                                                                        <div
                                                                                                                v-for="role in visibleRoles"
                                                                                                                :key="`${day.date}-${slotCode}-${role}`"
                                                                                                                class="rounded border min-h-[56px] print-no-page-break"
                                                                                                                :class="roleColor(role).box"
                                                                                                                @dragover.prevent
                                                                                                                @drop="dropOnLane(day.date, slotCode, role)"
                                                                                                        >
                                                                                                                <div class="px-1.5 py-1 text-[10px] font-semibold border-b text-center" :class="roleColor(role).header">
                                                                                                                        {{ roleLabel(role) }}
                                                                                                                </div>
                                                                                                                <div class="p-1 flex flex-col gap-1">
                                                                                                                        <div
                                                                                                                                v-for="item in laneAssignments(day.date, slotCode, role)"
                                                                                                                                :key="item.id"
                                                                                                                                draggable="true"
                                                                                                                                class="rounded border border-white/70 bg-white/90 px-1.5 py-1 text-[10px] text-gray-900 cursor-grab flex items-center justify-between gap-1"
                                                                                                                                @dragstart="startDragAssignment(item)"
                                                                                                                        >
                                                                                                                                <span class="truncate">{{ employeeName(item.employee) }}</span>
                                                                                                                                <button type="button" class="no-print text-gray-400 hover:text-red-600" @click.stop="removeAssignment(item.id)">×</button>
                                                                                                                        </div>
                                                                                                                </div>
                                                                                                        </div>
                                                                                                </div>
                                                                                        </div>
                                                                                </div>
                                                                        </div>
                                                                </div>
                                                        </div>
                                                </div>
                                        </div>

                                        <!-- دکمه‌ها - چاپ نمی‌شود -->
                                        <div class="no-print flex gap-2">
                                                <Button variant="outline" class="w-full" :loading="upsertResource.loading" @click="saveDraft">
                                                        ذخیره پیش‌نویس برنامه تیم
                                                </Button>
                                                <Button variant="solid" theme="green" class="w-full" :loading="saving" @click="finalizeWeek">
                                                        ثبت نهایی برنامه هفته
                                                </Button>
                                        </div>
                                </template>
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

// --- تمامی کدهای جاوااسکریپت و لاجیک شما بدون هیچ تغییری حفظ شده است ---
const employee = inject("$employee")

const isAllocator = computed(() =>
        Boolean(employee.data?.is_shift_allocator || employee.data?.is_shift_allocator_by_role)
)

const weekStartDate = ref(formatGregorianDate(new Date()))
const employeeFilter = ref("")
const roleFilter = ref("")
const slotFilter = ref("Both")
const planningOnly = ref(true)

const teamEmployees = ref([])
const finalizationDoc = ref(null)
const slotTemplates = ref({ Morning: null, Evening: null })
const requestIndex = ref({})
const assignments = ref([])
const dragging = ref(null)
const saving = ref(false)

let assignmentCounter = 1

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

const contextResource = createResource({
        url: "hrms.api.weekly_shift.get_weekly_shift_finalization_context",
        auto: false,
        onSuccess(data) {
                if (data?.week_start_date) {
                        weekStartDate.value = data.week_start_date
                }

                const planningEmployees = (data?.team_employees || []).filter(isPlanningEmployee)
                teamEmployees.value = planningEmployees
                slotTemplates.value = normalizeTemplates(data?.slot_templates || [])
                requestIndex.value = buildRequestIndex(planningEmployees)
                finalizationDoc.value = data?.finalization || null

                if (finalizationDoc.value?.final_slots?.length) {
                        assignments.value = normalizeFinalSlots(finalizationDoc.value.final_slots)
                } else {
                        assignments.value = buildAssignmentsFromRequests(planningEmployees)
                }
        },
})

const upsertResource = createResource({
        url: "hrms.api.weekly_shift.upsert_weekly_shift_finalization",
        auto: false,
        onSuccess(data) {
                finalizationDoc.value = data
                assignments.value = normalizeFinalSlots(data?.final_slots || [])
                showSuccessToast("پیش‌نویس برنامه تیم ذخیره شد")
        },
})

const finalizeResource = createResource({
        url: "hrms.api.weekly_shift.finalize_weekly_shift_finalization",
        auto: false,
})

const amendResource = createResource({
        url: "hrms.api.weekly_shift.create_weekly_shift_finalization_amendment",
        auto: false,
})

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

const displaySlotCodes = computed(() => {
        if (slotFilter.value === "Morning") return ["Morning"]
        if (slotFilter.value === "Evening") return ["Evening"]
        return ["Morning", "Evening"]
})

const filteredEmployees = computed(() => {
        const query = employeeFilter.value.trim().toLowerCase()
        return teamEmployees.value.filter((row) => {
                const matchesQuery =
                        !query ||
                        String(row.employee_name || "").toLowerCase().includes(query) ||
                        String(row.designation || "").toLowerCase().includes(query)
                if (!matchesQuery) return false
                if (!planningOnly.value) return true
                return isPlanningEmployee(row)
        })
})

const roleOptions = computed(() => {
        const roleMap = new Map()
        const registerRole = (value) => {
                const roleName = normalizeRoleName(value)
                if (!roleName) return
                const key = roleGroupingKey(roleName)
                if (!key || roleMap.has(key)) return
                roleMap.set(key, roleName)
        }

        for (const row of filteredEmployees.value) {
                for (const role of row.available_duty_roles || []) {
                        registerRole(role?.duty_role || role?.name)
                }
                registerRole(row.default_duty_role)
        }
        for (const item of assignments.value) {
                registerRole(item.duty_role)
        }
        return Array.from(roleMap.values())
})

const visibleRoles = computed(() => {
        if (!roleFilter.value) return roleOptions.value
        return roleOptions.value.filter((role) => role === roleFilter.value)
})

loadContext()

async function loadContext() {
        if (!isAllocator.value) return
        await contextResource.fetch({ week_start_date: weekStartDate.value })
}

function shiftWeek(direction) {
        weekStartDate.value = addDays(weekStartDate.value, direction * 7)
        loadContext()
}

function normalizeTemplates(rows) {
        const map = { Morning: null, Evening: null }
        for (const row of rows) {
                if (!row?.slot_code) continue
                map[row.slot_code] = row
        }
        return map
}

function buildRequestIndex(rows) {
        const index = {}
        for (const member of rows) {
                const map = {}
                for (const slot of member.plan?.slot_details || []) {
                        if (!(slot?.work_date && slot?.slot_code)) continue
                        map[`${slot.work_date}|${slot.slot_code}`] = slot
                }
                index[member.name] = map
        }
        return index
}

function isPlanningEmployee(row) {
        return Boolean(row.variable_shift || row.has_rotational_shift || row.needs_shift_registration)
}

function buildAssignmentsFromRequests(rows) {
        const result = []
        const seen = new Set()
        for (const member of rows) {
                if (planningOnly.value && !isPlanningEmployee(member)) continue
                for (const slot of member.plan?.slot_details || []) {
                        if (!(slot?.work_date && slot?.slot_code)) continue
                        const key = `${member.name}|${slot.work_date}|${slot.slot_code}`
                        if (seen.has(key)) continue
                        seen.add(key)
                        result.push({
                                id: nextAssignmentId(),
                                employee: member.name,
                                work_date: slot.work_date,
                                slot_code: slot.slot_code,
                                shift_type: slot.shift_type || slotTemplates.value[slot.slot_code]?.shift_type || "",
                                start_time: normalizeTime(slot.start_time) || normalizeTime(slotTemplates.value[slot.slot_code]?.start_time),
                                end_time: normalizeTime(slot.end_time) || normalizeTime(slotTemplates.value[slot.slot_code]?.end_time),
                                duty_role: slot.duty_role || member.default_duty_role || "",
                                is_manual: 0,
                                source_plan: member.plan?.name || "",
                                source_slot: slot.name || "",
                                was_requested: 1,
                        })
                }
        }
        return result
}

function normalizeFinalSlots(rows) {
        return (rows || []).map((slot) => ({
                id: nextAssignmentId(),
                employee: slot.employee,
                work_date: slot.work_date,
                slot_code: slot.slot_code,
                shift_type: slot.shift_type || "",
                start_time: normalizeTime(slot.start_time),
                end_time: normalizeTime(slot.end_time),
                duty_role: slot.duty_role || "",
                is_manual: slot.is_manual ? 1 : 0,
                source_plan: slot.source_plan || "",
                source_slot: slot.source_slot || "",
                was_requested: slot.was_requested ? 1 : 0,
        }))
}

function nextAssignmentId() {
        assignmentCounter += 1
        return assignmentCounter
}

function startDragEmployee(member) {
        dragging.value = { type: "employee", employee: member.name }
}

function startDragAssignment(item) {
        dragging.value = { type: "assignment", id: item.id }
}

function dropOnLane(workDate, slotCode, dutyRole) {
        if (!dragging.value) return

        if (dragging.value.type === "assignment") {
                const item = assignments.value.find((row) => row.id === dragging.value.id)
                if (!item) return
                removeEmployeeSlot(item.employee, workDate, slotCode, item.id)
                item.work_date = workDate
                item.slot_code = slotCode
                item.duty_role = dutyRole || item.duty_role
                if (!item.shift_type) {
                        item.shift_type = slotTemplates.value[slotCode]?.shift_type || ""
                }
                if (!item.start_time) {
                        item.start_time = normalizeTime(slotTemplates.value[slotCode]?.start_time)
                }
                if (!item.end_time) {
                        item.end_time = normalizeTime(slotTemplates.value[slotCode]?.end_time)
                }
        }

        if (dragging.value.type === "employee") {
                const employeeName = dragging.value.employee
                removeEmployeeSlot(employeeName, workDate, slotCode)
                const item = buildAssignment(employeeName, workDate, slotCode, dutyRole)
                if (item) assignments.value.push(item)
        }

        dragging.value = null
}

function removeEmployeeSlot(employeeName, workDate, slotCode, exceptId = null) {
        assignments.value = assignments.value.filter((row) => {
                if (row.employee !== employeeName) return true
                if (row.work_date !== workDate || row.slot_code !== slotCode) return true
                if (exceptId && row.id === exceptId) return true
                return false
        })
}

function buildAssignment(employeeName, workDate, slotCode, dutyRole) {
        const member = teamEmployees.value.find((row) => row.name === employeeName)
        if (!member) return null

        const requested = requestIndex.value[employeeName]?.[`${workDate}|${slotCode}`]
        const template = slotTemplates.value[slotCode] || {}
        return {
                id: nextAssignmentId(),
                employee: employeeName,
                work_date: workDate,
                slot_code: slotCode,
                shift_type: requested?.shift_type || template.shift_type || "",
                start_time: normalizeTime(requested?.start_time || template.start_time),
                end_time: normalizeTime(requested?.end_time || template.end_time),
                duty_role: dutyRole || requested?.duty_role || member.default_duty_role || "",
                is_manual: requested ? 0 : 1,
                source_plan: requested ? member.plan?.name || "" : "",
                source_slot: requested?.name || "",
                was_requested: requested ? 1 : 0,
        }
}

function laneAssignments(workDate, slotCode, dutyRole) {
        const allowedEmployees = new Set(filteredEmployees.value.map((row) => row.name))
        const laneRoleKey = roleGroupingKey(dutyRole)
        return assignments.value
                .filter(
                        (row) =>
                                row.work_date === workDate &&
                                row.slot_code === slotCode &&
                                roleGroupingKey(row.duty_role) === laneRoleKey
                )
                .filter((row) => allowedEmployees.has(row.employee))
                .sort((a, b) => employeeName(a.employee).localeCompare(employeeName(b.employee)))
}

function removeAssignment(id) {
        assignments.value = assignments.value.filter((row) => row.id !== id)
}

function employeeName(employeeNameValue) {
        return teamEmployees.value.find((row) => row.name === employeeNameValue)?.employee_name || employeeNameValue
}

function roleLabel(roleName) {
        return teamEmployees.value
                .flatMap((row) => row.available_duty_roles || [])
                .find((row) => row.duty_role === roleName || row.name === roleName)?.role_name || roleName
}

function normalizeRoleName(value) {
        return String(value || "").trim()
}

function roleGroupingKey(value) {
        const roleName = normalizeRoleName(value)
        if (!roleName) return ""
        return normalizeRoleName(roleLabel(roleName)).toLowerCase()
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

function slotLabel(slotCode) {
        return slotCode === "Morning" ? "شیفت صبح" : "شیفت عصر"
}

function slotTimeText(slotCode) {
        const template = slotTemplates.value[slotCode] || {}
        const start = normalizeTime(template.start_time)
        const end = normalizeTime(template.end_time)
        if (!(start && end)) return "ساعت تعریف نشده"
        return `${toPersianDigits(start)} تا ${toPersianDigits(end)}`
}

function calculateHours(startTime, endTime) {
        if (!(startTime && endTime)) return 0
        const [sh, sm] = normalizeTime(startTime).split(":").map(Number)
        const [eh, em] = normalizeTime(endTime).split(":").map(Number)
        if ([sh, sm, eh, em].some((value) => Number.isNaN(value))) return 0

        let start = sh * 60 + sm
        let end = eh * 60 + em
        if (end <= start) end += 24 * 60
        return (end - start) / 60
}

function employeeHours(employeeNameValue) {
        return assignments.value
                .filter((row) => row.employee === employeeNameValue)
                .reduce((sum, row) => sum + calculateHours(row.start_time, row.end_time), 0)
}

function requiredHours(employeeNameValue) {
        const member = teamEmployees.value.find((row) => row.name === employeeNameValue)
        const value = Number(member?.minimum_hours_per_week)
        if (Number.isNaN(value) || value <= 0) return 48
        return value
}

function hoursBadgeClass(employeeNameValue) {
        return employeeHours(employeeNameValue) >= requiredHours(employeeNameValue)
                ? "bg-green-100 text-green-800"
                : "bg-yellow-100 text-yellow-800"
}

const rolePalette = [
        { box: "bg-rose-50 border-rose-200", header: "bg-rose-100 text-rose-900 border-rose-200" },
        { box: "bg-amber-50 border-amber-200", header: "bg-amber-100 text-amber-900 border-amber-200" },
        { box: "bg-cyan-50 border-cyan-200", header: "bg-cyan-100 text-cyan-900 border-cyan-200" },
        { box: "bg-emerald-50 border-emerald-200", header: "bg-emerald-100 text-emerald-900 border-emerald-200" },
        { box: "bg-indigo-50 border-indigo-200", header: "bg-indigo-100 text-indigo-900 border-indigo-200" },
        { box: "bg-fuchsia-50 border-fuchsia-200", header: "bg-fuchsia-100 text-fuchsia-900 border-fuchsia-200" },
]

function roleColor(roleName) {
        if (!roleName) return { box: "bg-gray-50 border-gray-200", header: "bg-gray-100 text-gray-800 border-gray-200" }
        let hash = 0
        for (const char of roleName) hash += char.charCodeAt(0)
        return rolePalette[hash % rolePalette.length]
}

async function saveDraft() {
        const editableName = await ensureDraftBeforeEdit()
        if (editableName === null) return null

        await upsertResource.fetch({
                payload: {
                        name: editableName || undefined,
                        week_start_date: weekStartDate.value,
                        final_slots: assignments.value.map((row) => ({
                                employee: row.employee,
                                work_date: row.work_date,
                                slot_code: row.slot_code,
                                shift_type: row.shift_type,
                                start_time: row.start_time,
                                end_time: row.end_time,
                                duty_role: row.duty_role,
                                is_manual: row.is_manual,
                                source_plan: row.source_plan,
                                source_slot: row.source_slot,
                                was_requested: row.was_requested,
                        })),
                },
        })
        return true
}

async function ensureDraftBeforeEdit() {
        const current = finalizationDoc.value
        if (!(current?.name && Number(current.docstatus) === 1)) return current?.name || ""

        const confirmMessage =
                "این برنامه قبلا ثبت نهایی شده است. مطمئن هستید می‌خواهید آن را ویرایش کنید؟ با تایید شما یک نسخه اصلاحی ساخته می‌شود."
        const isConfirmed = typeof window === "undefined" ? true : window.confirm(confirmMessage)
        if (!isConfirmed) return null

        const amendment = await amendResource.fetch({ source_finalization_name: current.name })
        finalizationDoc.value = amendment
        assignments.value = normalizeFinalSlots(amendment?.final_slots || [])
        return amendment?.name || ""
}

async function finalizeWeek() {
        saving.value = true
        try {
                const saved = await saveDraft()
                if (saved === null) return
                if (!finalizationDoc.value?.name) return
                await finalizeResource.fetch({ finalization_name: finalizationDoc.value.name })
                showSuccessToast("برنامه هفتگی تیم نهایی شد")
                await loadContext()
        } catch (error) {
                showErrorToast(extractErrorMessage(error, "ثبت نهایی برنامه با خطا مواجه شد"))
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

<style scoped>
/* استایل‌های مربوط به ساختار گرید (جایگزین Inline Style) */
.schedule-grid {
        display: grid;
        /* 8 ستون در حالت عادی (1 ستون درگ کارمند + 7 روز هفته) */
        grid-template-columns: 280px repeat(7, minmax(0, 1fr));
}

/* تیتر مخصوص پرینت که در صفحه وب مخفی است */
.print-only-title {
        display: none;
}

/* تنظیمات مخصوص زمان پرینت (Ctrl+P) */
@media print {
        /* تنظیم کاغذ به صورت A4 و افقی (Landscape) */
        @page {
                size: A4 landscape;
                margin: 10mm;
        }

        /* ترفند مخفی کردن همه چیز در صفحه وب */
        body * {
                visibility: hidden;
        }

        /* فقط باکسی که جدول داخل آن است و فرزندانش دیده شوند */
        .print-area, .print-area * {
                visibility: visible;
        }

        /* باکس جدول را می‌کشد می‌آورد گوشه بالا سمت چپ کل صفحه تا حاشیه اضافه نداشته باشد */
        .print-area {
                position: absolute !important;
                left: 0 !important;
                top: 0 !important;
                width: 100% !important;
                border: none !important;
                box-shadow: none !important;
                border-radius: 0 !important;
        }

        /* المان‌هایی که با این کلاس مارک شده‌اند کاملاً حذف می‌شوند */
        .no-print {
                display: none !important;
        }

        /* مخفی کردن ستون اول (کارمندان قابل تخصیص) در زمان پرینت */
        .hide-on-print {
                display: none !important;
        }

        /* تغییر ساختار گرید: در حالت چاپ فقط 7 روز هفته را نشان می‌دهد (ستون اول حذف می‌شود) */
        .schedule-grid {
                grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
        }

        /* اجبار به چاپ رنگ پس‌زمینه‌ها (مثل رنگ شیفت‌ها) تا در کاغذ سفید نیفتند */
        * {
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
        }

        /* نمایش تیتر اصلی در کاغذ پرینت */
        .print-only-title {
                display: block !important;
                text-align: center;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 0 20px 0;
                color: #000;
        }

        /* جلوگیری از اسکرول خوردن افقی در کاغذ */
        .print-overflow-visible {
                overflow: visible !important;
        }
        
        .print-min-w-full {
                min-width: 100% !important;
        }

        /* جلوگیری از شکسته شدن باکس شیفت‌ها بین دو صفحه (اگر جدول به صفحه دوم رفت) */
        .print-no-page-break {
                break-inside: avoid;
                page-break-inside: avoid;
        }
}
</style>
