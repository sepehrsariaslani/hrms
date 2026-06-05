<template>
	<BaseLayout :pageTitle="__('تاریخچه تردد')">
		<template #body>
			<div class="w-full max-w-7xl mx-auto mt-7 mb-7 px-4">
				<ListView
					doctype="Employee Checkin"
					:pageTitle="__('تاریخچه تردد')"
					:fields="EMPLOYEE_CHECKIN_FIELDS"
					:filterConfig="FILTER_CONFIG"
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

const EMPLOYEE_CHECKIN_FIELDS = ["name", "log_type", "time", "latitude", "longitude"]

const FILTER_CONFIG = [
	{
		fieldname: "log_type",
		fieldtype: "Select",
		label: __("نوع ثبت"),
		options: "IN\nOUT",
	},
	{
		fieldname: "shift",
		fieldtype: "Link",
		label: __("شیفت"),
		options: "Shift Type",
	},
]
</script>
