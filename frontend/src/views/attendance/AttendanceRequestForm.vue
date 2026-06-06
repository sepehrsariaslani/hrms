<template>
        <BaseLayout :pageTitle="props.id ? __('Attendance Request') : __('New Attendance Request')">
                <template #body>
                        <div class="flex flex-col mt-7 mb-7 p-4 gap-6">
                                <div v-if="!props.id">
                                        <AttendanceCalendar
                                                :selectedDate="attendanceRequest.from_date"
                                                @dateSelected="setSelectedAttendanceDate"
                                                title="انتخاب روز حضور"
                                        />
                                </div>

                                <FormView
                                        v-if="formFields.data"
                                        doctype="Attendance Request"
                                        v-model="attendanceRequest"
                                        :isSubmittable="false"
                                        :returnOnCreate="true"
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
import { ref, watch, inject, computed } from "vue"
import { useRoute } from "vue-router"
import { formatGregorianDate } from "@/utils/jalali"

import BaseLayout from "@/components/BaseLayout.vue"
import FormView from "@/components/FormView.vue"
import AttendanceCalendar from "@/components/AttendanceCalendar.vue"

const employee = inject("$employee")
const __ = inject("$translate")
const route = useRoute()

const props = defineProps({
        id: {
                type: String,
                required: false,
        },
})

const REQUEST_FIELDS = [
        {
                fieldname: "requested_log_type",
                fieldtype: "Select",
                label: "نوع درخواست",
                options: "IN\nOUT",
                reqd: 1,
                default: "IN",
        },
        {
                fieldname: "requested_time",
                fieldtype: "Time",
                label: "ساعت",
                reqd: 1,
        },
        {
                fieldname: "explanation",
                fieldtype: "Small Text",
                label: "توضیحات",
                reqd: 0,
        },
]

function getInitialSelectedDate() {
        const queryDate = String(route.query?.date || "")
        if (/^\d{4}-\d{2}-\d{2}$/.test(queryDate)) return queryDate
        return formatGregorianDate(new Date())
}

function getCurrentTimeValue() {
        const now = new Date()
        const hour = String(now.getHours()).padStart(2, "0")
        const minute = String(now.getMinutes()).padStart(2, "0")
        return `${hour}:${minute}`
}

// reactive object to store form data
const attendanceRequest = ref({
        from_date: getInitialSelectedDate(),
        to_date: getInitialSelectedDate(),
        requested_log_type: "IN",
        requested_time: getCurrentTimeValue(),
})

// get form fields
const formFields = createResource({
        url: "hrms.api.get_doctype_fields",
        params: { doctype: "Attendance Request" },
        auto: true,
        transform(data) {
                if (props.id) return data
                return REQUEST_FIELDS
        },
})

// form scripts
watch(
        () => [attendanceRequest.value.employee, attendanceRequest.value.shift_request_approver],
        ([employeeId, approverId]) => {
                if (!props.id) return
                const isOwner = employeeId === employee.data.name
                const isApprover = approverId === employee.data.user_id
                if (!isOwner && !isApprover) {
                        setFormReadOnly()
                }
        },
        { immediate: true }
)

const selectedDate = computed(
        () => attendanceRequest.value.from_date || getInitialSelectedDate()
)

watch(
        () => attendanceRequest.value.request_mode,
        (requestMode) => {
                if (props.id || requestMode !== "Checkin Request") return
                attendanceRequest.value.to_date = selectedDate.value
                attendanceRequest.value.half_day = 0
                attendanceRequest.value.include_holidays = 0
        }
)

watch(
        () => route.query?.date,
        (value) => {
                const queryDate = String(value || "")
                if (!/^\d{4}-\d{2}-\d{2}$/.test(queryDate)) return
                if (props.id) return
                setSelectedAttendanceDate(queryDate)
        },
        { immediate: true }
)

// helper functions
function setSelectedAttendanceDate(date) {
        attendanceRequest.value.from_date = date
        attendanceRequest.value.to_date = date

        if (attendanceRequest.value.half_day) {
                attendanceRequest.value.half_day_date = date
        }
}

function setFormReadOnly() {
        formFields.data.map((field) => (field.read_only = true))
}

function validateForm() {
        const selectedLogType = attendanceRequest.value.requested_log_type || "IN"
        const selectedType = selectedLogType === "OUT" ? "خروج" : "ورود"
        const selectedTime = attendanceRequest.value.requested_time || getCurrentTimeValue()

        attendanceRequest.value.requested_log_type = selectedLogType
        attendanceRequest.value.requested_time = selectedTime

        attendanceRequest.value.employee = employee.data.name
        attendanceRequest.value.from_date = selectedDate.value
        attendanceRequest.value.to_date = selectedDate.value
        attendanceRequest.value.request_mode = "Checkin Request"
        attendanceRequest.value.reason = "On Duty"
        attendanceRequest.value.explanation =
                attendanceRequest.value.explanation || `درخواست ثبت ${selectedType} در ساعت ${selectedTime}`
        attendanceRequest.value.half_day = 0
        attendanceRequest.value.include_holidays = 0

        // explicitly clear reviewer-only fields so backend validation passes for regular employees
        attendanceRequest.value.review_status = null
        attendanceRequest.value.reviewed_log_type = null
        attendanceRequest.value.reviewed_time = null
        attendanceRequest.value.review_comment = null
}
</script>
