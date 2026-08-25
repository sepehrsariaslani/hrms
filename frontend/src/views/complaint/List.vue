<template>
	<ion-page>
		<ListView
			doctype="Employee Grievance"
			:pageTitle="__('Feedback History')"
			:tabButtons="TAB_BUTTONS"
			:fields="COMPLAINT_FIELDS"
			:filterConfig="FILTER_CONFIG"
		/>
	</ion-page>
</template>

<script setup>
import { IonPage } from "@ionic/vue"
import { inject } from "vue"

import ListView from "@/components/ListView.vue"

const __ = inject("$translate")
const TAB_BUTTONS = ["My Feedback", "Team Feedback"]

const COMPLAINT_FIELDS = [
	"name",
	"feedback_type",
	"subject",
	"raised_by",
	"employee_name",
	"grievance_type",
	"status",
	"date",
	"modified",
]

const FILTER_CONFIG = [
	{
		fieldname: "feedback_type",
		fieldtype: "Select",
		label: __("Feedback Type"),
		options: ["شکایت", "پیشنهاد", "انتقاد", "ایده"],
	},
	{
		fieldname: "status",
		fieldtype: "Select",
		label: __("Status"),
		options: ["Open", "Investigated", "Resolved", "Invalid"],
	},
	{
		fieldname: "grievance_type",
		fieldtype: "Link",
		label: __("Grievance Type"),
		options: "Grievance Type",
	},
	{
		fieldname: "raised_by",
		fieldtype: "Link",
		label: __("Raised By"),
		options: "Employee",
	},
	{
		fieldname: "date",
		fieldtype: "Date",
		label: __("Date"),
	},
]
</script>
