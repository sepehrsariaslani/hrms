<template>
	<BaseLayout :pageTitle="__('Employee Advances')">
		<template #body>
			<div class="w-full max-w-7xl mx-auto mt-7 mb-7 px-4">
				<ListView
					doctype="Employee Advance"
					:pageTitle="__('Employee Advances')"
					:tabButtons="TAB_BUTTONS"
					:fields="EMPLOYEE_ADVANCE_FIELDS"
					:filterConfig="FILTER_CONFIG"
					:embedded="true"
					:forceShowCreateButton="true"
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
const TAB_BUTTONS = ["My Advances", "Team Advances"] // __("My Advances"), __("Team Advances")
const EMPLOYEE_ADVANCE_FIELDS = [
	"name",
	"employee",
	"employee_name",
	"status",
	"purpose",
	"advance_amount",
	"paid_amount",
	"claimed_amount",
	"return_amount",
	"posting_date",
	"currency",
]

const STATUS_FILTER_OPTIONS = [
	"Draft",
	"Paid",
	"Unpaid",
	"Claimed",
	"Returned",
	"Partly Claimed and Returned",
	"Cancelled",
] // __("Draft"), __("Paid"), __("Unpaid"), __("Claimed"), __("Returned"), __("Partly Claimed and Returned"), __("Cancelled")
const FILTER_CONFIG = [
	{
		fieldname: "status",
		fieldtype: "Select",
		label: __("Status"),
		options: STATUS_FILTER_OPTIONS,
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
	{ fieldname: "posting_date", fieldtype: "Date", label: __("Posting Date") },
	{
		fieldname: "advance_amount",
		fieldtype: "Currency",
		label: __("Advance Amount"),
	},
	{ fieldname: "paid_amount", fieldtype: "Currency", label: __("Paid Amount") },
]
</script>
