<template>
	<BaseLayout :pageTitle="__('مرخصی‌ها')">
		<template #body>
			<div class="w-full max-w-7xl mx-auto mt-7 mb-7 px-4">
				<ListView
					doctype="Leave Application"
					:pageTitle="__('مرخصی‌ها')"
					:tabButtons="TAB_BUTTONS"
					:fields="LEAVE_FIELDS"
					:filterConfig="FILTER_CONFIG"
					:hideHeader="true"
					:hideTabs="true"
					:embedded="true"
				/>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import BaseLayout from "@/components/BaseLayout.vue"
import ListView from "@/components/ListView.vue"
import { inject } from "vue"

const __ = inject("$translate")
const TAB_BUTTONS = ["My Leaves", "Team Leaves"] // __("My Leaves"), __("Team Leaves")
const LEAVE_FIELDS = [
	"name",
	"employee",
	"employee_name",
	"leave_type",
	"leave_duration_mode",
	"hourly_date",
	"hourly_from_time",
	"hourly_to_time",
	"from_date",
	"to_date",
	"total_leave_days",
	"total_leave_hours",
	"status",
]
const STATUS_FILTER_OPTIONS = ["Open", "Approved", "Rejected"] // __("Open"), __("Approved"), __("Rejected")
const FILTER_CONFIG = [
	{
		fieldname: "status",
		fieldtype: "Select",
		label: __("Status"),
		options: STATUS_FILTER_OPTIONS,
	},
	{
		fieldname: "leave_type",
		fieldtype: "Link",
		label: __("Leave Type"),
		options: "Leave Type",
	},
	{
		fieldname: "employee",
		fieldtype: "Link",
		label: __("Employee"),
		options: "Employee",
	},
	{
		fieldname: "department",
		fieldtype: "Link",
		label: __("Department"),
		options: "Department",
	},
	{ fieldname: "from_date", fieldtype: "Date", label: __("From Date") },
	{ fieldname: "to_date", fieldtype: "Date", label: __("To Date") },
]
</script>
