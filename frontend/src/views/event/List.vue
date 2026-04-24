<template>
	<ion-page>
		<ListView
			doctype="Event"
			:pageTitle="__('رویدادها')"
			:fields="EVENT_FIELDS"
			:filterConfig="FILTER_CONFIG"
		/>
	</ion-page>
</template>

<script setup>
import { IonPage } from "@ionic/vue"
import { inject } from "vue"

import ListView from "@/components/ListView.vue"

const __ = inject("$translate")

const EVENT_FIELDS = [
	"name",
	"subject",
	"event_type",
	"starts_on",
	"ends_on",
	"all_day",
	"location",
	"owner",
	"creation",
	"modified",
]

const FILTER_CONFIG = [
	{
		fieldname: "event_type",
		fieldtype: "Select",
		label: __("نوع رویداد"),
		options: ["Public", "Private"],
	},
	{
		fieldname: "starts_on",
		fieldtype: "Date",
		label: __("از تاریخ"),
	},
	{
		fieldname: "ends_on",
		fieldtype: "Date",
		label: __("تا تاریخ"),
	},
	{
		fieldname: "all_day",
		fieldtype: "Select",
		label: __("تمام‌روز"),
		options: ["0", "1"],
	},
]
</script>
