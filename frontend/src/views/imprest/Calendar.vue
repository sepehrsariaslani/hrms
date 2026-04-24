<template>
	<BaseLayout :pageTitle="__('تقویم تنخواه')">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 px-3 pb-24 gap-3">
				<div v-if="!isImprestEnabled" class="bg-white rounded-xl p-4 text-sm text-gray-600">
					{{ __("برای شما حساب تنخواه تعریف نشده است.") }}
				</div>

				<template v-else>
					<div class="bg-white rounded-xl border border-gray-100 p-1 grid grid-cols-2 gap-1">
						<router-link
							:to="{ name: 'ImprestHome' }"
							class="text-center text-xs rounded-lg py-2 text-gray-600 bg-gray-50"
						>
							{{ __("داشبورد") }}
						</router-link>
						<router-link
							:to="{ name: 'ImprestCalendarView', query: calendarQuery }"
							class="text-center text-xs rounded-lg py-2 bg-amber-500 text-white"
						>
							{{ __("تقویم") }}
						</router-link>
					</div>

					<div class="bg-gradient-to-l from-amber-600 to-orange-600 rounded-xl p-3 text-white">
						<div class="flex items-center justify-between mb-2">
							<button class="px-2 py-1 bg-white/20 rounded-md" @click="navigatePrev">{{ "‹" }}</button>
							<div class="text-center flex-1">
								<div class="text-sm font-bold">{{ currentTitle }}</div>
								<div class="flex items-center justify-center gap-1 mt-1">
									<button class="text-[10px] px-2 py-0.5 rounded bg-white/25" @click="goToToday">
										{{ __("امروز") }}
									</button>
									<button class="text-[10px] px-2 py-0.5 rounded bg-white/25" @click="loadTransactions">
										{{ __("بروزرسانی") }}
									</button>
								</div>
							</div>
							<button class="px-2 py-1 bg-white/20 rounded-md" @click="navigateNext">{{ "›" }}</button>
						</div>

						<div class="grid grid-cols-3 gap-1 bg-white/15 rounded-lg p-1 mb-2">
							<button
								v-for="mode in viewModes"
								:key="mode.id"
								class="text-[11px] rounded-md py-1"
								:class="viewMode === mode.id ? 'bg-white text-amber-700 font-semibold' : 'text-white'"
								@click="viewMode = mode.id"
							>
								{{ mode.label }}
							</button>
						</div>

						<div class="flex gap-1 overflow-x-auto pb-1" v-if="viewMode !== 'weekly'">
							<button
								v-for="(month, index) in persianMonths"
								:key="index"
								class="px-2 py-1 rounded-md text-[10px] whitespace-nowrap"
								:class="currentJalaliMonth === index ? 'bg-white text-amber-700' : 'bg-white/20 text-white'"
								@click="selectMonth(index)"
							>
								{{ month }}
							</button>
						</div>
					</div>

					<div class="bg-white rounded-xl border border-gray-100 p-3">
						<label class="block text-xs text-gray-500 mb-1">{{ __("حساب تنخواه") }}</label>
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

					<div
						v-if="viewMode === 'monthly'"
						class="bg-white rounded-xl border border-gray-100 overflow-hidden"
					>
						<div class="grid grid-cols-7 bg-gray-50 text-[10px] text-gray-500">
							<div v-for="day in weekLabels" :key="day" class="text-center py-1.5">{{ day }}</div>
						</div>
						<div class="grid grid-cols-7">
							<button
								v-for="cell in monthGridDays"
								:key="cell.key"
								class="min-h-[58px] border-b border-l border-gray-100 first:border-l-0 p-1 text-right"
								:class="[
									cell.isCurrentMonth ? 'hover:bg-amber-50' : 'bg-gray-50 text-gray-300',
									selectedDate === cell.dateStr ? 'bg-amber-50 ring-1 ring-inset ring-amber-400' : '',
								]"
								:disabled="!cell.isCurrentMonth"
								@click="selectDate(cell)"
							>
								<div class="text-[10px] font-semibold" :class="cell.isToday ? 'text-amber-700' : ''">
									{{ toPersianDigits(cell.jalaliDay) }}
								</div>
								<div v-if="cell.hasTransactions" class="mt-1 space-y-0.5">
									<div class="flex h-1 rounded-sm overflow-hidden">
										<div v-if="cell.incoming > 0" class="bg-emerald-500" :style="{ width: getPercent(cell.incoming, cell.total) + '%' }" />
										<div v-if="cell.outgoing > 0" class="bg-rose-500" :style="{ width: getPercent(cell.outgoing, cell.total) + '%' }" />
										<div v-if="cell.transfer > 0" class="bg-blue-500" :style="{ width: getPercent(cell.transfer, cell.total) + '%' }" />
									</div>
									<div class="flex justify-between text-[8px]">
										<span v-if="cell.incoming > 0" class="text-emerald-600">+{{ formatCompact(cell.incoming) }}</span>
										<span v-if="cell.outgoing > 0" class="text-rose-600">-{{ formatCompact(cell.outgoing) }}</span>
										<span v-if="cell.transfer > 0" class="text-blue-600">~{{ formatCompact(cell.transfer) }}</span>
									</div>
								</div>
							</button>
						</div>
					</div>

					<div
						v-else-if="viewMode === 'weekly'"
						class="bg-white rounded-xl border border-gray-100 p-2"
					>
						<div class="grid grid-cols-7 gap-1">
							<button
								v-for="day in weekDaysGrid"
								:key="day.dateStr"
								class="rounded-lg p-1.5 text-center"
								:class="selectedDate === day.dateStr ? 'bg-amber-100 text-amber-700' : day.isToday ? 'bg-amber-50 ring-1 ring-amber-400' : 'bg-gray-50'"
								@click="selectDate(day)"
							>
								<div class="text-[9px] text-gray-500">{{ weekLabels[(day.dayOfWeek + 1) % 7] }}</div>
								<div class="text-sm font-bold">{{ toPersianDigits(day.jalaliDay) }}</div>
								<div v-if="day.hasTransactions" class="text-[8px] mt-1">{{ formatCompact(day.total) }}</div>
							</button>
						</div>
					</div>

					<div v-else class="bg-white rounded-xl border border-gray-100 p-2 overflow-x-auto">
						<div class="flex gap-1.5">
							<button
								v-for="day in calendarDays"
								:key="day.dateStr"
								class="w-12 flex-shrink-0 rounded-xl py-2 text-center"
								:class="selectedDate === day.dateStr ? 'bg-amber-500 text-white' : day.isToday ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-700'"
								@click="selectDate(day)"
							>
								<div class="text-[9px]">{{ weekLabels[(day.dayOfWeek + 1) % 7] }}</div>
								<div class="text-sm font-bold">{{ toPersianDigits(day.jalaliDay) }}</div>
							</button>
						</div>
					</div>

					<div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
						<div class="flex">
							<button
								v-for="tab in tabs"
								:key="tab.id"
								class="flex-1 py-2 text-[11px] border-b-2"
								:class="activeTab === tab.id ? 'border-amber-500 text-amber-700 bg-amber-50' : 'border-transparent text-gray-500'"
								@click="activeTab = tab.id"
							>
								{{ tab.label }}
								<span class="mr-1 text-[10px]">{{ toPersianDigits(getTabCount(tab.id)) }}</span>
							</button>
						</div>
					</div>

					<div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
						<div class="rounded-xl p-3 border hr-accent-tertiary-soft hr-accent-tertiary-border">
							<div class="text-[10px] hr-accent-tertiary-text">{{ __("واریزی ماه") }}</div>
							<div class="text-sm font-bold hr-accent-tertiary-text">{{ formatCurrency(kpiSummary.incoming) }}</div>
						</div>
						<div class="rounded-xl p-3 border hr-accent-soft hr-accent-border">
							<div class="text-[10px] hr-accent-text">{{ __("پرداخت ماه") }}</div>
							<div class="text-sm font-bold hr-accent-text">{{ formatCurrency(kpiSummary.outgoing) }}</div>
						</div>
						<div class="rounded-xl p-3 border hr-accent-secondary-soft hr-accent-secondary-border">
							<div class="text-[10px] hr-accent-secondary-text">{{ __("انتقال ماه") }}</div>
							<div class="text-sm font-bold hr-accent-secondary-text">{{ formatCurrency(kpiSummary.transfer) }}</div>
						</div>
						<div class="rounded-xl p-3 border hr-accent-soft hr-accent-border">
							<div class="text-[10px] hr-accent-text">{{ __("خالص ماه") }}</div>
							<div class="text-sm font-bold hr-accent-text">{{ formatCurrency(kpiSummary.net) }}</div>
						</div>
					</div>

					<div class="bg-white rounded-xl border border-gray-100 p-3" v-if="selectedDate">
						<div class="text-[11px] text-gray-500 mb-1">
							{{ __("خلاصه روز") }}: {{ formatJalaliDateShort(selectedDate) }}
						</div>
						<div class="grid grid-cols-3 gap-2 text-center">
							<div>
								<div class="text-[10px] hr-accent-tertiary-text">{{ __("واریزی") }}</div>
								<div class="text-xs font-bold hr-accent-tertiary-text">{{ formatCurrency(selectedDaySummary.incoming) }}</div>
							</div>
							<div>
								<div class="text-[10px] hr-accent-text">{{ __("پرداخت") }}</div>
								<div class="text-xs font-bold hr-accent-text">{{ formatCurrency(selectedDaySummary.outgoing) }}</div>
							</div>
							<div>
								<div class="text-[10px] hr-accent-secondary-text">{{ __("انتقال") }}</div>
								<div class="text-xs font-bold hr-accent-secondary-text">{{ formatCurrency(selectedDaySummary.transfer) }}</div>
							</div>
						</div>
						<div v-if="selectedDaySummary.total > 0" class="mt-2 flex h-2 rounded-full overflow-hidden bg-gray-100">
							<div v-if="selectedDaySummary.incoming > 0" class="bg-emerald-500" :style="{ width: getPercent(selectedDaySummary.incoming, selectedDaySummary.total) + '%' }" />
							<div v-if="selectedDaySummary.outgoing > 0" class="bg-rose-500" :style="{ width: getPercent(selectedDaySummary.outgoing, selectedDaySummary.total) + '%' }" />
							<div v-if="selectedDaySummary.transfer > 0" class="bg-blue-500" :style="{ width: getPercent(selectedDaySummary.transfer, selectedDaySummary.total) + '%' }" />
						</div>
					</div>

					<div v-if="loadingTransactions" class="bg-white rounded-xl border border-gray-100 p-10 text-center text-sm text-gray-500">
						{{ __("در حال بارگذاری تراکنش‌ها...") }}
					</div>

					<div v-else-if="filteredTransactions.length" class="space-y-2">
						<button
							v-for="tx in filteredTransactions"
							:key="`${tx.doctype}:${tx.name}`"
							class="w-full text-right bg-white rounded-xl border p-3"
							:class="transactionBorderClass(tx)"
							@click="showTransactionDetail(tx)"
						>
							<div class="flex items-start justify-between gap-2">
								<div class="min-w-0">
									<div class="flex items-center gap-1 mb-1">
										<span class="text-[10px] px-1.5 py-0.5 rounded" :class="transactionBadgeClass(tx)">
											{{ getVoucherTypeLabel(tx) }}
										</span>
										<span class="text-[10px] text-gray-400 truncate">{{ tx.name }}</span>
									</div>
									<div class="text-sm font-medium text-gray-800 truncate">
										{{ tx.party_name || tx.party || tx.paid_to || tx.paid_from || __('بدون شرح') }}
									</div>
									<div class="text-[11px] text-gray-500 mt-1">
										{{ formatJalaliDateShort(tx.posting_date) }}
									</div>
								</div>
								<div class="text-left">
									<div class="text-sm font-bold" :class="transactionAmountClass(tx)">
										{{ transactionSign(tx) }}{{ formatCurrency(tx.amount) }}
									</div>
								</div>
							</div>
						</button>
					</div>

					<div v-else class="bg-white rounded-xl border border-gray-100 p-8 text-center text-sm text-gray-500">
						{{ __("برای این روز تراکنشی وجود ندارد.") }}
					</div>

					<ErrorMessage :message="errorMessage" />
				</template>
			</div>

			<Transition name="modal">
				<div v-if="selectedTransaction" class="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
					<div class="absolute inset-0 bg-black/50" @click="closeTransactionDetail" />
					<div class="relative w-full sm:max-w-lg bg-white rounded-t-2xl sm:rounded-xl max-h-[88vh] flex flex-col">
						<div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
							<div>
								<div class="text-[10px] text-gray-500">{{ getVoucherTypeLabel(selectedTransaction) }}</div>
								<div class="text-sm font-semibold text-gray-800">{{ selectedTransaction.name }}</div>
							</div>
							<button class="text-sm text-gray-500" @click="closeTransactionDetail">{{ __("بستن") }}</button>
						</div>

						<div class="flex-1 overflow-y-auto p-4 space-y-3">
							<div class="bg-gray-50 rounded-xl p-4 text-center">
								<div class="text-2xl font-bold" :class="transactionAmountClass(selectedTransaction)">
									{{ transactionSign(selectedTransaction) }}{{ formatCurrency(selectedTransaction.amount) }}
								</div>
							</div>

							<div class="grid grid-cols-2 gap-2 text-xs">
								<div class="bg-gray-50 rounded-lg p-2">
									<div class="text-gray-500">{{ __("تاریخ") }}</div>
									<div class="font-medium">{{ formatJalaliDateShort(selectedTransaction.posting_date) }}</div>
								</div>
								<div class="bg-gray-50 rounded-lg p-2">
									<div class="text-gray-500">{{ __("نوع") }}</div>
									<div class="font-medium">{{ getVoucherTypeLabel(selectedTransaction) }}</div>
								</div>
								<div class="bg-gray-50 rounded-lg p-2" v-if="selectedTransaction.party || selectedTransaction.party_name">
									<div class="text-gray-500">{{ __("طرف حساب") }}</div>
									<div class="font-medium truncate">{{ selectedTransaction.party_name || selectedTransaction.party }}</div>
								</div>
								<div class="bg-gray-50 rounded-lg p-2" v-if="selectedTransaction.reference_no">
									<div class="text-gray-500">{{ __("شماره مرجع") }}</div>
									<div class="font-medium">{{ selectedTransaction.reference_no }}</div>
								</div>
							</div>

							<div class="bg-gray-50 rounded-xl p-3 text-xs">
								<div class="text-gray-500 mb-1">{{ __("حساب‌ها") }}</div>
								<div class="space-y-1">
									<div><span class="text-gray-500">{{ __("از") }}:</span> {{ selectedTransaction.paid_from || '-' }}</div>
									<div><span class="text-gray-500">{{ __("به") }}:</span> {{ selectedTransaction.paid_to || '-' }}</div>
								</div>
							</div>

							<div class="bg-gray-50 rounded-xl p-3 text-xs" v-if="selectedTransaction.remarks">
								<div class="text-gray-500 mb-1">{{ __("توضیحات") }}</div>
								<div class="text-gray-700 whitespace-pre-line">{{ selectedTransaction.remarks }}</div>
							</div>

							<div class="bg-gray-50 rounded-xl p-3" v-if="detailLoading">
								<div class="text-center text-xs text-gray-500">{{ __("در حال بارگذاری جزئیات...") }}</div>
							</div>

							<div class="bg-gray-50 rounded-xl p-3" v-if="!detailLoading && selectedTransaction.gl_entries?.length">
								<div class="text-xs font-semibold text-gray-700 mb-2">{{ __("پیش‌نمایش ثبت‌های حسابداری") }}</div>
								<div class="space-y-1">
									<div
										v-for="row in selectedTransaction.gl_entries"
										:key="row.name"
										class="bg-white rounded-lg p-2 text-[11px]"
									>
										<div class="font-medium text-gray-700 truncate">{{ row.account_name || row.account }}</div>
										<div class="flex items-center justify-between mt-1">
											<div class="text-emerald-600">{{ __("بدهکار") }}: {{ formatCurrency(row.debit) }}</div>
											<div class="text-rose-600">{{ __("بستانکار") }}: {{ formatCurrency(row.credit) }}</div>
										</div>
									</div>
								</div>
							</div>

							<div class="bg-gray-50 rounded-xl p-3" v-if="!detailLoading && selectedTransaction.attachments?.length">
								<div class="text-xs font-semibold text-gray-700 mb-2">
									{{ __("پیوست‌ها") }} ({{ toPersianDigits(selectedTransaction.attachments.length) }})
								</div>
								<div class="grid grid-cols-2 gap-2">
									<a
										v-for="file in selectedTransaction.attachments"
										:key="file.name"
										:href="file.file_url"
										target="_blank"
										class="bg-white rounded-lg p-2 text-[11px] text-amber-700 truncate"
									>
										{{ file.file_name || file.name }}
									</a>
								</div>
							</div>
						</div>

						<div class="p-3 border-t border-gray-100 space-y-2">
							<label
								v-if="canEditSelected"
								class="block w-full py-2 text-center text-xs rounded-lg bg-gray-100 text-gray-700 cursor-pointer"
							>
								<input
									type="file"
									class="hidden"
									accept="image/*"
									@change="handleFileUpload"
								/>
								{{ uploadingFile ? __('در حال آپلود...') : __('افزودن پیوست') }}
							</label>
							<div
								v-else
								class="w-full py-2 text-center text-xs rounded-lg bg-gray-100 text-gray-500"
							>
								{{ __('این سند فقط قابل مشاهده است') }}
							</div>
							<button
								class="w-full py-2 rounded-lg text-xs text-white bg-amber-600"
								:disabled="!canEditSelected"
								:class="!canEditSelected ? 'opacity-50 cursor-not-allowed' : ''"
								@click="goToEdit(selectedTransaction)"
							>
								{{ __("ویرایش سند") }}
							</button>
							<button
								v-if="canEditSelected"
								class="w-full py-2 rounded-lg text-xs text-white bg-rose-600"
								:disabled="cancellingTransaction"
								:class="cancellingTransaction ? 'opacity-60 cursor-wait' : ''"
								@click="cancelSelectedTransaction"
							>
								{{ cancellingTransaction ? __("در حال لغو...") : __("لغو سند") }}
							</button>
						</div>
					</div>
				</div>
			</Transition>

			<div class="fixed bottom-20 left-3 z-40">
				<Transition name="scale">
					<div v-if="showQuickActions" class="absolute bottom-14 left-0 bg-white rounded-xl border border-gray-100 shadow p-2 w-44">
						<button class="w-full text-right p-2 rounded-lg hover:bg-gray-50 text-xs" @click="openQuickAction('pay')">
							{{ __('ثبت پرداخت') }}
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
import { computed, inject, onMounted, ref, watch } from "vue"
import { createResource, ErrorMessage } from "frappe-ui"
import { onIonViewWillEnter } from "@ionic/vue"
import { useRoute, useRouter } from "vue-router"

import BaseLayout from "@/components/BaseLayout.vue"
import SearchableDropdown from "@/components/SearchableDropdown.vue"
import dayjs from "@/utils/dayjs"
import { callImprest, extractErrorMessage } from "@/data/imprest"
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

const viewModes = [
	{ id: "monthly", label: __("ماهانه") },
	{ id: "weekly", label: __("هفتگی") },
	{ id: "daily", label: __("روزانه") },
]

const tabs = [
	{ id: "all", label: __("همه") },
	{ id: "payments", label: __("پرداخت") },
	{ id: "journals", label: __("روزنامه") },
	{ id: "transfers", label: __("انتقال") },
]

const baseDate = ref(new Date())
const selectedDate = ref(dayjs().format("YYYY-MM-DD"))
const viewMode = ref(typeof window !== "undefined" && window.innerWidth < 768 ? "weekly" : "monthly")
const activeTab = ref("all")
const selectedAccounts = ref([])
const accountPickerValue = ref("")
const transactions = ref([])
const loadingTransactions = ref(false)
const selectedTransaction = ref(null)
const detailLoading = ref(false)
const uploadingFile = ref(false)
const cancellingTransaction = ref(false)
const showQuickActions = ref(false)
const errorMessage = ref("")

const contextResource = createResource({
	url: "hrms.api.imprest.get_imprest_context",
	auto: true,
	cache: "hrms:imprest_context",
	onSuccess(data) {
		const filters = parseRouteAccountFilters(route.query)
		selectedAccounts.value = filters
		if (route.query.date) {
			const date = dayjs(String(route.query.date))
			if (date.isValid()) {
				selectedDate.value = date.format("YYYY-MM-DD")
				baseDate.value = date.toDate()
			}
		}
	},
	onError(error) {
		errorMessage.value = extractErrorMessage(error, __("خطا در بارگذاری اطلاعات تنخواه"))
	},
})

const calendarResource = createResource({
	url: "hrms.api.imprest.get_imprest_calendar_transactions",
	auto: false,
})

const isImprestEnabled = computed(() => Boolean(contextResource.data?.has_imprest))
const allowedAccounts = computed(() => contextResource.data?.allowed_accounts || [])
const accountOptions = computed(() =>
	allowedAccounts.value.map((row) => ({
		label: row.account_name || row.account,
		value: row.account,
	}))
)
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

const currentJalali = computed(() =>
	gregorianToJalali(baseDate.value.getFullYear(), baseDate.value.getMonth() + 1, baseDate.value.getDate())
)

const currentJalaliMonth = computed(() => currentJalali.value.month - 1)

const currentTitle = computed(
	() => `${persianMonths[currentJalali.value.month - 1]} ${toPersianDigits(currentJalali.value.year)}`
)

const transactionsByDate = computed(() => {
	const grouped = {}
	for (const tx of transactions.value) {
		const date = String(tx.posting_date || "").slice(0, 10)
		if (!date) continue
		if (!grouped[date]) grouped[date] = []
		grouped[date].push(tx)
	}
	return grouped
})

function summarizeDay(rows) {
	const summary = { incoming: 0, outgoing: 0, transfer: 0, total: 0 }
	for (const row of rows || []) {
		const amount = Number(row.amount || 0)
		if (row.transaction_type === "incoming") summary.incoming += amount
		else if (row.transaction_type === "outgoing") summary.outgoing += amount
		else summary.transfer += amount
	}
	summary.total = summary.incoming + summary.outgoing + summary.transfer
	return summary
}

const calendarDays = computed(() => {
	const days = []
	const todayStr = dayjs().format("YYYY-MM-DD")
	const gStart = jalaliToGregorian(currentJalali.value.year, currentJalali.value.month, 1)
	const start = dayjs(`${gStart.year}-${String(gStart.month).padStart(2, "0")}-${String(gStart.day).padStart(2, "0")}`)
	const daysInMonth = getJalaliDaysInMonth(currentJalali.value.year, currentJalali.value.month)

	for (let i = 0; i < daysInMonth; i++) {
		const date = start.add(i, "day")
		const dateStr = date.format("YYYY-MM-DD")
		const jalali = gregorianToJalali(date.year(), date.month() + 1, date.date())
		const summary = summarizeDay(transactionsByDate.value[dateStr] || [])
		days.push({
			key: dateStr,
			dateStr,
			jalaliDay: jalali.day,
			dayOfWeek: date.day(),
			isToday: dateStr === todayStr,
			hasTransactions: summary.total > 0,
			...summary,
		})
	}
	return days
})

const monthGridDays = computed(() => {
	const first = calendarDays.value[0]
	if (!first) return []
	const firstDayIndex = (Number(first.dayOfWeek) + 1) % 7
	const result = []

	for (let i = 0; i < firstDayIndex; i++) {
		result.push({
			key: `prev-${i}`,
			isCurrentMonth: false,
			jalaliDay: "",
			dateStr: "",
			hasTransactions: false,
			incoming: 0,
			outgoing: 0,
			transfer: 0,
			total: 0,
		})
	}

	for (const day of calendarDays.value) {
		result.push({ ...day, isCurrentMonth: true })
	}

	while (result.length < 42) {
		result.push({
			key: `next-${result.length}`,
			isCurrentMonth: false,
			jalaliDay: "",
			dateStr: "",
			hasTransactions: false,
			incoming: 0,
			outgoing: 0,
			transfer: 0,
			total: 0,
		})
	}

	return result
})

const weekDaysGrid = computed(() => {
	const current = dayjs(baseDate.value)
	const weekStartOffset = (current.day() + 1) % 7
	const saturday = current.subtract(weekStartOffset, "day")
	const days = []
	for (let i = 0; i < 7; i++) {
		const date = saturday.add(i, "day")
		const dateStr = date.format("YYYY-MM-DD")
		const jalali = gregorianToJalali(date.year(), date.month() + 1, date.date())
		const summary = summarizeDay(transactionsByDate.value[dateStr] || [])
		days.push({
			key: dateStr,
			dateStr,
			jalaliDay: jalali.day,
			dayOfWeek: date.day(),
			isToday: dateStr === dayjs().format("YYYY-MM-DD"),
			hasTransactions: summary.total > 0,
			...summary,
		})
	}
	return days
})

const dayTransactions = computed(() => transactionsByDate.value[selectedDate.value] || [])

const filteredTransactions = computed(() => {
	if (activeTab.value === "all") return dayTransactions.value
	if (activeTab.value === "payments") {
		return dayTransactions.value.filter((tx) => tx.doctype === "Payment Entry")
	}
	if (activeTab.value === "journals") {
		return dayTransactions.value.filter((tx) => tx.doctype === "Journal Entry")
	}
	if (activeTab.value === "transfers") {
		return dayTransactions.value.filter((tx) => tx.transaction_type === "transfer")
	}
	return dayTransactions.value
})

const selectedDaySummary = computed(() => summarizeDay(dayTransactions.value))

const kpiSummary = computed(() => {
	let incoming = 0
	let outgoing = 0
	let transfer = 0
	for (const day of calendarDays.value) {
		incoming += Number(day.incoming || 0)
		outgoing += Number(day.outgoing || 0)
		transfer += Number(day.transfer || 0)
	}
	return {
		incoming,
		outgoing,
		transfer,
		net: incoming - outgoing,
	}
})

const canEditSelected = computed(() => Boolean(selectedTransaction.value?.can_edit))

function getTabCount(tabId) {
	if (tabId === "all") return dayTransactions.value.length
	if (tabId === "payments") return dayTransactions.value.filter((tx) => tx.doctype === "Payment Entry").length
	if (tabId === "journals") return dayTransactions.value.filter((tx) => tx.doctype === "Journal Entry").length
	if (tabId === "transfers") return dayTransactions.value.filter((tx) => tx.transaction_type === "transfer").length
	return 0
}

function getPercent(value, total) {
	if (!total) return 0
	return (Number(value || 0) / Number(total || 1)) * 100
}

function getVoucherTypeLabel(tx) {
	if (!tx) return "-"
	if (tx.doctype === "Journal Entry") return __("روزنامه")
	if (tx.payment_type === "Internal Transfer" || tx.transaction_type === "transfer") return __("انتقال داخلی")
	if (tx.transaction_type === "incoming") return __("واریزی")
	return __("پرداخت")
}

function transactionBadgeClass(tx) {
	if (tx.transaction_type === "incoming") return "bg-emerald-100 text-emerald-700"
	if (tx.transaction_type === "outgoing") return "bg-rose-100 text-rose-700"
	if (tx.doctype === "Journal Entry") return "bg-purple-100 text-purple-700"
	return "bg-blue-100 text-blue-700"
}

function transactionBorderClass(tx) {
	if (tx.transaction_type === "incoming") return "border-emerald-200"
	if (tx.transaction_type === "outgoing") return "border-rose-200"
	if (tx.doctype === "Journal Entry") return "border-purple-200"
	return "border-blue-200"
}

function transactionAmountClass(tx) {
	if (tx.transaction_type === "incoming") return "text-emerald-600"
	if (tx.transaction_type === "outgoing") return "text-rose-600"
	return "text-blue-600"
}

function transactionSign(tx) {
	if (tx.transaction_type === "incoming") return "+"
	if (tx.transaction_type === "outgoing") return "-"
	return ""
}

function formatCurrency(value) {
	const amount = Math.round(Number(value || 0))
	return toPersianDigits(new Intl.NumberFormat("en-US").format(Math.abs(amount)))
}

function formatCompact(value) {
	const amount = Math.round(Number(value || 0))
	if (amount >= 1000000) return `${toPersianDigits((amount / 1000000).toFixed(1))}م`
	if (amount >= 1000) return `${toPersianDigits((amount / 1000).toFixed(0))}ه`
	return toPersianDigits(amount)
}

function navigatePrev() {
	if (viewMode.value === "weekly") {
		baseDate.value = dayjs(baseDate.value).subtract(7, "day").toDate()
	} else if (viewMode.value === "daily") {
		const nextDate = dayjs(baseDate.value).subtract(1, "day")
		baseDate.value = nextDate.toDate()
		selectedDate.value = nextDate.format("YYYY-MM-DD")
	} else {
		const month = currentJalali.value.month === 1 ? 12 : currentJalali.value.month - 1
		const year = currentJalali.value.month === 1 ? currentJalali.value.year - 1 : currentJalali.value.year
		const gregorian = jalaliToGregorian(year, month, 1)
		baseDate.value = new Date(gregorian.year, gregorian.month - 1, gregorian.day, 12, 0, 0)
	}
}

function navigateNext() {
	if (viewMode.value === "weekly") {
		baseDate.value = dayjs(baseDate.value).add(7, "day").toDate()
	} else if (viewMode.value === "daily") {
		const nextDate = dayjs(baseDate.value).add(1, "day")
		baseDate.value = nextDate.toDate()
		selectedDate.value = nextDate.format("YYYY-MM-DD")
	} else {
		const month = currentJalali.value.month === 12 ? 1 : currentJalali.value.month + 1
		const year = currentJalali.value.month === 12 ? currentJalali.value.year + 1 : currentJalali.value.year
		const gregorian = jalaliToGregorian(year, month, 1)
		baseDate.value = new Date(gregorian.year, gregorian.month - 1, gregorian.day, 12, 0, 0)
	}
}

function selectMonth(monthIndex) {
	const gregorian = jalaliToGregorian(currentJalali.value.year, monthIndex + 1, 1)
	baseDate.value = new Date(gregorian.year, gregorian.month - 1, gregorian.day, 12, 0, 0)
}

function selectDate(day) {
	if (!day?.isCurrentMonth && viewMode.value === "monthly") return
	if (!day?.dateStr) return
	selectedDate.value = day.dateStr
	if (viewMode.value !== "monthly") {
		const date = dayjs(day.dateStr)
		if (date.isValid()) {
			baseDate.value = date.toDate()
		}
	}
}

function goToToday() {
	baseDate.value = new Date()
	selectedDate.value = dayjs().format("YYYY-MM-DD")
}

async function loadTransactions() {
	if (!isImprestEnabled.value) return
	loadingTransactions.value = true
	errorMessage.value = ""
	const { fromDate, toDate } = getFetchRange()

	calendarResource.fetch(
		{
			from_date: fromDate,
			to_date: toDate,
			account: selectedAccounts.value.length === 1 ? selectedAccounts.value[0] : null,
			accounts: selectedAccounts.value.length > 1 ? JSON.stringify(selectedAccounts.value) : null,
		},
		{
			onSuccess(data) {
				transactions.value = data || []
				loadingTransactions.value = false
			},
			onError(error) {
				errorMessage.value = extractErrorMessage(error, __("خطا در دریافت تراکنش‌های تقویم"))
				loadingTransactions.value = false
			},
		}
	)
}

function getFetchRange() {
	if (viewMode.value === "weekly") {
		const current = dayjs(baseDate.value)
		const weekStartOffset = (current.day() + 1) % 7
		const from = current.subtract(weekStartOffset, "day")
		const to = from.add(6, "day")
		return {
			fromDate: from.format("YYYY-MM-DD"),
			toDate: to.format("YYYY-MM-DD"),
		}
	}

	if (viewMode.value === "daily") {
		const current = dayjs(selectedDate.value || baseDate.value)
		const day = current.isValid() ? current : dayjs(baseDate.value)
		const date = day.format("YYYY-MM-DD")
		return {
			fromDate: date,
			toDate: date,
		}
	}

	const start = jalaliToGregorian(currentJalali.value.year, currentJalali.value.month, 1)
	const end = jalaliToGregorian(
		currentJalali.value.year,
		currentJalali.value.month,
		getJalaliDaysInMonth(currentJalali.value.year, currentJalali.value.month)
	)

	return {
		fromDate: `${start.year}-${String(start.month).padStart(2, "0")}-${String(start.day).padStart(2, "0")}`,
		toDate: `${end.year}-${String(end.month).padStart(2, "0")}-${String(end.day).padStart(2, "0")}`,
	}
}

function closeTransactionDetail() {
	selectedTransaction.value = null
	detailLoading.value = false
}

async function showTransactionDetail(transaction) {
	selectedTransaction.value = {
		...transaction,
		attachments: transaction.attachments || [],
		gl_entries: transaction.gl_entries || [],
	}
	detailLoading.value = true
	try {
		const detail = await callImprest("get_imprest_transaction_detail", {
			name: transaction.name,
			doctype: transaction.doctype,
		})
		selectedTransaction.value = {
			...selectedTransaction.value,
			...detail,
		}
	} catch (error) {
		errorMessage.value = extractErrorMessage(error, __("خطا در دریافت جزئیات تراکنش"))
	} finally {
		detailLoading.value = false
	}
}

async function handleFileUpload(event) {
	const file = event?.target?.files?.[0]
	if (!file || !selectedTransaction.value) return
	uploadingFile.value = true
	try {
		const content = await readFileAsDataUrl(file)
		await callImprest("attach_imprest_image", {
			name: selectedTransaction.value.name,
			doctype: selectedTransaction.value.doctype,
			file_name: file.name,
			file_content: content,
		})
		await showTransactionDetail(selectedTransaction.value)
	} catch (error) {
		errorMessage.value = extractErrorMessage(error, __("آپلود پیوست ناموفق بود"))
	} finally {
		uploadingFile.value = false
		event.target.value = ""
	}
}

async function cancelSelectedTransaction() {
	if (!selectedTransaction.value?.name || !canEditSelected.value || cancellingTransaction.value) return
	const confirmed = typeof window === "undefined" ? true : window.confirm(__("آیا از لغو این سند مطمئن هستید؟"))
	if (!confirmed) return

	cancellingTransaction.value = true
	errorMessage.value = ""
	try {
		await callImprest("cancel_imprest_entry", {
			name: selectedTransaction.value.name,
			doctype: selectedTransaction.value.doctype,
		})
		closeTransactionDetail()
		await loadTransactions()
	} catch (error) {
		errorMessage.value = extractErrorMessage(error, __("لغو سند ناموفق بود"))
	} finally {
		cancellingTransaction.value = false
	}
}

function readFileAsDataUrl(file) {
	return new Promise((resolve, reject) => {
		const reader = new FileReader()
		reader.onload = () => resolve(reader.result)
		reader.onerror = () => reject(new Error("file_read_failed"))
		reader.readAsDataURL(file)
	})
}

function goToEdit(transaction) {
	if (!transaction?.name || !transaction?.can_edit) return
	closeTransactionDetail()
	router.push({
		name: "ImprestQuickEntryEditView",
		params: { id: transaction.name },
		query: { doctype: transaction.doctype || "Payment Entry" },
	})
}

function openQuickAction(type) {
	showQuickActions.value = false
	const query = {
		type,
		date: selectedDate.value || dayjs().format("YYYY-MM-DD"),
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

watch([selectedAccounts, baseDate, viewMode], () => {
	if (isImprestEnabled.value) loadTransactions()
}, { deep: true })

watch(
	isImprestEnabled,
	(enabled) => {
		if (enabled) loadTransactions()
	},
	{ immediate: true }
)

watch(selectedDate, () => {
	if (viewMode.value === "daily" && isImprestEnabled.value) loadTransactions()
})

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
	() => route.query.date,
	(value) => {
		if (!value) return
		const date = dayjs(String(value))
		if (!date.isValid()) return
		selectedDate.value = date.format("YYYY-MM-DD")
		baseDate.value = date.toDate()
	},
	{ immediate: true }
)

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

watch(
	() => route.query.refresh,
	(value) => {
		if (!value || !isImprestEnabled.value) return
		loadTransactions()
	}
)

onMounted(() => {
	if (!selectedDate.value) selectedDate.value = dayjs().format("YYYY-MM-DD")
})

onIonViewWillEnter(() => {
	if (isImprestEnabled.value) loadTransactions()
})

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
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
	transition: all 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
	opacity: 0;
}

.modal-enter-from > div:last-child,
.modal-leave-to > div:last-child {
	transform: translateY(12px);
}

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
