<template>
	<BaseLayout :pageTitle="pageTitle">
		<template #body>
			<div class="w-full max-w-5xl mx-auto mt-7 mb-7 p-4">
				<FormView
					v-if="formFields.data"
					doctype="Leave Application"
					v-model="leaveApplication"
					:isSubmittable="true"
					:returnOnCreate="true"
					returnOnCreateRoute="LeaveApplicationListView"
					:fields="formFields.data"
					:id="props.id"
					:showAttachmentView="true"
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

import BaseLayout from "@/components/BaseLayout.vue"
import FormView from "@/components/FormView.vue"
import { getEmployeeInfo, getEmployeeInfoByUserID } from "@/data/employees"
import { formatGregorianDate } from "@/utils/jalali"
import { localizeLeaveType } from "@/utils/leaveTypeLabels"

const __ = inject("$translate")
const route = useRoute()
const today = formatGregorianDate(new Date())
const HOURLY_MODE = "ساعتی"
const DAILY_MODE = "روزانه"

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})
const pageTitle = computed(() =>
	props.id ? __("Leave Application") : __("New Leave Application")
)

const sessionEmployee = inject("$employee")
const currEmployee = ref(sessionEmployee.data?.name)

// reactive object to store form data
const leaveApplication = ref({
	leave_duration_mode: DAILY_MODE,
})

function getInitialDateFromQuery() {
	const queryDate = String(route.query?.date || "")
	return /^\d{4}-\d{2}-\d{2}$/.test(queryDate) ? queryDate : today
}

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Leave Application" },
	transform(data) {
		return getFilteredFields(data)
	},
	onSuccess() {
		ensureLeaveModeDefault()
		updateLeaveModeFields()
		setSupervisorApprover()
		leaveTypes.reload()
	},
})
formFields.reload()

const leaveTypes = createResource({
	url: "hrms.api.get_leave_types",
	auto: false,
	makeParams() {
		return {
			employee: currEmployee.value,
			date: getLeaveBaseDate(),
		}
	},
	onSuccess(data) {
		setLeaveTypes(data)
	},
})

// form scripts
watch(
	() => leaveApplication.value.employee,
	(employee_id) => {
		if (props.id && employee_id !== currEmployee.value) {
			// if employee is not the current user, set form as read only
			setFormReadOnly()
		}
		currEmployee.value = employee_id
		leaveTypes.fetch({ employee: currEmployee.value, date: getLeaveBaseDate() })
		setSupervisorApprover()
	}
)

watch(
	() => sessionEmployee.data?.name,
	(employeeName) => {
		if (!employeeName) return
		currEmployee.value = employeeName
		if (!props.id) {
			leaveApplication.value.employee = employeeName
			leaveApplication.value.employee_name = sessionEmployee.data?.employee_name
			leaveApplication.value.company = sessionEmployee.data?.company
			leaveApplication.value.department = sessionEmployee.data?.department
			const selectedDate = getInitialDateFromQuery()
			leaveApplication.value.from_date = selectedDate
			leaveApplication.value.to_date = selectedDate
			leaveApplication.value.hourly_date = selectedDate
		}
		leaveTypes.reload()
		setSupervisorApprover()
	},
	{ immediate: true }
)

watch(
	() => route.query?.date,
	(value) => {
		const queryDate = String(value || "")
		if (!/^\d{4}-\d{2}-\d{2}$/.test(queryDate)) return
		if (props.id) return
		leaveApplication.value.from_date = queryDate
		leaveApplication.value.to_date = queryDate
		leaveApplication.value.hourly_date = queryDate
	},
	{ immediate: true }
)

watch(
	() => leaveApplication.value.leave_duration_mode,
	() => {
		updateLeaveModeFields()
		setTotalLeaveDays()
	}
)

watch(
	() => leaveApplication.value.leave_type,
	() => {
		setLeaveBalance()
	}
)

watch(
	() => leaveApplication.value.from_date,
	(from_date) => {
		if (leaveApplication.value.leave_duration_mode === HOURLY_MODE) return

		if (!leaveApplication.value.to_date) {
			leaveApplication.value.to_date = from_date
		}

		// fetch leave types for the selected date
		leaveTypes.fetch({
			employee: currEmployee.value,
			date: from_date,
		})
	}
)

watch(
	() => leaveApplication.value.hourly_date,
	(hourlyDate) => {
		if (leaveApplication.value.leave_duration_mode !== HOURLY_MODE || !hourlyDate) return

		leaveApplication.value.from_date = hourlyDate
		leaveApplication.value.to_date = hourlyDate
		leaveTypes.fetch({
			employee: currEmployee.value,
			date: hourlyDate,
		})
	}
)

watch(
	() => [leaveApplication.value.from_date, leaveApplication.value.to_date],
	([from_date, to_date]) => {
		if (leaveApplication.value.leave_duration_mode === HOURLY_MODE) return

		validateDates(from_date, to_date)
		setTotalLeaveDays()
	}
)

// helper functions
function getFilteredFields(fields) {
	// reduce noise from the form view by excluding unnecessary fields
	// ex: employee and other details can be fetched from the session user
	const excludeFields = [
		"naming_series",
		"sb_other_details",
		"salary_slip",
		"letter_head",
		"half_day",
		"half_day_date",
		"leave_approver",
		"leave_approver_name",
		"section_break_7",
		"column_break_18",
	]

	const employeeFields = [
		"employee",
		"employee_name",
		"department",
		"company",
		"follow_via_email",
		"status",
		"posting_date",
	]

	if (!props.id) excludeFields.push(...employeeFields)

	return fields.filter((field) => {
		const fieldname = field.fieldname || ""
		const label = String(field.label || "")
		if (excludeFields.includes(fieldname)) return false
		if (/shamsi|jalali/i.test(fieldname)) return false
		if (label.includes("شمسی")) return false
		return true
	})
}

function setFormReadOnly() {
	if (leaveApplication.value.leave_approver === sessionEmployee.data.user_id) return
	formFields.data.map((field) => (field.read_only = true))
}

function validateDates(from_date, to_date) {
	if (!(from_date && to_date)) return

	const error_message =
		from_date > to_date ? __("To Date cannot be before From Date") : ""

	const from_date_field = formFields.data.find(
		(field) => field.fieldname === "from_date"
	)
	from_date_field.error_message = error_message
}

function getLeaveBaseDate() {
	return leaveApplication.value.leave_duration_mode === HOURLY_MODE
		? leaveApplication.value.hourly_date || today
		: leaveApplication.value.from_date || today
}

function ensureLeaveModeDefault() {
	if (!leaveApplication.value.leave_duration_mode) {
		leaveApplication.value.leave_duration_mode = DAILY_MODE
	}
}

function setTotalLeaveDays() {
	if (!areValuesSet()) return

	const leaveDays = createResource({
		url: "hrms.hr.doctype.leave_application.leave_application.get_number_of_leave_days",
		params: {
			employee: currEmployee.value,
			leave_type: leaveApplication.value.leave_type,
			from_date: leaveApplication.value.from_date,
			to_date: leaveApplication.value.to_date,
			half_day: 0,
			half_day_date: null,
		},
		onSuccess(data) {
			leaveApplication.value.total_leave_days = data
		},
	})
	leaveDays.reload()
	setLeaveBalance()
}

function setLeaveBalance() {
	if (!areValuesSet()) return

	const leaveBalance = createResource({
		url: "hrms.hr.doctype.leave_application.leave_application.get_leave_balance_on",
		params: {
			employee: currEmployee.value,
			date: leaveApplication.value.from_date,
			to_date: leaveApplication.value.to_date,
			leave_type: leaveApplication.value.leave_type,
			consider_all_leaves_in_the_allocation_period: 1,
		},
		onSuccess(data) {
			leaveApplication.value.leave_balance = data
		},
	})
	leaveBalance.reload()
}

function updateLeaveModeFields() {
	if (!formFields.data) return

	ensureLeaveModeDefault()
	const isHourly = leaveApplication.value.leave_duration_mode === HOURLY_MODE
	const fromDate = formFields.data.find((field) => field.fieldname === "from_date")
	const toDate = formFields.data.find((field) => field.fieldname === "to_date")
	const hourlyDate = formFields.data.find((field) => field.fieldname === "hourly_date")
	const hourlyFromTime = formFields.data.find(
		(field) => field.fieldname === "hourly_from_time"
	)
	const hourlyToTime = formFields.data.find(
		(field) => field.fieldname === "hourly_to_time"
	)

	if (fromDate) {
		fromDate.hidden = isHourly ? 1 : 0
		fromDate.reqd = isHourly ? 0 : 1
	}
	if (toDate) {
		toDate.hidden = isHourly ? 1 : 0
		toDate.reqd = isHourly ? 0 : 1
	}
	if (hourlyDate) {
		hourlyDate.hidden = isHourly ? 0 : 1
		hourlyDate.reqd = isHourly ? 1 : 0
	}
	if (hourlyFromTime) {
		hourlyFromTime.hidden = isHourly ? 0 : 1
		hourlyFromTime.reqd = isHourly ? 1 : 0
	}
	if (hourlyToTime) {
		hourlyToTime.hidden = isHourly ? 0 : 1
		hourlyToTime.reqd = isHourly ? 1 : 0
	}

	if (isHourly && leaveApplication.value.hourly_date) {
		leaveApplication.value.from_date = leaveApplication.value.hourly_date
		leaveApplication.value.to_date = leaveApplication.value.hourly_date
	}
}

function setSupervisorApprover() {
	const expenseApproverUser = sessionEmployee.data?.expense_approver
	const expenseApproverEmployee = expenseApproverUser
		? getEmployeeInfoByUserID(expenseApproverUser)
		: null
	if (expenseApproverUser) {
		leaveApplication.value.leave_approver = expenseApproverUser
		leaveApplication.value.leave_approver_name =
			expenseApproverEmployee?.employee_name ||
			expenseApproverEmployee?.name ||
			expenseApproverUser
		return
	}

	const reportsTo = sessionEmployee.data?.reports_to
	const supervisor = reportsTo ? getEmployeeInfo(reportsTo) : null
	if (supervisor?.user_id) {
		leaveApplication.value.leave_approver = supervisor.user_id
		leaveApplication.value.leave_approver_name = supervisor.employee_name || supervisor.name
	}
}

function setLeaveTypes(data) {
	const leave_type = formFields.data.find(
		(field) => field.fieldname === "leave_type"
	)
	if (!leave_type) return
	leave_type.documentList = data?.map((typeName) => ({
		label: localizeLeaveType(typeName),
		value: typeName,
	}))
	if (!leaveApplication.value.leave_type && leave_type.documentList?.length) {
		leaveApplication.value.leave_type = leave_type.documentList[0].value
	}
}

function areValuesSet() {
	return (
		leaveApplication.value.from_date &&
		leaveApplication.value.to_date &&
		leaveApplication.value.leave_type
	)
}

function validateForm() {
	ensureLeaveModeDefault()
	if (!leaveApplication.value.leave_type) {
		const leaveTypeField = formFields.data?.find((field) => field.fieldname === "leave_type")
		const firstLeaveType = leaveTypeField?.documentList?.[0]?.value
		if (firstLeaveType) leaveApplication.value.leave_type = firstLeaveType
	}

	const isHourly = leaveApplication.value.leave_duration_mode === HOURLY_MODE
	if (isHourly) {
		const leaveDate = leaveApplication.value.hourly_date || today
		leaveApplication.value.from_date = leaveDate
		leaveApplication.value.to_date = leaveDate
	}

	setSupervisorApprover()
	if (!leaveApplication.value.leave_approver) {
		leaveApplication.value.leave_approver = sessionEmployee.data.user_id
	}
	leaveApplication.value.employee = currEmployee.value
	leaveApplication.value.half_day = 0
	leaveApplication.value.half_day_date = null
}
</script>
