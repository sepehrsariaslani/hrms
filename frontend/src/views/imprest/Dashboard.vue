<template>
	<BaseLayout :pageTitle="__('تنخواه')">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-4">
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

					<div class="bg-white rounded-xl p-4 border border-gray-100">
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
								{{ formatSignedAmount(stats.period_net, Number(stats.period_net || 0) >= 0 ? "incoming" : "outgoing") }}
							</div>
						</div>
					</div>

						<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
							<router-link :to="{ name: 'ImprestQuickEntryView' }" v-slot="{ navigate }">
								<Button class="w-full py-5 text-base" @click="navigate">
									{{ __("ثبت سریع تنخواه") }}
								</Button>
							</router-link>
							<router-link
								:to="{ name: 'ImprestCalendarView', query: calendarQuery }"
								v-slot="{ navigate }"
							>
								<Button variant="outline" class="w-full py-5 text-base" @click="navigate">
									{{ __("تقویم تنخواه") }}
								</Button>
							</router-link>
						</div>

					<div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
						<div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
							<div class="text-sm font-semibold text-gray-800">{{ __("تراکنش‌های اخیر") }}</div>
							<div class="text-xs text-gray-500">
								{{ toPersianDigits(recentTransactions.length) }} {{ __("مورد") }}
							</div>
						</div>
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
											{{ formatJalaliDateShort(tx.posting_date) }} · {{ tx.name }} · {{ tx.doctype || "Payment Entry" }}
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
											{{ formatJalaliDateShort(tx.posting_date) }} · {{ tx.name }} · {{ tx.doctype || "Payment Entry" }}
										</div>
									</div>
									<div class="text-sm font-semibold" :class="getAmountClass(tx.transaction_type)">
										{{ formatSignedAmount(tx.amount, tx.transaction_type) }}
									</div>
								</div>
							</div>
						</div>
					</div>
				</template>

				<ErrorMessage :message="errorMessage" />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue"
import { createResource, ErrorMessage } from "frappe-ui"
import { onIonViewWillEnter } from "@ionic/vue"
import { useRoute } from "vue-router"

import BaseLayout from "@/components/BaseLayout.vue"
import SearchableDropdown from "@/components/SearchableDropdown.vue"
import { extractErrorMessage } from "@/data/imprest"
import { formatJalaliDateShort, toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")
const route = useRoute()
const selectedAccounts = ref([])
const accountPickerValue = ref("")
const errorMessage = ref("")

const contextResource = createResource({
	url: "hrms.api.imprest.get_imprest_context",
	auto: true,
	cache: "hrms:imprest_context",
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

watch(selectedAccounts, () => {
	if (isImprestEnabled.value) reloadStats()
}, { deep: true })

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

function reloadStats() {
	if (!isImprestEnabled.value) return
	errorMessage.value = ""
	const payload = {}
	if (selectedAccounts.value.length === 1) {
		payload.account = selectedAccounts.value[0]
	}
	if (selectedAccounts.value.length > 1) {
		payload.accounts = JSON.stringify(selectedAccounts.value)
	}
	dashboardResource.fetch(
		payload,
		{
			onError(error) {
				errorMessage.value = extractErrorMessage(error, __("خطا در دریافت داشبورد تنخواه"))
			},
		}
	)
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
	return ["Pay", "Internal Transfer"].includes(tx.payment_type)
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

onIonViewWillEnter(() => {
	if (isImprestEnabled.value) reloadStats()
})
</script>
