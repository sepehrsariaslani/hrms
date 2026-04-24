<template>
	<ion-page>
		<ion-content class="ion-no-padding">
			<ion-refresher slot="fixed" @ionRefresh="handlePullToRefresh">
				<ion-refresher-content
					pulling-text="برای بروزرسانی بکشید"
					refreshing-text="در حال بروزرسانی..."
				/>
			</ion-refresher>

			<div class="min-h-screen bg-slate-100">
				<div class="flex min-h-screen w-full">
					<aside
						class="hidden w-72 shrink-0 flex-col border-l border-slate-200 bg-white lg:flex"
					>
						<div class="flex items-center gap-3 border-b border-slate-200 px-6 py-5">
							<div
								class="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-amber-600 to-orange-600 text-white shadow"
							>
								<FeatherIcon name="grid" class="h-5 w-5" />
							</div>
							<div>
								<div class="text-sm font-semibold text-slate-500">{{ __("HRMS") }}</div>
								<div class="text-lg font-bold text-slate-900">{{ __("Employee Desk") }}</div>
							</div>
						</div>

						<div class="border-b border-slate-100 p-4">
							<div class="flex items-center gap-3 rounded-2xl bg-slate-50 p-3">
								<Avatar
									:image="profileImage"
									:label="employeeName"
									size="xl"
								/>
								<div class="min-w-0">
									<div class="truncate text-sm font-semibold text-slate-900">
										{{ employeeName }}
									</div>
									<div class="truncate text-xs text-slate-500">
										{{ employeeRole }}
									</div>
								</div>
							</div>
						</div>

						<nav class="flex-1 space-y-4 overflow-y-auto px-4 py-4">
							<div v-for="group in menuGroups" :key="group.title">
								<p class="mb-2 px-3 text-[11px] font-bold tracking-wide text-slate-400">
									{{ group.title }}
								</p>
								<div class="space-y-1">
									<router-link
										v-for="item in group.items"
										:key="item.route"
										:to="item.route"
										class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition"
										:class="
											isActive(item.route)
												? 'bg-amber-50 text-amber-700'
												: 'text-slate-600 hover:bg-slate-100'
										"
									>
										<FeatherIcon :name="item.icon" class="h-4 w-4" />
										<span class="flex-1">{{ item.label }}</span>
										<span
											v-if="item.badge"
											class="inline-flex min-w-6 items-center justify-center rounded-full bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-700"
										>
											{{ toPersianDigits(item.badge) }}
										</span>
									</router-link>
								</div>
							</div>
						</nav>
					</aside>

					<div class="flex min-w-0 flex-1 flex-col">
						<header class="sticky top-0 z-10 border-b border-slate-200 bg-white/95 backdrop-blur">
							<div class="flex items-center gap-3 px-4 py-3 md:px-6">
								<Button
									variant="ghost"
									class="!rounded-xl lg:!hidden"
									@click="sidebarOpen = true"
								>
									<FeatherIcon name="menu" class="h-5 w-5" />
								</Button>
								<div class="min-w-0">
									<div class="truncate text-base font-bold text-slate-900 md:text-lg">
										{{ __("داشبورد کارمند") }}
									</div>
									<div class="truncate text-xs text-slate-500 md:text-sm">
										{{ todayLabel }}
									</div>
								</div>
								<div class="mr-auto flex items-center gap-2">
									<router-link :to="{ name: 'Notifications' }" class="rounded-xl border border-slate-200 p-2">
										<FeatherIcon name="bell" class="h-4 w-4 text-slate-600" />
									</router-link>
									<router-link :to="{ name: 'Profile' }">
										<Avatar
											:image="profileImage"
											:label="employeeName"
											size="lg"
										/>
									</router-link>
								</div>
							</div>
						</header>

						<main class="flex-1 space-y-6 p-4 md:p-6">
							<section class="grid gap-4 xl:grid-cols-12">
								<div class="xl:col-span-6">
									<CheckInPanel />
								</div>
								<div class="grid gap-4 sm:grid-cols-2 xl:col-span-6">
									<div
										v-for="card in kpiCards"
										:key="card.title"
										class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
									>
										<div class="text-xs font-semibold text-slate-500">
											{{ card.title }}
										</div>
										<div class="mt-2 text-2xl font-bold text-slate-900">
											{{ card.value }}
										</div>
										<div class="mt-1 text-xs text-slate-500">
											{{ card.caption }}
										</div>
									</div>
								</div>
							</section>

							<section class="grid gap-4 xl:grid-cols-3">
								<div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm xl:col-span-2">
									<div class="mb-4 flex items-center justify-between">
										<h3 class="text-sm font-bold text-slate-800">{{ __("روند فعالیت ۶ ماه اخیر") }}</h3>
										<div class="flex items-center gap-3 text-[11px] text-slate-500">
											<span class="inline-flex items-center gap-1">
												<span class="h-2 w-2 rounded-full bg-sky-500" />
												{{ __("حضور") }}
											</span>
											<span class="inline-flex items-center gap-1">
												<span class="h-2 w-2 rounded-full bg-emerald-500" />
												{{ __("مرخصی") }}
											</span>
											<span class="inline-flex items-center gap-1">
												<span class="h-2 w-2 rounded-full bg-amber-500" />
												{{ __("هزینه") }}
											</span>
										</div>
									</div>
									<div class="grid grid-cols-6 gap-2 md:gap-3">
										<div
											v-for="bucket in activityBuckets"
											:key="bucket.key"
											class="flex flex-col items-center gap-2"
										>
											<div class="flex h-36 items-end gap-1 md:h-44">
												<div
													class="w-2 rounded-t bg-sky-500 transition-all"
													:style="{ height: getActivityBarHeight(bucket.attendance) }"
												/>
												<div
													class="w-2 rounded-t bg-emerald-500 transition-all"
													:style="{ height: getActivityBarHeight(bucket.leaves) }"
												/>
												<div
													class="w-2 rounded-t bg-amber-500 transition-all"
													:style="{ height: getActivityBarHeight(bucket.expenses) }"
												/>
											</div>
											<div class="text-[11px] text-slate-400">{{ bucket.label }}</div>
											<div class="text-xs font-semibold text-slate-700">
												{{ toPersianDigits(bucket.total) }}
											</div>
										</div>
									</div>
								</div>

								<div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
									<h3 class="text-sm font-bold text-slate-800">{{ __("وضعیت هزینه‌ها") }}</h3>
									<div class="mt-5 flex items-center justify-center">
										<div
											class="relative h-36 w-36 rounded-full"
											:style="expenseDonutStyle"
										>
											<div
												class="absolute inset-5 flex items-center justify-center rounded-full bg-white text-center"
											>
												<div>
													<div class="text-[11px] text-slate-500">{{ __("کل مبلغ") }}</div>
													<div class="mt-1 text-xs font-bold text-slate-800">
														{{ formatCurrency(expenseTotalAmount, companyCurrency) }}
													</div>
												</div>
											</div>
										</div>
									</div>
									<div class="mt-4 space-y-2">
										<div
											v-for="status in expenseStatusSeries"
											:key="status.label"
											class="flex items-center justify-between text-xs"
										>
											<div class="inline-flex items-center gap-2 text-slate-600">
												<span class="h-2.5 w-2.5 rounded-full" :class="status.colorClass" />
												{{ status.label }}
											</div>
											<div class="font-semibold text-slate-800">
												{{ formatCurrency(status.value, companyCurrency) }}
											</div>
										</div>
									</div>
								</div>
							</section>

							<section class="grid gap-4 xl:grid-cols-3">
								<div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm xl:col-span-2">
									<h3 class="mb-4 text-sm font-bold text-slate-800">{{ __("نمودار مانده مرخصی") }}</h3>
									<div v-if="leaveBalanceSeries.length" class="space-y-3">
										<div v-for="item in leaveBalanceSeries" :key="item.label">
											<div class="mb-1 flex items-center justify-between text-xs">
												<span class="font-medium text-slate-700">{{ item.label }}</span>
												<span class="text-slate-500">
													{{ toPersianDigits(item.balance) }}/{{ toPersianDigits(item.total) }}
												</span>
											</div>
											<div class="h-2 rounded-full bg-slate-100">
												<div
													class="h-2 rounded-full bg-gradient-to-r from-amber-500 to-orange-600"
													:style="{ width: `${item.percentage}%` }"
												/>
											</div>
										</div>
									</div>
									<EmptyState v-else :message="__('You have no leaves allocated')" />
								</div>

								<div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
									<h3 class="mb-4 text-sm font-bold text-slate-800">{{ __("میانبرهای سریع") }}</h3>
									<div class="space-y-2">
										<router-link
											v-for="link in quickLinks"
											:key="link.title"
											:to="{ name: link.route }"
											class="flex items-center gap-3 rounded-xl border border-slate-100 px-3 py-2.5 transition hover:bg-slate-50"
										>
											<component :is="link.icon" class="h-4 w-4 text-slate-500" />
											<span class="flex-1 text-sm text-slate-700">{{ link.title }}</span>
											<span
												v-if="Number(link.badge) > 0"
												class="inline-flex min-w-6 items-center justify-center rounded-full bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-700"
											>
												{{ toPersianDigits(link.badge) }}
											</span>
										</router-link>
									</div>
								</div>
							</section>

							<section class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
								<h3 class="mb-4 text-sm font-bold text-slate-800">{{ __("درخواست‌های اخیر") }}</h3>
								<RequestPanel />
							</section>
						</main>
					</div>
				</div>
			</div>
		</ion-content>

		<Teleport to="body">
			<Transition name="fade">
				<div
					v-if="sidebarOpen"
					class="fixed inset-0 z-40 bg-black/40 lg:hidden"
					@click="sidebarOpen = false"
				/>
			</Transition>
			<Transition name="slide-right">
				<aside
					v-if="sidebarOpen"
					class="fixed top-0 right-0 z-50 flex h-full w-72 flex-col bg-white shadow-xl lg:hidden"
				>
					<div class="flex items-center justify-between border-b border-slate-200 px-4 py-4">
						<div class="text-base font-bold text-slate-900">{{ __("منو") }}</div>
						<Button variant="ghost" class="!rounded-xl" @click="sidebarOpen = false">
							<FeatherIcon name="x" class="h-5 w-5" />
						</Button>
					</div>
					<nav class="flex-1 space-y-4 overflow-y-auto px-4 py-4">
						<div v-for="group in menuGroups" :key="`${group.title}-mobile`">
							<p class="mb-2 px-3 text-[11px] font-bold tracking-wide text-slate-400">
								{{ group.title }}
							</p>
							<div class="space-y-1">
								<router-link
									v-for="item in group.items"
									:key="`mobile-${item.route}`"
									:to="item.route"
									class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition"
									:class="
										isActive(item.route)
											? 'bg-amber-50 text-amber-700'
											: 'text-slate-600 hover:bg-slate-100'
									"
									@click="sidebarOpen = false"
								>
									<FeatherIcon :name="item.icon" class="h-4 w-4" />
									<span class="flex-1">{{ item.label }}</span>
									<span
										v-if="item.badge"
										class="inline-flex min-w-6 items-center justify-center rounded-full bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-700"
									>
										{{ toPersianDigits(item.badge) }}
									</span>
								</router-link>
							</div>
						</div>
					</nav>
				</aside>
			</Transition>
		</Teleport>
	</ion-page>
</template>

<script setup>
import { computed, inject, markRaw, ref, watch } from "vue"
import { useRoute } from "vue-router"
import { IonContent, IonPage, IonRefresher, IonRefresherContent } from "@ionic/vue"
import { Avatar, FeatherIcon } from "frappe-ui"

import RequestPanel from "@/components/RequestPanel.vue"
import CheckInPanel from "@/components/CheckInPanel.vue"
import AttendanceIcon from "@/components/icons/AttendanceIcon.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import ExpenseIcon from "@/components/icons/ExpenseIcon.vue"
import EmployeeAdvanceIcon from "@/components/icons/EmployeeAdvanceIcon.vue"
import SalaryIcon from "@/components/icons/SalaryIcon.vue"
import ComplaintIcon from "@/components/icons/ComplaintIcon.vue"
import MealIcon from "@/components/icons/MealIcon.vue"
import AppraisalIcon from "@/components/icons/AppraisalIcon.vue"
import NewsletterIcon from "@/components/icons/NewsletterIcon.vue"
import ImprestIcon from "@/components/icons/ImprestIcon.vue"
import MissionIcon from "@/components/icons/MissionIcon.vue"
import EventIcon from "@/components/icons/EventIcon.vue"

import { myAttendanceRequests } from "@/data/attendance"
import { expenseClaimSummary, myClaims } from "@/data/claims"
import { myAppraisals } from "@/data/appraisals"
import { leaveBalance, myLeaves } from "@/data/leaves"
import { layoutHasImprestAccess, layoutUnreadNewsletterCount } from "@/data/layout"
import { buildNavbarGroups } from "@/data/navigation"
import { activeMissions } from "@/data/missions"
import { localizeLeaveType } from "@/utils/leaveTypeLabels"
import { formatCurrency } from "@/utils/formatters"
import { formatJalaliDate, toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")
const user = inject("$user")
const employee = inject("$employee")
const dayjs = inject("$dayjs")
const route = useRoute()

const sidebarOpen = ref(false)

watch(
	() => route.path,
	() => {
		sidebarOpen.value = false
	}
)

const employeeName = computed(
	() => employee.data?.employee_name || user.data?.full_name || __("کاربر")
)
const employeeRole = computed(
	() => employee.data?.designation || employee.data?.department || __("کارمند")
)
const profileImage = computed(() => employee.data?.image || user.data?.user_image || "")
const todayLabel = computed(() => formatJalaliDate(new Date(), { withWeekday: true }))

const PENDING_STATUSES = new Set(["draft", "open", "pending", "pending approval"])
const APPROVED_STATUSES = new Set(["approved", "accepted", "completed"])

const allMyRequests = computed(() => [
	...(myAttendanceRequests.data || []),
	...(myLeaves.data || []),
	...(myClaims.data || []),
])

function normalizeStatus(status) {
	return String(status || "").trim().toLowerCase()
}

function countByStatus(statuses) {
	return allMyRequests.value.filter((row) => statuses.has(normalizeStatus(row.status))).length
}

const pendingRequestsCount = computed(() => countByStatus(PENDING_STATUSES))
const approvedRequestsCount = computed(() => countByStatus(APPROVED_STATUSES))

const totalLeaveBalance = computed(() =>
	Object.values(leaveBalance.data || {}).reduce(
		(total, row) => total + Number(row?.balance_leaves || 0),
		0
	)
)
const activeMissionCount = computed(() => activeMissions.value.length)

const latestAppraisalScore = computed(() => {
	const rows = [...(myAppraisals.data || [])]
	if (!rows.length) return "-"
	rows.sort((a, b) => {
		const left = new Date(a?.end_date || a?.modified || a?.creation || 0).getTime()
		const right = new Date(b?.end_date || b?.modified || b?.creation || 0).getTime()
		return right - left
	})
	const score = Number(rows[0]?.final_score)
	return Number.isFinite(score) ? toPersianDigits(score.toFixed(2)) : "-"
})

const expenseRejectedAmount = computed(() => {
	const totalRejected = Number(expenseClaimSummary.data?.total_rejected_amount || 0)
	const claimedInApproved = Number(expenseClaimSummary.data?.total_claimed_in_approved || 0)
	const approved = Number(expenseClaimSummary.data?.total_approved_amount || 0)
	return Math.max(0, totalRejected + (claimedInApproved - approved))
})

const companyCurrency = computed(() => expenseClaimSummary.data?.currency)
const expenseTotalAmount = computed(() => {
	const pending = Number(expenseClaimSummary.data?.total_pending_amount || 0)
	const approved = Number(expenseClaimSummary.data?.total_approved_amount || 0)
	const rejected = Number(expenseRejectedAmount.value || 0)
	return pending + approved + rejected
})

const expenseStatusSeries = computed(() => [
	{
		label: __("Pending"),
		value: Number(expenseClaimSummary.data?.total_pending_amount || 0),
		color: "#f59e0b",
		colorClass: "bg-amber-500",
	},
	{
		label: __("Approved"),
		value: Number(expenseClaimSummary.data?.total_approved_amount || 0),
		color: "#10b981",
		colorClass: "bg-emerald-500",
	},
	{
		label: __("Rejected"),
		value: Number(expenseRejectedAmount.value || 0),
		color: "#ef4444",
		colorClass: "bg-rose-500",
	},
])

const expenseDonutStyle = computed(() => {
	const total = expenseTotalAmount.value
	if (!total) {
		return {
			background: "conic-gradient(#e2e8f0 0% 100%)",
		}
	}
	let offset = 0
	const parts = expenseStatusSeries.value.map((item) => {
		const span = (item.value / total) * 100
		const from = offset
		const to = offset + span
		offset = to
		return `${item.color} ${from}% ${to}%`
	})
	return {
		background: `conic-gradient(${parts.join(",")})`,
	}
})

const activityBuckets = computed(() => {
	const buckets = Array.from({ length: 6 }, (_, index) => {
		const month = dayjs().subtract(5 - index, "month")
		return {
			key: month.format("YYYY-MM"),
			label: month.format("MMM"),
			attendance: 0,
			leaves: 0,
			expenses: 0,
		}
	})
	const bucketMap = Object.fromEntries(buckets.map((bucket) => [bucket.key, bucket]))

	const addToBucket = (rows, category, fields) => {
		(rows || []).forEach((row) => {
			const dateValue = fields.map((field) => row?.[field]).find(Boolean)
			if (!dateValue) return
			const key = dayjs(dateValue).format("YYYY-MM")
			if (bucketMap[key]) {
				bucketMap[key][category] += 1
			}
		})
	}

	addToBucket(myAttendanceRequests.data, "attendance", ["from_date", "creation", "modified"])
	addToBucket(myLeaves.data, "leaves", ["from_date", "creation", "modified"])
	addToBucket(myClaims.data, "expenses", ["posting_date", "creation", "modified"])

	return buckets.map((bucket) => ({
		...bucket,
		total: bucket.attendance + bucket.leaves + bucket.expenses,
	}))
})

const activityMaxValue = computed(() => {
	const allValues = activityBuckets.value.flatMap((bucket) => [
		bucket.attendance,
		bucket.leaves,
		bucket.expenses,
	])
	return Math.max(1, ...allValues)
})

function getActivityBarHeight(value) {
	return `${Math.max(8, (value / activityMaxValue.value) * 100)}%`
}

const leaveBalanceSeries = computed(() =>
	Object.entries(leaveBalance.data || {}).map(([leaveType, row]) => {
		const total = Number(row?.allocated_leaves || 0)
		const balance = Number(row?.balance_leaves || 0)
		const percentage = total > 0 ? Math.min(100, Math.max(0, (balance / total) * 100)) : 0
		return {
			label: localizeLeaveType(leaveType),
			total: total.toFixed(1).replace(/\.0$/, ""),
			balance: balance.toFixed(1).replace(/\.0$/, ""),
			percentage,
		}
	})
)

const quickLinks = computed(() => {
	const links = [
		{
			icon: markRaw(AttendanceIcon),
			title: __("Request Attendance"),
			route: "AttendanceRequestFormView",
		},
		{
			icon: markRaw(LeaveIcon),
			title: __("Request Leave"),
			route: "LeaveApplicationFormView",
		},
		{
			icon: markRaw(ExpenseIcon),
			title: __("Claim an Expense"),
			route: "ExpenseClaimFormView",
		},
		{
			icon: markRaw(MissionIcon),
			title: __("ماموریت‌های کاری"),
			route: "MissionsDashboard",
		},
		{
			icon: markRaw(EventIcon),
			title: __("رویدادها"),
			route: "EventsDashboard",
		},
		{
			icon: markRaw(EmployeeAdvanceIcon),
			title: __("درخواست مساعده"),
			route: "EmployeeAdvanceFormView",
		},
		{
			icon: markRaw(SalaryIcon),
			title: __("View Salary Slips"),
			route: "SalarySlipsDashboard",
		},
		{
			icon: markRaw(ComplaintIcon),
			title: __("Feedback & Suggestions"),
			route: "ComplaintsDashboard",
		},
		{
			icon: markRaw(MealIcon),
			title: __("Meal Program"),
			route: "MealsDashboard",
		},
		{
			icon: markRaw(AppraisalIcon),
			title: __("Performance Appraisal"),
			route: "AppraisalsDashboard",
		},
		{
			icon: markRaw(NewsletterIcon),
			title: __("Organization Newsletters"),
			route: "NewslettersDashboard",
			badge: layoutUnreadNewsletterCount.value,
		},
	]

	if (layoutHasImprestAccess.value) {
		links.splice(4, 0, {
			icon: markRaw(ImprestIcon),
			title: __("مدیریت تنخواه"),
			route: "ImprestDashboard",
		})
	}

	return links
})

const kpiCards = computed(() => [
	{
		title: __("درخواست‌های در انتظار"),
		value: toPersianDigits(pendingRequestsCount.value),
		caption: __("درخواست‌های نیازمند پیگیری شما"),
	},
	{
		title: __("درخواست‌های تایید شده"),
		value: toPersianDigits(approvedRequestsCount.value),
		caption: __("تعداد تاییدها در درخواست‌های اخیر"),
	},
	{
		title: __("مانده کل مرخصی"),
		value: toPersianDigits(totalLeaveBalance.value.toFixed(1).replace(/\.0$/, "")),
		caption: __("روز قابل استفاده"),
	},
	{
		title: __("ماموریت‌های فعال"),
		value: toPersianDigits(activeMissionCount.value),
		caption: __("ماموریت‌های در حال انجام یا برنامه‌ریزی‌شده"),
	},
	{
		title: __("امتیاز آخرین ارزیابی"),
		value: latestAppraisalScore.value,
		caption: __("آخرین نتیجه ثبت‌شده عملکرد"),
	},
])

const canSeeAllocatorShiftTools = computed(() => {
	return Boolean(employee.data?.is_shift_allocator)
})

const canSeeWeeklyShiftPlanner = computed(() => {
	return Boolean(
		employee.data?.variable_shift
		|| employee.data?.has_rotational_shift
		|| employee.data?.needs_shift_registration
		|| employee.data?.is_shift_allocator
	)
})

const menuGroups = computed(() => {
	return buildNavbarGroups(__, {
		unreadNewsletterCount: layoutUnreadNewsletterCount.value,
		hasImprestAccess: layoutHasImprestAccess.value,
		canSeeAllocatorShiftTools: canSeeAllocatorShiftTools.value,
		canSeeWeeklyShiftPlanner: canSeeWeeklyShiftPlanner.value,
	})
})

function isActive(path) {
	return route.path === path || route.path.startsWith(`${path}/`)
}

function handlePullToRefresh(event) {
	const complete = event?.detail?.complete || event?.target?.complete
	if (typeof complete === "function") {
		complete.call(event?.detail || event?.target)
	}

	setTimeout(() => {
		window.location.reload()
	}, 120)
}
</script>
