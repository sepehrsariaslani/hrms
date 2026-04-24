<template>
	<ion-tab-bar
		slot="bottom"
		class="bg-white dark:bg-[#171719] shadow-md w-full max-w-7xl mx-auto py-2 pb-2 standalone:pb-safe-bottom md:rounded-t-xl md:border md:border-gray-200 dark:md:border-[#2d2d33] lg:hidden"
		data-tour="bottom-tabs"
	>
		<ion-tab-button
			v-for="item in tabItems"
			:key="item.key"
			:tab="item.key"
			:href="item.route"
			routerDirection="none"
			:class="[
				'bg-white dark:bg-[#171719] text-xs space-y-1.5 !hover:border-gray-300 !hover:text-gray-700 dark:!hover:text-gray-200 transition active:scale-95',
				item.emphasized
					? '-mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-2 pb-2 pt-1 shadow-sm dark:border-amber-700/40 dark:bg-amber-900/20'
					: '',
				route.path === item.route
					? 'border-gray-900 dark:border-gray-200 text-gray-800 dark:text-gray-100 font-semibold'
					: 'text-gray-600 dark:text-gray-400 font-normal',
			]"
		>
			<component :is="item.icon" :class="item.emphasized ? 'h-6 w-6' : 'h-5 w-5'" />
			<div :class="item.emphasized ? 'text-sm font-bold' : ''">{{ item.title }}</div>
		</ion-tab-button>
	</ion-tab-bar>
</template>

<script setup>
import { useRoute } from "vue-router"

import { IonTabBar, IonTabButton } from "@ionic/vue"

import HomeIcon from "@/components/icons/HomeIcon.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import ExpenseIcon from "@/components/icons/ExpenseIcon.vue"
import SalaryIcon from "@/components/icons/SalaryIcon.vue"
import AttendanceIcon from "@/components/icons/AttendanceIcon.vue"
import { inject } from "vue"

const __ = inject("$translate")

const route = useRoute()

const tabItems = [
	{
		key: "home",
		icon: HomeIcon,
		title: __("خانه"),
		route: "/home",
	},
	{
		key: "leaves",
		icon: LeaveIcon,
		title: __("مرخصی"),
		route: "/dashboard/leaves",
	},
	{
		key: "attendance",
		icon: AttendanceIcon,
		title: __("تقویم"),
		route: "/dashboard/attendance",
		emphasized: true,
	},
	{
		key: "expenses",
		icon: ExpenseIcon,
		title: __("هزینه"),
		route: "/dashboard/expense-claims",
	},
	{
		key: "salary",
		icon: SalaryIcon,
		title: __("حقوق"),
		route: "/dashboard/salary-slips",
	},
]
</script>
