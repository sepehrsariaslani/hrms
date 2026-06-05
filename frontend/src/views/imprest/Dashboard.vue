<template>
	<BaseLayout :pageTitle="__('تنخواه')">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 pb-24 gap-4">
				<div v-if="!isImprestEnabled" class="bg-white rounded-xl p-4 text-sm text-gray-600">
					{{ __("برای شما حساب تنخواه تعریف نشده است.") }}
				</div>

				<template v-else>
					<div class="bg-white rounded-xl border border-gray-100 p-1 grid grid-cols-2 gap-1">
						<router-link
							:to="{ name: 'ImprestHome' }"
							class="text-center text-xs rounded-lg py-2"
							:class="activeTab === 'dashboard' ? 'bg-amber-500 text-white' : 'text-gray-600 bg-gray-50'"
						>
							{{ __("داشبورد") }}
						</router-link>
						<router-link
							:to="{ name: 'ImprestCalendarView', query: calendarQuery }"
							class="text-center text-xs rounded-lg py-2"
							:class="activeTab === 'calendar' ? 'bg-amber-500 text-white' : 'text-gray-600 bg-gray-50'"
						>
							{{ __("تقویم") }}
						</router-link>
					</div>

					<div class="bg-white rounded-xl p-4 border border-gray-100" data-tour="imprest-account-filter">
						<label class="text-xs text-gray-600 block mb-2">{{ __("حساب تنخواه") }}</label>
						<SearchableDropdown
							v-model="accountPickerValue"
							:options="accountOptions"
							:placeholder="__('افزودن حساب به فیلتر')"
							:include-empty-option="true"
							:empty-label="__('همه حساب‌های مجاز')"
						/>
						<div class="mt-2 flex flex-wrap gap-1.5">
							<button
								v-if="selectedAccounts.length"
								type="button"
								class="text-[11px] rounded-md px-2 py-1 bg-gray-100 text-gray-600"
								@click="clearAccountFilter"
							>
								{{ __("نمایش همه") }}
							</button>
							<div
								v-if="!selectedAccounts.length"
								class="text-[11px] rounded-md px-2 py-1 bg-emerald-50 text-emerald-700"
							>
								{{ __("همه حساب‌های مجاز فعال است") }}
							</div>
							<div
								v-for="account in selectedAccounts"
								:key="account"
								class="text-[11px] rounded-md px-2 py-1 bg-amber-50 text-amber-700 flex items-center gap-1"
							>
								<span>{{ getAccountLabel(account) }}</span>
								<button type="button" class="text-amber-900" @click="removeSelectedAccount(account)">×</button>
							</div>
						</div>
					</div>

					<div class="bg-white rounded-xl border border-gray-100 p-4" data-tour="imprest-date-filter">
						<div class="flex items-center justify-between gap-2">
							<div>
								<div class="text-xs text-gray-500">{{ __("بازه گزارش") }}</div>
								<div class="text-sm font-semibold text-gray-800 mt-1">{{ rangeLabel }}</div>
							</div>
							<button
								type="button"
								class="text-xs rounded-md px-3 py-1.5 bg-amber-50 text-amber-700"
								@click="toggleRangePicker"
							>
								{{ rangePickerOpen ? __("بستن") : __("انتخاب دوره") }}
							</button>
						</div>
						<div v-if="rangePickerOpen" class="mt-3 border border-gray-100 rounded-xl p-3">
							<div class="flex items-center justify-between mb-2">
								<button class="px-2 py-1 bg-gray-100 rounded-md text-xs" @click="navigateRangeMonth(-1)">‹</button>
								<div class="text-xs font-semibold text-gray-700">{{ pickerMonthTitle }}</div>
								<button class="px-2 py-1 bg-gray-100 rounded-md text-xs" @click="navigateRangeMonth(1)">›</button>
							</div>
							<div class="grid grid-cols-7 bg-gray-50 rounded-lg mb-1">
								<div v-for="day in weekLabels" :key="day" class="text-center py-1 text-[10px] text-gray-500">
									{{ day }}
								</div>
							</div>
							<div class="grid grid-cols-7 gap-1">
								<button
									v-for="cell in pickerMonthDays"
									:key="cell.key"
									type="button"
									class="h-9 rounded-lg text-[11px]"
									:class="getRangeCellClass(cell)"
									:disabled="!cell.isCurrentMonth"
									@click="selectRangeDate(cell)"
								>
									{{ cell.jalaliDay ? toPersianDigits(cell.jalaliDay) : '' }}
								</button>
							</div>
							<div class="mt-2 text-[11px] text-gray-500">
								{{ __("برای انتخاب یک روز، همان روز را دوبار انتخاب کنید.") }}
							</div>
						</div>
					</div>

					<div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
						<div class="bg-emerald-50 rounded-xl p-4 border border-emerald-100">
							<div class="text-xs text-emerald-700">{{ __("موجودی فعلی") }}</div>
							<div class="text-lg font-bold text-emerald-800 mt-1">
								{{ formatAmount(stats.current_balance) }}
							</div>
						</div>
						<div class="bg-blue-50 rounded-xl p-4 border border-blue-100">
							<div class="text-xs text-blue-700">{{ __("دریافتی دوره") }}</div>
							<div class="text-lg font-bold text-blue-800 mt-1">
								{{ formatAmount(stats.total_incoming) }}
							</div>
						</div>
						<div class="bg-rose-50 rounded-xl p-4 border border-rose-100">
							<div class="text-xs text-rose-700">{{ __("پرداختی دوره") }}</div>
							<div class="text-lg font-bold text-rose-800 mt-1">
								{{ formatAmount(stats.total_outgoing) }}
							</div>
						</div>
						<div class="bg-sky-50 rounded-xl p-4 border border-sky-100">
							<div class="text-xs text-sky-700">{{ __("انتقال داخلی دوره") }}</div>
							<div class="text-lg font-bold text-sky-800 mt-1">
								{{ formatAmount(stats.total_transfer) }}
							</div>
						</div>
						<div class="bg-amber-50 rounded-xl p-4 border border-amber-100">
							<div class="text-xs text-amber-700">{{ __("خالص ورود/خروج") }}</div>
							<div class="text-lg font-bold mt-1" :class="Number(stats.period_net || 0) >= 0 ? 'text-emerald-700' : 'text-rose-700'">
								{{ formatSignedAmount(stats.period_net, Number(stats.period_net || 0) >= 0 ? 'incoming' : 'outgoing') }}
							</div>
						</div>
					</div>

					<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
						<router-link :to="{ name: 'ImprestQuickEntryView' }" v-slot="{ navigate }">
							<Button class="w-full py-5 text-base !bg-amber-600 !text-white hover:!bg-amber-700" @click="navigate">
								{{ __("ثبت سریع تنخواه") }}
							</Button>
						</router-link>
						<router-link
							:to="{ name: 'ImprestCalendarView', query: calendarQuery }"
							v-slot="{ navigate }"
						>
							<Button class="w-full py-5 text-base !bg-blue-600 !text-white hover:!bg-blue-700" @click="navigate">
								{{ __("تقویم تنخواه") }}
							</Button>
						</router-link>
					</div>

					<div class="bg-white rounded-xl border border-gray-100 overflow-hidden" data-tour="imprest-transactions-board">
						<div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
							<div class="text-sm font-semibold text-gray-800">{{ __("داشبورد تراکنش‌ها") }}</div>
							<div class="text-xs text-gray-500">
								{{ toPersianDigits(recentTransactions.length) }} {{ __("مورد") }}
							</div>
						</div>
						<div class="grid grid-cols-3 gap-1 p-2 bg-gray-50 border-b border-gray-100">
							<button
								v-for="tab in transactionTabs"
								:key="tab.id"
								type="button"
								class="rounded-md py-2 text-[11px]"
								:class="insightTab === tab.id ? 'bg-white text-amber-700 border border-amber-200' : 'text-gray-600'"
								@click="insightTab = tab.id"
							>
								{{ tab.label }}
							</button>
						</div>

						<div v-if="insightTab === 'recent'">
							<div v-if="!recentTransactions.length" class="p-4 text-sm text-gray-500">
								{{ __("تراکنشی برای نمایش وجود ندارد.") }}
							</div>
							<div v-else class="divide-y divide-gray-100">
								<div v-for="tx in recentTransactions" :key="`${tx.doctype || 'Payment Entry'}:${tx.name}`">
									<router-link
										v-if="isEditableTransaction(tx)"
										:to="{
											name: 'ImprestQuickEntryEditView',
											params: { id: tx.name },
											query: { doctype: tx.doctype || 'Payment Entry' },
										}"
										class="flex items-center justify-between px-4 py-3"
									>
										<div>
											<div class="text-sm text-gray-800 font-medium">
												{{ tx.party_name || tx.party || tx.paid_to || tx.paid_from || __("بدون طرف حساب") }}
											</div>
											<div class="text-xs text-gray-500 mt-1">
												{{ formatJalaliDateShort(tx.posting_date) }} · {{ tx.name }} · {{ tx.doctype || 'Payment Entry' }}
											</div>
										</div>
										<div class="text-sm font-semibold" :class="getAmountClass(tx.transaction_type)">
											{{ formatSignedAmount(tx.amount, tx.transaction_type) }}
										</div>
									</router-link>
									<div v-else class="flex items-center justify-between px-4 py-3">
										<div>
											<div class="text-sm text-gray-800 font-medium">
												{{ tx.party_name || tx.party || tx.paid_to || tx.paid_from || __("بدون طرف حساب") }}
											</div>
											<div class="text-xs text-gray-500 mt-1">
												{{ formatJalaliDateShort(tx.posting_date) }} · {{ tx.name }} · {{ tx.doctype || 'Payment Entry' }}
											</div>
										</div>
										<div class="text-sm font-semibold" :class="getAmountClass(tx.transaction_type)">
											{{ formatSignedAmount(tx.amount, tx.transaction_type) }}
										</div>
									</div>
								</div>
							</div>
						</div>

						<div v-else-if="insightTab === 'expense'" class="p-4 space-y-3">
							<div class="bg-rose-50 border border-rose-100 rounded-xl p-3 text-sm text-rose-700">
								{{ expenseSummarySentence }}
							</div>
							<div v-if="!accountExpenseTotals.length" class="text-sm text-gray-500">
								{{ __("در بازه انتخابی هزینه پرداختی ثبت نشده است.") }}
							</div>
							<div v-else class="space-y-2">
								<div
									v-for="row in accountExpenseTotals"
									:key="row.account"
									class="rounded-lg border border-gray-100 p-3"
								>
									<div class="flex items-center justify-between gap-2">
										<div class="text-sm font-medium text-gray-800 truncate">{{ row.account_name || row.account }}</div>
										<div class="text-sm font-semibold text-rose-700">{{ formatAmount(row.amount) }}</div>
									</div>
								</div>
							</div>
						</div>

						<div v-else class="p-4 space-y-4" data-tour="imprest-charts-tab">
							<div class="rounded-xl border border-gray-100 p-3 bg-gray-50">
								<div class="text-xs text-gray-500">{{ __("مقایسه با دوره قبل") }}</div>
								<div class="mt-2 text-sm text-gray-700">
									{{ __("هزینه این دوره") }}:
									<span class="font-semibold text-rose-700">{{ formatAmount(totalOutgoing) }}</span>
								</div>
								<div class="mt-1 text-sm text-gray-700">
									{{ __("هزینه دوره قبل") }}:
									<span class="font-semibold text-gray-800">{{ formatAmount(previousOutgoing) }}</span>
								</div>
								<div class="mt-2 text-xs" :class="expenseGrowthPercent >= 0 ? 'text-rose-700' : 'text-emerald-700'">
									{{ expenseGrowthPercent >= 0 ? __('افزایش') : __('کاهش') }}
									{{ toPersianDigits(Math.abs(expenseGrowthPercent).toFixed(1)) }}%
								</div>
							</div>

							<div class="rounded-xl border border-gray-100 p-3">
								<div class="text-xs text-gray-500 mb-2">{{ __("سهم هزینه‌ها (Pie)") }}</div>
								<div class="flex items-center gap-3">
									<div class="w-28 h-28 rounded-full border border-gray-100" :style="{ background: pieGradient }"></div>
									<div class="flex-1 space-y-1">
										<div v-for="slice in categorySlices" :key="slice.label" class="flex items-center justify-between gap-2 text-xs">
											<div class="flex items-center gap-1 min-w-0">
												<span class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: slice.color }"></span>
												<span class="truncate text-gray-700">{{ slice.label }}</span>
											</div>
											<div class="text-gray-500">{{ toPersianDigits(slice.percent.toFixed(1)) }}%</div>
										</div>
									</div>
								</div>
							</div>

							<div class="rounded-xl border border-gray-100 p-3">
								<div class="text-xs text-gray-500 mb-2">{{ __("هزینه به تفکیک حساب تنخواه") }}</div>
								<div v-if="!accountExpenseTotals.length" class="text-xs text-gray-500">
									{{ __("داده‌ای برای نمایش نمودار موجود نیست.") }}
								</div>
								<div v-else class="space-y-2">
									<div v-for="row in accountBars" :key="`${row.account}-bar`">
										<div class="flex items-center justify-between text-[11px] mb-1">
											<span class="text-gray-700 truncate">{{ row.account_name || row.account }}</span>
											<span class="text-gray-500">{{ formatAmount(row.amount) }}</span>
										</div>
										<div class="h-2 rounded-full bg-gray-100 overflow-hidden">
											<div class="h-full bg-amber-500" :style="{ width: `${row.width}%` }"></div>
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				</template>

				<ErrorMessage :message="errorMessage" />
			</div>

			<div v-if="isImprestEnabled" class="fixed bottom-20 left-3 z-40" data-tour="imprest-quick-actions">
				<Transition name="scale">
					<div v-if="showQuickActions" class="absolute bottom-14 left-0 bg-white rounded-xl border border-gray-100 shadow p-2 w-44">
						<button class="w-full text-right p-2 rounded-lg hover:bg-gray-50 text-xs" @click="openQuickAction('pay')">
							{{ __('ثبت پرداخت') }}
						</button>
						<button class="w-full text-right p-2 rounded-lg hover:bg-gray-50 text-xs" @click="openQuickAction('receive')">
							{{ __('ثبت دریافت') }}
						</button>
						<button class="w-full text-right p-2 rounded-lg hover:bg-gray-50 text-xs" @click="openQuickAction('transfer')">
							{{ __('ثبت انتقال داخلی') }}
						</button>
					</div>
				</Transition>
				<button
					class="w-12 h-12 rounded-full shadow-lg bg-amber-500 text-white text-2xl leading-none"
					:class="showQuickActions ? 'rotate-45' : ''"
					@click="showQuickActions = !showQuickActions"
				>
					+
				</button>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue"
import { createResource, ErrorMessage } from "frappe-ui"
import { onIonViewWillEnter } from "@ionic/vue"
import { useRoute, useRouter } from "vue-router"

import BaseLayout from "@/components/BaseLayout.vue"
import SearchableDropdown from "@/components/SearchableDropdown.vue"
import dayjs from "@/utils/dayjs"
import { extractErrorMessage } from "@/data/imprest"
import {
	formatJalaliDateShort,
	gregorianToJalali,
	jalaliToGregorian,
	getJalaliDaysInMonth,
	toPersianDigits,
} from "@/utils/jalali"

const __ = inject("$translate")
const route = useRoute()
const router = useRouter()

const weekLabels = ["ش", "ی", "د", "س", "چ", "پ", "ج"]
const persianMonths = [
	"فروردین",
	"اردیبهشت",
	"خرداد",
	"تیر",
	"مرداد",
	"شهریور",
	"مهر",
	"آبان",
	"آذر",
	"دی",
	"بهمن",
	"اسفند",
]
const pieColors = ["#ef4444", "#f97316", "#0ea5e9", "#14b8a6", "#22c55e", "#8b5cf6"]

const selectedAccounts = ref([])
const accountPickerValue = ref("")
const errorMessage = ref("")
const insightTab = ref("recent")
const showQuickActions = ref(false)

const rangePickerOpen = ref(false)
const rangeMonthBase = ref(new Date())
const rangeSelectionStart = ref("")
const rangeSelectionEnd = ref("")
const appliedFromDate = ref("")
const appliedToDate = ref("")

initializeDefaultRange()

const contextResource = createResource({
	url: "hrms.api.imprest.get_imprest_context",
	auto: true,
	cache: "hrms:imprest_context",
	onSuccess() {
		selectedAccounts.value = parseRouteAccountFilters(route.query)
	},
	onError(error) {
		errorMessage.value = extractErrorMessage(error, __("خطا در بارگذاری اطلاعات تنخواه"))
	},
})

const dashboardResource = createResource({
	url: "hrms.api.imprest.get_imprest_dashboard_stats",
	auto: false,
})

const isImprestEnabled = computed(() => Boolean(contextResource.data?.has_imprest))
const allowedAccounts = computed(() => contextResource.data?.allowed_accounts || [])
const accountOptions = computed(() =>
	allowedAccounts.value.map((account) => ({
		label: account.account_name || account.account,
		value: account.account,
	}))
)
const stats = computed(() => dashboardResource.data || {})
const recentTransactions = computed(() => stats.value?.recent_transactions || [])
const activeTab = computed(() => (route.path.includes("/calendar") ? "calendar" : "dashboard"))
const accountLookup = computed(
	() =>
		new Map(
			allowedAccounts.value.map((account) => [
				account.account,
				account.account_name || account.account,
			])
		)
)
const calendarQuery = computed(() => {
	if (selectedAccounts.value.length === 1) {
		return { account: selectedAccounts.value[0] }
	}
	if (selectedAccounts.value.length > 1) {
		return { accounts: JSON.stringify(selectedAccounts.value) }
	}
	return {}
})
const transactionTabs = computed(() => [
	{ id: "recent", label: __("تراکنش‌های اخیر") },
	{ id: "expense", label: __("آمار هزینه‌ها") },
	{ id: "charts", label: __("داشبوردها و نمودارها") },
])
const accountExpenseTotals = computed(() => stats.value?.account_expense_totals || [])
const categoryTotals = computed(() => stats.value?.expense_category_totals || [])
const totalOutgoing = computed(() => Number(stats.value?.total_outgoing || 0))
const previousOutgoing = computed(() => Number(stats.value?.previous_outgoing_total || 0))
const expenseGrowthPercent = computed(() => {
	if (!previousOutgoing.value) {
		return totalOutgoing.value > 0 ? 100 : 0
	}
	return ((totalOutgoing.value - previousOutgoing.value) / previousOutgoing.value) * 100
})
const accountBars = computed(() => {
	const maxAmount = Math.max(...accountExpenseTotals.value.map((row) => Number(row.amount || 0)), 0)
	return accountExpenseTotals.value.map((row) => {
		const amount = Number(row.amount || 0)
		return {
			...row,
			amount,
			width: maxAmount > 0 ? Math.max((amount / maxAmount) * 100, 4) : 0,
		}
	})
})
const categorySlices = computed(() => {
	const total = Math.max(totalOutgoing.value, 1)
	return categoryTotals.value.slice(0, 6).map((row, index) => {
		const amount = Number(row.amount || 0)
		return {
			label: row.label || __("سایر"),
			amount,
			percent: (amount / total) * 100,
			color: pieColors[index % pieColors.length],
		}
	})
})
const pieGradient = computed(() => {
	if (!categorySlices.value.length || totalOutgoing.value <= 0) {
		return "conic-gradient(#e5e7eb 0 100%)"
	}
	let start = 0
	const ranges = categorySlices.value.map((slice) => {
		const end = start + slice.percent
		const segment = `${slice.color} ${start}% ${end}%`
		start = end
		return segment
	})
	if (start < 100) {
		ranges.push(`#e5e7eb ${start}% 100%`)
	}
	return `conic-gradient(${ranges.join(", ")})`
})
const expenseSummarySentence = computed(() => {
	if (!accountExpenseTotals.value.length) {
		return __("در بازه انتخابی، هزینه‌ای برای حساب‌های تنخواه شما ثبت نشده است.")
	}
	if (selectedAccounts.value.length === 1) {
		const account = selectedAccounts.value[0]
		return `از حساب ${getAccountLabel(account)} در این بازه ${formatAmount(totalOutgoing.value)} هزینه ثبت شده است.`
	}
	return `در بازه انتخابی مجموع هزینه پرداختی شما ${formatAmount(totalOutgoing.value)} است.`
})

const currentRangeJalali = computed(() =>
	gregorianToJalali(
		rangeMonthBase.value.getFullYear(),
		rangeMonthBase.value.getMonth() + 1,
		rangeMonthBase.value.getDate()
	)
)
const pickerMonthTitle = computed(
	() =>
		`${persianMonths[currentRangeJalali.value.month - 1]} ${toPersianDigits(currentRangeJalali.value.year)}`
)
const pickerMonthDays = computed(() => {
	const current = currentRangeJalali.value
	const monthStart = jalaliToGregorian(current.year, current.month, 1)
	const startDate = dayjs(
		`${monthStart.year}-${String(monthStart.month).padStart(2, "0")}-${String(monthStart.day).padStart(2, "0")}`
	)
	const daysInMonth = getJalaliDaysInMonth(current.year, current.month)
	const firstDayIndex = (startDate.day() + 1) % 7
	const cells = []

	for (let i = 0; i < firstDayIndex; i++) {
		cells.push({
			key: `empty-${i}`,
			dateStr: "",
			jalaliDay: "",
			isCurrentMonth: false,
		})
	}

	for (let day = 0; day < daysInMonth; day++) {
		const date = startDate.add(day, "day")
		cells.push({
			key: date.format("YYYY-MM-DD"),
			dateStr: date.format("YYYY-MM-DD"),
			jalaliDay: day + 1,
			isCurrentMonth: true,
		})
	}

	while (cells.length < 42) {
		cells.push({
			key: `tail-${cells.length}`,
			dateStr: "",
			jalaliDay: "",
			isCurrentMonth: false,
		})
	}

	return cells
})
const rangeLabel = computed(() => {
	if (!appliedFromDate.value || !appliedToDate.value) {
		return __("دوره نامشخص")
	}
	if (appliedFromDate.value === appliedToDate.value) {
		return formatJalaliDateShort(appliedFromDate.value)
	}
	return `${formatJalaliDateShort(appliedFromDate.value)} تا ${formatJalaliDateShort(appliedToDate.value)}`
})

watch(
	selectedAccounts,
	() => {
		if (isImprestEnabled.value) reloadStats()
	},
	{ deep: true }
)

watch(
	isImprestEnabled,
	(enabled) => {
		if (enabled) reloadStats()
	},
	{ immediate: true }
)

watch(accountPickerValue, (value) => {
	if (value === null || value === undefined) return
	const normalized = String(value).trim()
	if (!normalized) {
		clearAccountFilter()
		accountPickerValue.value = ""
		return
	}
	if (!selectedAccounts.value.includes(normalized)) {
		selectedAccounts.value = [...selectedAccounts.value, normalized]
	}
	accountPickerValue.value = ""
})

watch(
	() => route.query.account,
	() => {
		selectedAccounts.value = parseRouteAccountFilters(route.query)
	},
	{ immediate: true }
)

watch(
	() => route.query.accounts,
	() => {
		selectedAccounts.value = parseRouteAccountFilters(route.query)
	},
	{ immediate: true }
)

function initializeDefaultRange() {
	const today = dayjs()
	const monthStart = today.startOf("month")
	appliedFromDate.value = monthStart.format("YYYY-MM-DD")
	appliedToDate.value = today.format("YYYY-MM-DD")
	rangeSelectionStart.value = appliedFromDate.value
	rangeSelectionEnd.value = appliedToDate.value
	rangeMonthBase.value = monthStart.toDate()
}

function toggleRangePicker() {
	rangePickerOpen.value = !rangePickerOpen.value
	if (rangePickerOpen.value) {
		rangeSelectionStart.value = appliedFromDate.value
		rangeSelectionEnd.value = appliedToDate.value
		const start = dayjs(appliedFromDate.value || dayjs())
		rangeMonthBase.value = start.isValid() ? start.toDate() : new Date()
	}
}

function navigateRangeMonth(direction) {
	rangeMonthBase.value = dayjs(rangeMonthBase.value).add(direction, "month").toDate()
}

function getRangeCellClass(cell) {
	if (!cell.isCurrentMonth) return "bg-gray-50 text-gray-300"
	const isStart = cell.dateStr === rangeSelectionStart.value
	const isEnd = cell.dateStr === rangeSelectionEnd.value
	const inRange = isDateInRange(cell.dateStr)
	if (isStart || isEnd) return "bg-amber-500 text-white"
	if (inRange) return "bg-amber-100 text-amber-700"
	return "bg-gray-50 text-gray-700 hover:bg-amber-50"
}

function selectRangeDate(cell) {
	if (!cell?.isCurrentMonth || !cell.dateStr) return

	if (!rangeSelectionStart.value || (rangeSelectionStart.value && rangeSelectionEnd.value)) {
		rangeSelectionStart.value = cell.dateStr
		rangeSelectionEnd.value = ""
		return
	}

	if (cell.dateStr < rangeSelectionStart.value) {
		rangeSelectionEnd.value = rangeSelectionStart.value
		rangeSelectionStart.value = cell.dateStr
	} else {
		rangeSelectionEnd.value = cell.dateStr
	}

	applyRangeFilter()
}

function isDateInRange(dateStr) {
	if (!dateStr || !rangeSelectionStart.value || !rangeSelectionEnd.value) return false
	const start = rangeSelectionStart.value <= rangeSelectionEnd.value ? rangeSelectionStart.value : rangeSelectionEnd.value
	const end = rangeSelectionStart.value <= rangeSelectionEnd.value ? rangeSelectionEnd.value : rangeSelectionStart.value
	return dateStr > start && dateStr < end
}

function applyRangeFilter() {
	if (!rangeSelectionStart.value || !rangeSelectionEnd.value) return
	if (rangeSelectionStart.value <= rangeSelectionEnd.value) {
		appliedFromDate.value = rangeSelectionStart.value
		appliedToDate.value = rangeSelectionEnd.value
	} else {
		appliedFromDate.value = rangeSelectionEnd.value
		appliedToDate.value = rangeSelectionStart.value
	}
	rangePickerOpen.value = false
	reloadStats()
}

function reloadStats() {
	if (!isImprestEnabled.value) return
	errorMessage.value = ""
	const payload = {
		from_date: appliedFromDate.value,
		to_date: appliedToDate.value,
	}
	if (selectedAccounts.value.length === 1) {
		payload.account = selectedAccounts.value[0]
	}
	if (selectedAccounts.value.length > 1) {
		payload.accounts = JSON.stringify(selectedAccounts.value)
	}
	dashboardResource.fetch(payload, {
		onError(error) {
			errorMessage.value = extractErrorMessage(error, __("خطا در دریافت داشبورد تنخواه"))
		},
	})
}

function formatAmount(value) {
	return toPersianDigits(new Intl.NumberFormat("en-US").format(Math.round(Number(value || 0))))
}

function formatSignedAmount(amount, type) {
	const prefix = type === "outgoing" ? "-" : type === "incoming" ? "+" : ""
	return `${prefix}${formatAmount(amount)}`
}

function getAmountClass(type) {
	if (type === "incoming") return "text-emerald-600"
	if (type === "outgoing") return "text-rose-600"
	return "text-blue-600"
}

function isEditableTransaction(tx) {
	if (!tx?.can_edit) return false
	if (tx.doctype === "Journal Entry") return true
	return ["Pay", "Receive", "Internal Transfer"].includes(tx.payment_type)
}

function getAccountLabel(account) {
	return accountLookup.value.get(account) || account
}

function removeSelectedAccount(account) {
	selectedAccounts.value = selectedAccounts.value.filter((entry) => entry !== account)
}

function clearAccountFilter() {
	selectedAccounts.value = []
}

function parseRouteAccountFilters(query) {
	const available = new Set(allowedAccounts.value.map((row) => row.account))
	const hasAvailableAccounts = available.size > 0
	const result = []

	if (query?.accounts) {
		try {
			const parsed = JSON.parse(String(query.accounts))
			if (Array.isArray(parsed)) {
				for (const account of parsed) {
					const normalized = String(account || "").trim()
					const isAllowed = hasAvailableAccounts ? available.has(normalized) : true
					if (normalized && isAllowed && !result.includes(normalized)) {
						result.push(normalized)
					}
				}
			}
		} catch (_) {
			// ignore invalid query and fallback to single account mode
		}
	}

	if (!result.length && query?.account) {
		const single = String(query.account).trim()
		const isAllowed = hasAvailableAccounts ? available.has(single) : true
		if (single && isAllowed) {
			result.push(single)
		}
	}

	return result
}

function openQuickAction(type) {
	showQuickActions.value = false
	const query = {
		type,
		date: appliedToDate.value || dayjs().format("YYYY-MM-DD"),
	}
	if (selectedAccounts.value.length === 1) {
		query.account = selectedAccounts.value[0]
	} else if (selectedAccounts.value.length > 1) {
		query.accounts = JSON.stringify(selectedAccounts.value)
	}
	router.push({
		name: "ImprestQuickEntryView",
		query,
	})
}

onIonViewWillEnter(() => {
	if (typeof contextResource.reload === "function") {
		contextResource.reload()
	} else {
		contextResource.fetch()
	}
	if (isImprestEnabled.value) reloadStats()
})
</script>

<style scoped>
.scale-enter-active,
.scale-leave-active {
	transition: all 0.2s ease;
}

.scale-enter-from,
.scale-leave-to {
	opacity: 0;
	transform: scale(0.92);
}
</style>
