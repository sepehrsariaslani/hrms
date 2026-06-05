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

						<main class="flex flex-1 flex-col gap-6 p-4 md:p-6">
							<div v-if="canCustomizeEmployeeDeskGlobal" class="flex flex-wrap items-center justify-end gap-2">
								<Button
									variant="outline"
									class="!rounded-xl"
									@click="toggleHomeEditMode"
								>
									{{ homeEditMode ? __("پایان ویرایش") : __("ویرایش صفحه اصلی") }}
								</Button>
								<Button
									v-if="homeEditMode"
									variant="ghost"
									class="!rounded-xl"
									@click="restoreHomeBlocks"
								>
									{{ __("بازنشانی") }}
								</Button>
							</div>

							<section
								v-if="isSectionVisible('enable_home_check_in_panel') || (isSectionVisible('enable_home_kpi_section') && kpiCards.length)"
								class="grid gap-4 xl:grid-cols-12"
								:style="getHomeGroupStyle(['enable_home_check_in_panel', 'enable_home_kpi_section'])"
							>
								<div
									v-if="isSectionVisible('enable_home_check_in_panel')"
									class="xl:col-span-6"
									:style="getHomeSectionStyle('enable_home_check_in_panel')"
								>
									<div v-if="homeEditMode" class="mb-2 flex items-center justify-end gap-1">
										<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeSection('enable_home_check_in_panel', -1)">↑</Button>
										<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeSection('enable_home_check_in_panel', 1)">↓</Button>
										<Button
											size="sm"
											:variant="isHomeSectionHidden('enable_home_check_in_panel') ? 'outline' : 'ghost'"
											class="!rounded-lg"
											@click="toggleHomeSection('enable_home_check_in_panel')"
										>
											{{ isHomeSectionHidden('enable_home_check_in_panel') ? __("نمایش") : __("مخفی") }}
										</Button>
									</div>
									<CheckInPanel />
								</div>
								<div
									v-if="isSectionVisible('enable_home_kpi_section') && kpiCards.length"
									class="grid gap-4 sm:grid-cols-2 xl:col-span-6"
									:style="getHomeSectionStyle('enable_home_kpi_section')"
								>
									<div v-if="homeEditMode" class="sm:col-span-2 mb-1 flex items-center justify-end gap-1">
										<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeSection('enable_home_kpi_section', -1)">↑</Button>
										<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeSection('enable_home_kpi_section', 1)">↓</Button>
										<Button
											size="sm"
											:variant="isHomeSectionHidden('enable_home_kpi_section') ? 'outline' : 'ghost'"
											class="!rounded-lg"
											@click="toggleHomeSection('enable_home_kpi_section')"
										>
											{{ isHomeSectionHidden('enable_home_kpi_section') ? __("نمایش") : __("مخفی") }}
										</Button>
									</div>
									<div
										v-for="card in kpiCards"
										:key="card.key"
										class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition"
										:class="homeEditMode && card.hidden ? 'opacity-50 saturate-50' : ''"
									>
										<div v-if="homeEditMode" class="mb-2 flex items-center justify-end gap-1">
											<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeKpi(card.key, -1)">↑</Button>
											<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeKpi(card.key, 1)">↓</Button>
											<Button
												size="sm"
												:variant="isHomeKpiHidden(card.key) ? 'outline' : 'ghost'"
												class="!rounded-lg"
												@click="toggleHomeKpi(card.key)"
											>
												{{ isHomeKpiHidden(card.key) ? __("نمایش") : __("مخفی") }}
											</Button>
										</div>
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

							<section
								v-if="isSectionVisible('enable_home_activity_section') || isSectionVisible('enable_home_expense_section')"
								class="grid gap-4 xl:grid-cols-3"
								:style="getHomeGroupStyle(['enable_home_activity_section', 'enable_home_expense_section'])"
							>
								<div
									v-if="isSectionVisible('enable_home_activity_section')"
									class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm xl:col-span-2"
									:style="getHomeSectionStyle('enable_home_activity_section')"
								>
									<div class="mb-4 flex items-center justify-between">
										<h3 class="text-sm font-bold text-slate-800">{{ __("روند فعالیت ۶ ماه اخیر") }}</h3>
										<div class="flex items-center gap-2">
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
											<div v-if="homeEditMode" class="flex items-center gap-1">
												<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeSection('enable_home_activity_section', -1)">↑</Button>
												<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeSection('enable_home_activity_section', 1)">↓</Button>
												<Button
													size="sm"
													:variant="isHomeSectionHidden('enable_home_activity_section') ? 'outline' : 'ghost'"
													class="!rounded-lg"
													@click="toggleHomeSection('enable_home_activity_section')"
												>
													{{ isHomeSectionHidden('enable_home_activity_section') ? __("نمایش") : __("مخفی") }}
												</Button>
											</div>
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

								<div
									v-if="isSectionVisible('enable_home_expense_section')"
									class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
									:style="getHomeSectionStyle('enable_home_expense_section')"
								>
									<div class="mb-2 flex items-center justify-between">
										<h3 class="text-sm font-bold text-slate-800">{{ __("وضعیت هزینه‌ها") }}</h3>
										<div v-if="homeEditMode" class="flex items-center gap-1">
											<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeSection('enable_home_expense_section', -1)">↑</Button>
											<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeSection('enable_home_expense_section', 1)">↓</Button>
											<Button
												size="sm"
												:variant="isHomeSectionHidden('enable_home_expense_section') ? 'outline' : 'ghost'"
												class="!rounded-lg"
												@click="toggleHomeSection('enable_home_expense_section')"
											>
												{{ isHomeSectionHidden('enable_home_expense_section') ? __("نمایش") : __("مخفی") }}
											</Button>
										</div>
									</div>
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

							<section
								v-if="isSectionVisible('enable_home_leave_balance_section') || isSectionVisible('enable_home_quick_links_section')"
								class="grid gap-4 xl:grid-cols-3"
								:style="getHomeGroupStyle(['enable_home_leave_balance_section', 'enable_home_quick_links_section'])"
							>
								<div
									v-if="isSectionVisible('enable_home_leave_balance_section')"
									class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm xl:col-span-2"
									:style="getHomeSectionStyle('enable_home_leave_balance_section')"
								>
									<div class="mb-4 flex items-center justify-between">
										<h3 class="text-sm font-bold text-slate-800">{{ __("نمودار مانده مرخصی") }}</h3>
										<div v-if="homeEditMode" class="flex items-center gap-1">
											<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeSection('enable_home_leave_balance_section', -1)">↑</Button>
											<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeSection('enable_home_leave_balance_section', 1)">↓</Button>
											<Button
												size="sm"
												:variant="isHomeSectionHidden('enable_home_leave_balance_section') ? 'outline' : 'ghost'"
												class="!rounded-lg"
												@click="toggleHomeSection('enable_home_leave_balance_section')"
											>
												{{ isHomeSectionHidden('enable_home_leave_balance_section') ? __("نمایش") : __("مخفی") }}
											</Button>
										</div>
									</div>
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

								<div
									v-if="isSectionVisible('enable_home_quick_links_section')"
									class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
									:style="getHomeSectionStyle('enable_home_quick_links_section')"
								>
									<div class="mb-4 flex items-center justify-between">
										<h3 class="text-sm font-bold text-slate-800">{{ __("میانبرهای سریع") }}</h3>
										<div v-if="homeEditMode" class="flex items-center gap-1">
											<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeSection('enable_home_quick_links_section', -1)">↑</Button>
											<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeSection('enable_home_quick_links_section', 1)">↓</Button>
											<Button
												size="sm"
												:variant="isHomeSectionHidden('enable_home_quick_links_section') ? 'outline' : 'ghost'"
												class="!rounded-lg"
												@click="toggleHomeSection('enable_home_quick_links_section')"
											>
												{{ isHomeSectionHidden('enable_home_quick_links_section') ? __("نمایش") : __("مخفی") }}
											</Button>
										</div>
									</div>
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

							<section
								v-if="isSectionVisible('enable_home_recent_requests_section')"
								class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
								:style="getHomeSectionStyle('enable_home_recent_requests_section')"
							>
								<div class="mb-4 flex items-center justify-between">
									<h3 class="text-sm font-bold text-slate-800">{{ __("درخواست‌های اخیر") }}</h3>
									<div v-if="homeEditMode" class="flex items-center gap-1">
										<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeSection('enable_home_recent_requests_section', -1)">↑</Button>
										<Button size="sm" variant="ghost" class="!rounded-lg" @click="moveHomeSection('enable_home_recent_requests_section', 1)">↓</Button>
										<Button
											size="sm"
											:variant="isHomeSectionHidden('enable_home_recent_requests_section') ? 'outline' : 'ghost'"
											class="!rounded-lg"
											@click="toggleHomeSection('enable_home_recent_requests_section')"
										>
											{{ isHomeSectionHidden('enable_home_recent_requests_section') ? __("نمایش") : __("مخفی") }}
										</Button>
									</div>
								</div>
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
import { employeeDeskVisibility, layoutHasImprestAccess, layoutUnreadNewsletterCount } from "@/data/layout"
import { buildNavbarGroups } from "@/data/navigation"
import {
	canCustomizeEmployeeDeskGlobal,
	employeeDeskGlobalPersonalization,
	saveEmployeeDeskGlobalPersonalization,
} from "@/data/personalization"
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
const homeEditMode = ref(false)

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
const visibilityMap = computed(() => employeeDeskVisibility.data || {})
const personalPreferences = computed(() => employeeDeskGlobalPersonalization.data?.preferences || {})
const hiddenHomeSections = computed(() => new Set(personalPreferences.value.home_hidden_sections || []))
const hiddenHomeKpis = computed(() => new Set(personalPreferences.value.home_hidden_kpis || []))
const HOME_SECTION_KEYS = [
	"enable_home_check_in_panel",
	"enable_home_kpi_section",
	"enable_home_activity_section",
	"enable_home_expense_section",
	"enable_home_leave_balance_section",
	"enable_home_quick_links_section",
	"enable_home_recent_requests_section",
]
const HOME_KPI_KEYS = [
	"enable_kpi_pending_requests",
	"enable_kpi_approved_requests",
	"enable_kpi_leave_balance",
	"enable_kpi_active_missions",
	"enable_kpi_latest_appraisal",
]

function buildOrderedKeys(validKeys, savedKeys = []) {
	const validSet = new Set(validKeys)
	const ordered = []
	const seen = new Set()
	for (const key of [...(savedKeys || []), ...validKeys]) {
		if (!validSet.has(key) || seen.has(key)) continue
		seen.add(key)
		ordered.push(key)
	}
	return ordered
}

const orderedHomeSectionKeys = computed(() =>
	buildOrderedKeys(HOME_SECTION_KEYS, personalPreferences.value.home_section_order_keys || [])
)

const homeSectionOrderMap = computed(
	() => new Map(orderedHomeSectionKeys.value.map((key, index) => [key, index]))
)

const orderedHomeKpiKeys = computed(() =>
	buildOrderedKeys(HOME_KPI_KEYS, personalPreferences.value.kpi_order_keys || [])
)

const homeKpiOrderMap = computed(
	() => new Map(orderedHomeKpiKeys.value.map((key, index) => [key, index]))
)

function isVisible(key) {
	return visibilityMap.value?.[key] !== false
}

function isSectionVisible(key) {
	if (!isVisible(key)) return false
	if (homeEditMode.value) return true
	return !isHomeSectionHidden(key)
}

function isHomeSectionHidden(key) {
	return hiddenHomeSections.value.has(key)
}

function isHomeKpiHidden(key) {
	return hiddenHomeKpis.value.has(key)
}

function getSectionOrder(key) {
	if (homeSectionOrderMap.value.has(key)) {
		return homeSectionOrderMap.value.get(key)
	}
	return Number.MAX_SAFE_INTEGER
}

function getHomeSectionStyle(key) {
	const sectionStyle = {
		order: getSectionOrder(key),
	}
	if (homeEditMode.value && isHomeSectionHidden(key)) {
		sectionStyle.opacity = 0.45
		sectionStyle.filter = "grayscale(40%)"
	}
	return sectionStyle
}

function getHomeGroupStyle(keys = []) {
	const orders = keys.map((key) => getSectionOrder(key))
	return {
		order: Math.min(...orders, Number.MAX_SAFE_INTEGER),
	}
}

function toggleHomeSection(key) {
	if (!canCustomizeEmployeeDeskGlobal.value) return
	const current = new Set(personalPreferences.value.home_hidden_sections || [])
	if (current.has(key)) current.delete(key)
	else current.add(key)
	void saveEmployeeDeskGlobalPersonalization({
		...personalPreferences.value,
		home_hidden_sections: [...current],
	})
}

function toggleHomeKpi(key) {
	if (!canCustomizeEmployeeDeskGlobal.value) return
	const current = new Set(personalPreferences.value.home_hidden_kpis || [])
	if (current.has(key)) current.delete(key)
	else current.add(key)
	void saveEmployeeDeskGlobalPersonalization({
		...personalPreferences.value,
		home_hidden_kpis: [...current],
	})
}

function moveHomeSection(key, direction) {
	if (!canCustomizeEmployeeDeskGlobal.value) return
	const ordered = [...orderedHomeSectionKeys.value]
	const index = ordered.indexOf(key)
	if (index < 0) return
	const targetIndex = index + direction
	if (targetIndex < 0 || targetIndex >= ordered.length) return
	const [moved] = ordered.splice(index, 1)
	ordered.splice(targetIndex, 0, moved)
	void saveEmployeeDeskGlobalPersonalization({
		...personalPreferences.value,
		home_section_order_keys: ordered,
	})
}

function moveHomeKpi(key, direction) {
	if (!canCustomizeEmployeeDeskGlobal.value) return
	const ordered = [...orderedHomeKpiKeys.value]
	const index = ordered.indexOf(key)
	if (index < 0) return
	const targetIndex = index + direction
	if (targetIndex < 0 || targetIndex >= ordered.length) return
	const [moved] = ordered.splice(index, 1)
	ordered.splice(targetIndex, 0, moved)
	void saveEmployeeDeskGlobalPersonalization({
		...personalPreferences.value,
		kpi_order_keys: ordered,
	})
}

function toggleHomeEditMode() {
	homeEditMode.value = !homeEditMode.value
}

function restoreHomeBlocks() {
	if (!canCustomizeEmployeeDeskGlobal.value) return
	void saveEmployeeDeskGlobalPersonalization({
		...personalPreferences.value,
		home_hidden_sections: [],
		home_hidden_kpis: [],
		home_section_order_keys: [],
		kpi_order_keys: [],
	})
}

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
			visibilityKey: "enable_requests_center",
			icon: markRaw(AttendanceIcon),
			title: __("مرکز درخواست‌ها"),
			route: "RequestsDashboard",
			badge: pendingRequestsCount.value,
		},
		{
			visibilityKey: "enable_attendance",
			icon: markRaw(AttendanceIcon),
			title: __("Request Attendance"),
			route: "AttendanceRequestFormView",
		},
		{
			visibilityKey: "enable_leaves",
			icon: markRaw(LeaveIcon),
			title: __("Request Leave"),
			route: "LeaveApplicationFormView",
		},
		{
			visibilityKey: "enable_expense_claims",
			icon: markRaw(ExpenseIcon),
			title: __("Claim an Expense"),
			route: "ExpenseClaimFormView",
		},
		{
			visibilityKey: "enable_missions",
			icon: markRaw(MissionIcon),
			title: __("ماموریت‌های کاری"),
			route: "MissionsDashboard",
		},
		{
			visibilityKey: "enable_events",
			icon: markRaw(EventIcon),
			title: __("رویدادها"),
			route: "EventsDashboard",
		},
		{
			visibilityKey: "enable_employee_advances",
			icon: markRaw(EmployeeAdvanceIcon),
			title: __("درخواست مساعده"),
			route: "EmployeeAdvanceFormView",
		},
		{
			visibilityKey: "enable_salary_slips",
			icon: markRaw(SalaryIcon),
			title: __("View Salary Slips"),
			route: "SalarySlipsDashboard",
		},
		{
			visibilityKey: "enable_complaints",
			icon: markRaw(ComplaintIcon),
			title: __("Feedback & Suggestions"),
			route: "ComplaintsDashboard",
		},
		{
			visibilityKey: "enable_meals",
			icon: markRaw(MealIcon),
			title: __("Meal Program"),
			route: "MealsDashboard",
		},
		{
			visibilityKey: "enable_appraisals",
			icon: markRaw(AppraisalIcon),
			title: __("Performance Appraisal"),
			route: "AppraisalsDashboard",
		},
		{
			visibilityKey: "enable_newsletters",
			icon: markRaw(NewsletterIcon),
			title: __("Organization Newsletters"),
			route: "NewslettersDashboard",
			badge: layoutUnreadNewsletterCount.value,
		},
	]

	if (layoutHasImprestAccess.value && isVisible("enable_imprest")) {
		links.splice(4, 0, {
			visibilityKey: "enable_imprest",
			icon: markRaw(ImprestIcon),
			title: __("مدیریت تنخواه"),
			route: "ImprestDashboard",
		})
	}

	return links.filter((link) => isVisible(link.visibilityKey))
})

const kpiCards = computed(() =>
	[
		{
			key: "enable_kpi_pending_requests",
			title: __("درخواست‌های در انتظار"),
			value: toPersianDigits(pendingRequestsCount.value),
			caption: __("درخواست‌های نیازمند پیگیری شما"),
		},
		{
			key: "enable_kpi_approved_requests",
			title: __("درخواست‌های تایید شده"),
			value: toPersianDigits(approvedRequestsCount.value),
			caption: __("تعداد تاییدها در درخواست‌های اخیر"),
		},
		{
			key: "enable_kpi_leave_balance",
			title: __("مانده کل مرخصی"),
			value: toPersianDigits(totalLeaveBalance.value.toFixed(1).replace(/\.0$/, "")),
			caption: __("روز قابل استفاده"),
		},
		{
			key: "enable_kpi_active_missions",
			title: __("ماموریت‌های فعال"),
			value: toPersianDigits(activeMissionCount.value),
			caption: __("ماموریت‌های در حال انجام یا برنامه‌ریزی‌شده"),
		},
		{
			key: "enable_kpi_latest_appraisal",
			title: __("امتیاز آخرین ارزیابی"),
			value: latestAppraisalScore.value,
			caption: __("آخرین نتیجه ثبت‌شده عملکرد"),
		},
	]
		.filter((card) => isVisible(card.key))
		.map((card) => ({
			...card,
			hidden: isHomeKpiHidden(card.key),
		}))
		.filter((card) => homeEditMode.value || !card.hidden)
		.sort((left, right) => {
			const leftOrder = homeKpiOrderMap.value.has(left.key)
				? homeKpiOrderMap.value.get(left.key)
				: Number.MAX_SAFE_INTEGER
			const rightOrder = homeKpiOrderMap.value.has(right.key)
				? homeKpiOrderMap.value.get(right.key)
				: Number.MAX_SAFE_INTEGER
			if (leftOrder !== rightOrder) return leftOrder - rightOrder
			return 0
		})
)

const canSeeAllocatorShiftTools = computed(() => {
	return Boolean(employee.data?.is_shift_allocator || employee.data?.is_shift_allocator_by_role)
})

const canSeeWeeklyShiftPlanner = computed(() => {
	return Boolean(
		employee.data?.variable_shift
		|| employee.data?.has_rotational_shift
		|| employee.data?.needs_shift_registration
	)
})

const menuGroups = computed(() => {
	return buildNavbarGroups(__, {
		unreadNewsletterCount: layoutUnreadNewsletterCount.value,
		hasImprestAccess: layoutHasImprestAccess.value,
		canSeeAllocatorShiftTools: canSeeAllocatorShiftTools.value,
		canSeeWeeklyShiftPlanner: canSeeWeeklyShiftPlanner.value,
		visibility: visibilityMap.value,
		hiddenRoutes: personalPreferences.value.hidden_sidebar_routes || [],
		routeOrder: personalPreferences.value.sidebar_order_routes || [],
		customLabels: personalPreferences.value.sidebar_labels || {},
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
