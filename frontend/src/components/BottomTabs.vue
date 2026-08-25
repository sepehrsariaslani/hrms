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
				isTabActive(item)
					? 'border-gray-900 dark:border-gray-200 text-gray-800 dark:text-gray-100 font-semibold'
					: 'text-gray-600 dark:text-gray-400 font-normal',
			]"
		>
			<component v-if="item.icon" :is="item.icon" class="h-5 w-5" />
			<FeatherIcon v-else :name="item.featherIcon" class="h-5 w-5" />
			<div>{{ item.title }}</div>
		</ion-tab-button>
	</ion-tab-bar>
</template>

<script setup>
import { computed, inject } from "vue"
import { useRoute } from "vue-router"

import { IonTabBar, IonTabButton } from "@ionic/vue"
import { FeatherIcon } from "frappe-ui"

import AppraisalIcon from "@/components/icons/AppraisalIcon.vue"
import AttendanceIcon from "@/components/icons/AttendanceIcon.vue"
import ComplaintIcon from "@/components/icons/ComplaintIcon.vue"
import EmployeeAdvanceIcon from "@/components/icons/EmployeeAdvanceIcon.vue"
import EventIcon from "@/components/icons/EventIcon.vue"
import ExpenseIcon from "@/components/icons/ExpenseIcon.vue"
import HomeIcon from "@/components/icons/HomeIcon.vue"
import ImprestIcon from "@/components/icons/ImprestIcon.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import MealIcon from "@/components/icons/MealIcon.vue"
import MissionIcon from "@/components/icons/MissionIcon.vue"
import NewsletterIcon from "@/components/icons/NewsletterIcon.vue"
import SalaryIcon from "@/components/icons/SalaryIcon.vue"
import ShiftIcon from "@/components/icons/ShiftIcon.vue"
import { employeeDeskVisibility, layoutHasImprestAccess } from "@/data/layout"
import { employeeDeskGlobalPersonalization } from "@/data/personalization"

const __ = inject("$translate")
const employee = inject("$employee")

const route = useRoute()

const canSeeAllocatorShiftTools = computed(() =>
	Boolean(employee.data?.is_shift_allocator || employee.data?.is_shift_allocator_by_role)
)
const canSeeWeeklyShiftPlanner = computed(() => {
	return Boolean(
		employee.data?.variable_shift
			|| employee.data?.has_rotational_shift
			|| employee.data?.needs_shift_registration
	)
})

const allTabItems = [
	{
		key: "home",
		icon: HomeIcon,
		defaultTitle: __("خانه"),
		route: "/home",
	},
	{
		key: "requests",
		featherIcon: "inbox",
		defaultTitle: __("درخواست‌ها"),
		route: "/dashboard/requests",
		visibilityKey: "enable_requests_center",
	},
	{
		key: "attendance",
		icon: AttendanceIcon,
		defaultTitle: __("تقویم حضور و غیاب"),
		route: "/dashboard/attendance",
		visibilityKey: "enable_attendance",
	},
	{
		key: "missions",
		icon: MissionIcon,
		defaultTitle: __("ماموریت‌ها"),
		route: "/dashboard/missions",
		visibilityKey: "enable_missions",
	},
	{
		key: "weekly_shift",
		icon: ShiftIcon,
		defaultTitle: __("شیفت هفته"),
		route: "/weekly-shift-planner",
		visibilityKey: "enable_attendance",
		isAllowed: () => canSeeWeeklyShiftPlanner.value,
	},
	{
		key: "leaves",
		icon: LeaveIcon,
		defaultTitle: __("مرخصی"),
		route: "/dashboard/leaves",
		visibilityKey: "enable_leaves",
	},
	{
		key: "shift_allocator_scheduler",
		icon: ShiftIcon,
		defaultTitle: __("تقویم شیفت هفتگی"),
		route: "/shift-allocator-scheduler",
		visibilityKey: "enable_attendance",
		isAllowed: () => canSeeAllocatorShiftTools.value,
	},
	{
		key: "imprest",
		icon: ImprestIcon,
		defaultTitle: __("تنخواه"),
		route: "/dashboard/imprest",
		visibilityKey: "enable_imprest",
		isAllowed: () => layoutHasImprestAccess.value,
	},
	{
		key: "expenses",
		icon: ExpenseIcon,
		defaultTitle: __("مطالبه هزینه"),
		route: "/dashboard/expense-claims",
		visibilityKey: "enable_expense_claims",
	},
	{
		key: "advances",
		icon: EmployeeAdvanceIcon,
		defaultTitle: __("درخواست مساعده"),
		route: "/employee-advances",
		visibilityKey: "enable_employee_advances",
	},
	{
		key: "events",
		icon: EventIcon,
		defaultTitle: __("رویدادها"),
		route: "/dashboard/events",
		visibilityKey: "enable_events",
	},
	{
		key: "salary",
		icon: SalaryIcon,
		defaultTitle: __("حقوق"),
		route: "/dashboard/salary-slips",
		visibilityKey: "enable_salary_slips",
	},
	{
		key: "appraisals",
		icon: AppraisalIcon,
		defaultTitle: __("ارزیابی"),
		route: "/dashboard/appraisals",
		visibilityKey: "enable_appraisals",
	},
	{
		key: "meals",
		icon: MealIcon,
		defaultTitle: __("غذا"),
		route: "/dashboard/meals",
		visibilityKey: "enable_meals",
	},
	{
		key: "complaints",
		icon: ComplaintIcon,
		defaultTitle: __("شکایات"),
		route: "/dashboard/complaints",
		visibilityKey: "enable_complaints",
	},
	{
		key: "newsletters",
		icon: NewsletterIcon,
		defaultTitle: __("خبرنامه"),
		route: "/dashboard/newsletters",
		visibilityKey: "enable_newsletters",
	},
	{
		key: "profile",
		featherIcon: "user",
		defaultTitle: __("پروفایل"),
		route: "/profile",
	},
	{
		key: "notifications",
		featherIcon: "bell",
		defaultTitle: __("اعلان‌ها"),
		route: "/notifications",
	},
	{
		key: "settings",
		featherIcon: "settings",
		defaultTitle: __("تنظیمات"),
		route: "/settings",
	},
]

const visibilityMap = computed(() => employeeDeskVisibility.data || {})
const navbarPreferences = computed(() => {
	return employeeDeskGlobalPersonalization.data?.preferences || {}
})
const availableTabItems = computed(() =>
	allTabItems.filter(
		(item) =>
			(!item.visibilityKey || visibilityMap.value?.[item.visibilityKey] !== false)
			&& (typeof item.isAllowed !== "function" || item.isAllowed())
	)
)
const hiddenTabSet = computed(() => new Set(navbarPreferences.value.hidden_tab_keys || []))
const tabOrderMap = computed(
	() => new Map((navbarPreferences.value.tab_order_keys || []).map((key, index) => [key, index]))
)

const tabItems = computed(() => {
	const tabLabels = navbarPreferences.value.tab_labels || {}
	const items = [...availableTabItems.value]
		.sort((left, right) => {
			const leftOrder = tabOrderMap.value.has(left.key)
				? tabOrderMap.value.get(left.key)
				: Number.MAX_SAFE_INTEGER
			const rightOrder = tabOrderMap.value.has(right.key)
				? tabOrderMap.value.get(right.key)
				: Number.MAX_SAFE_INTEGER
			if (leftOrder !== rightOrder) return leftOrder - rightOrder
			return 0
		})
		.map((item) => ({
			...item,
			title: tabLabels[item.key] || item.defaultTitle,
		}))
		.filter((item) => !hiddenTabSet.value.has(item.key))

	return items.slice(0, 5)
})

function isTabActive(item) {
	return route.path === item.route || route.path.startsWith(`${item.route}/`)
}
</script>
