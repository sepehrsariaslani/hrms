<template>
	<BaseLayout :pageTitle="props.id ? __('ویرایش تنخواه') : __('ثبت سریع تنخواه')">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-4">
				<div v-if="!isImprestEnabled" class="bg-white rounded-xl p-4 text-sm text-gray-600">
					{{ __("برای شما حساب تنخواه تعریف نشده است.") }}
				</div>

				<template v-else>
					<div
						v-if="props.id"
						class="bg-amber-50 border border-amber-200 rounded-xl p-3 text-xs text-amber-700"
					>
						{{ __("شماره سند") }}: {{ toPersianDigits(editingDocName || props.id) }}
					</div>

					<div class="bg-white rounded-xl border border-gray-100 p-4 space-y-3">
						<div class="grid grid-cols-3 gap-2" data-tour="imprest-entry-type">
							<button
								class="rounded-lg border px-3 py-2 text-sm"
								:class="
									paymentType === 'Pay'
										? 'bg-rose-50 border-rose-300 text-rose-700'
										: 'border-gray-200 text-gray-600'
								"
								@click="paymentType = 'Pay'"
							>
								{{ __("پرداخت") }}
							</button>
							<button
								class="rounded-lg border px-3 py-2 text-sm"
								:class="
									paymentType === 'Receive'
										? 'bg-emerald-50 border-emerald-300 text-emerald-700'
										: 'border-gray-200 text-gray-600'
								"
								@click="paymentType = 'Receive'"
							>
								{{ __("دریافت") }}
							</button>
							<button
								class="rounded-lg border px-3 py-2 text-sm"
								:class="
									paymentType === 'Internal Transfer'
										? 'bg-blue-50 border-blue-300 text-blue-700'
										: 'border-gray-200 text-gray-600'
								"
								@click="paymentType = 'Internal Transfer'"
							>
								{{ __("انتقال داخلی") }}
							</button>
						</div>

						<div data-tour="imprest-entry-account">
							<label class="block text-xs text-gray-600 mb-1">{{ __("تاریخ") }}</label>
							<JalaliDatePicker v-model="postingDate" />
						</div>

						<div>
							<label class="block text-xs text-gray-600 mb-1">{{ __("مبلغ") }}</label>
							<PersianNumberInput v-model="amount" placeholder="مبلغ را وارد کنید" />
						</div>

						<div>
							<label class="block text-xs text-gray-600 mb-1">
								{{ paymentType === "Receive" ? __("به حساب تنخواه") : __("از حساب تنخواه") }}
							</label>
							<SearchableDropdown
								v-model="paidFrom"
								:options="allowedAccountOptions"
								:placeholder="__('انتخاب حساب')"
							/>
						</div>

						<template v-if="paymentType === 'Internal Transfer'">
							<div data-tour="imprest-entry-party-type">
								<label class="block text-xs text-gray-600 mb-1">{{ __("به حساب") }}</label>
								<SearchableDropdown
									v-model="paidTo"
									:options="cashBankAccountOptions"
									:placeholder="__('انتخاب حساب مقصد')"
								/>
								<div class="text-[11px] text-gray-500 mt-1">
									{{ __("مبدا فقط از حساب‌های تنخواه شماست، مقصد می‌تواند سایر حساب‌های نقد/بانک شرکت باشد.") }}
								</div>
							</div>
						</template>

						<template v-else>
							<div data-tour="imprest-entry-party">
								<label class="block text-xs text-gray-600 mb-1">{{ __("نوع طرف حساب") }}</label>
								<div class="grid grid-cols-3 gap-2">
									<button
										v-for="option in partyTypeOptions"
										:key="option.value"
										class="rounded-md border px-2 py-1.5 text-xs"
										:class="
											partyType === option.value
												? 'bg-amber-500 text-white border-amber-500'
												: 'border-gray-200 text-gray-700'
										"
										@click="setPartyType(option.value)"
									>
										{{ option.label }}
									</button>
								</div>
							</div>

							<div>
								<label class="block text-xs text-gray-600 mb-1">{{ __("طرف حساب") }}</label>
								<template v-if="partyType === 'Account'">
									<SearchableDropdown
										v-model="party"
										:options="companyAccountOptions"
										:placeholder="__('انتخاب حساب مقصد')"
									/>
									<div class="text-[11px] text-gray-500 mt-1">
										{{ __("در حالت حساب، سند به صورت روزنامه ثبت می‌شود (به‌جای پرداخت).") }}
									</div>
								</template>
								<template v-else>
									<SearchableDropdown
										v-model="party"
										:options="partyOptionsForDropdown"
										:placeholder="partyType === 'Employee' ? __('انتخاب کارمند') : __('انتخاب تامین‌کننده')"
									/>
								</template>
							</div>
						</template>

						<div data-tour="imprest-entry-tracking">
							<label class="block text-xs text-gray-600 mb-1">
								{{ __("شماره پیگیری") }} <span class="text-rose-600">*</span>
							</label>
							<input
								v-model="referenceNo"
								type="text"
								class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
								:placeholder="__('الزامی')"
							/>
						</div>

						<div>
							<label class="block text-xs text-gray-600 mb-1">{{ __("توضیحات") }}</label>
							<textarea
								v-model="remarks"
								rows="3"
								class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
							/>
						</div>
					</div>

					<AttachmentDropzone
						v-model="selectedFiles"
						:existing-files="existingAttachments"
						:label="__('عکس فیش / رسید')"
						accept="image/*"
						:max-file-size-m-b="5"
						@error="onAttachmentError"
					/>

					<Button
						class="w-full py-5 text-base !bg-amber-600 !text-white hover:!bg-amber-700"
						:disabled="!canSubmit || saving"
						:loading="saving"
						@click="submitEntry"
						data-tour="imprest-entry-submit"
					>
						{{
							props.id
								? __("ثبت تغییرات")
								: selectedFiles.length
									? __("ثبت سند و آپلود رسید")
									: __("ثبت سند")
						}}
					</Button>
					<Button
						v-if="props.id"
						class="w-full py-5 text-base !bg-blue-600 !text-white hover:!bg-blue-700"
						:disabled="cancelling"
						:loading="cancelling"
						@click="cancelEntry"
					>
						{{ __("لغو سند") }}
					</Button>
				</template>

				<ErrorMessage :message="errorMessage" />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue"
import { onIonViewWillEnter } from "@ionic/vue"
import { createResource, ErrorMessage, toast } from "frappe-ui"
import { useRoute, useRouter } from "vue-router"

import BaseLayout from "@/components/BaseLayout.vue"
import JalaliDatePicker from "@/components/JalaliDatePicker.vue"
import PersianNumberInput from "@/components/PersianNumberInput.vue"
import SearchableDropdown from "@/components/SearchableDropdown.vue"
import AttachmentDropzone from "@/components/AttachmentDropzone.vue"
import dayjs from "@/utils/dayjs"
import { callImprest, extractErrorMessage } from "@/data/imprest"
import { toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")
const router = useRouter()
const route = useRoute()

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

const paymentType = ref("Pay")
const postingDate = ref(dayjs().format("YYYY-MM-DD"))
const amount = ref("")
const paidFrom = ref("")
const paidTo = ref("")
const partyType = ref("Supplier")
const party = ref("")
const remarks = ref("")
const referenceNo = ref("")
const editingDocName = ref("")
const editingDoctype = ref("")
const saving = ref(false)
const cancelling = ref(false)
const errorMessage = ref("")
const selectedFiles = ref([])
const existingAttachments = ref([])
const companyCashBankAccounts = ref([])
const companyAccounts = ref([])
const supplierPartyOptions = ref([])
const employeePartyOptions = ref([])

const partyTypeOptions = computed(() => {
	const options = [
		{ label: __("تامین‌کننده"), value: "Supplier" },
		{ label: __("کارمند"), value: "Employee" },
	]
	if (paymentType.value === "Pay") {
		options.push({ label: __("حساب"), value: "Account" })
	}
	return options
})

const contextResource = createResource({
	url: "hrms.api.imprest.get_imprest_context",
	auto: true,
	cache: "hrms:imprest_context",
	onSuccess(data) {
		applyCreateRouteDefaults(data)
		ensureLookupResourcesLoaded()
		if (props.id) loadForEdit()
	},
	onError(error) {
		errorMessage.value = extractErrorMessage(error, __("خطا در بارگذاری اطلاعات تنخواه"))
	},
})

const entryResource = createResource({
	url: "hrms.api.imprest.get_imprest_payment_entry_for_edit",
	auto: false,
})

const createResourceEntry = createResource({
	url: "hrms.api.imprest.create_imprest_payment_entry",
	auto: false,
})

const updateResourceEntry = createResource({
	url: "hrms.api.imprest.update_imprest_payment_entry",
	auto: false,
})

const companyAccountsResource = createResource({
	url: "hrms.api.imprest.get_company_cash_bank_accounts",
	auto: false,
})

const allCompanyAccountsResource = createResource({
	url: "hrms.api.imprest.get_company_accounts",
	auto: false,
})

const partyOptionsResource = createResource({
	url: "hrms.api.imprest.get_imprest_party_options",
	auto: false,
})

const attachImageResource = createResource({
	url: "hrms.api.imprest.attach_imprest_image",
	auto: false,
})

const isImprestEnabled = computed(() => Boolean(contextResource.data?.has_imprest))
const allowedAccounts = computed(() => contextResource.data?.allowed_accounts || [])
const allowedAccountOptions = computed(() =>
	allowedAccounts.value.map((account) => ({
		label: account.account_name || account.account,
		value: account.account,
	}))
)
const cashBankAccountOptions = computed(() =>
	(companyCashBankAccounts.value || []).map((account) => ({
		label: account.account_name || account.name,
		value: account.name,
	}))
)
const companyAccountOptions = computed(() =>
	(companyAccounts.value || []).map((account) => ({
		label: account.account_name || account.name,
		value: account.name,
	}))
)
const partyOptionsForDropdown = computed(() =>
	partyType.value === "Employee" ? employeePartyOptions.value : supplierPartyOptions.value
)

const canSubmit = computed(() => {
	const numericAmount = Number(amount.value || 0)
	if (!paidFrom.value || numericAmount <= 0 || !postingDate.value) return false
	if (!String(referenceNo.value || "").trim()) return false

	if (paymentType.value === "Internal Transfer") {
		return Boolean(paidTo.value && paidTo.value !== paidFrom.value)
	}

	if (partyType.value === "Account") {
		return Boolean(party.value && party.value !== paidFrom.value)
	}

	return Boolean(partyType.value && party.value)
})

function setPartyType(value) {
	partyType.value = value
	party.value = ""
}

function applyCreateRouteDefaults(data, force = false) {
	if (props.id) return

	const queryAccounts = getAccountFiltersFromQuery()
	const initialAccount = route.query.account || queryAccounts[0] || data?.default_account || ""
	if (force || !paidFrom.value) paidFrom.value = initialAccount
	if (force || !paidTo.value) paidTo.value = initialAccount

	if (route.query.type === "transfer") {
		paymentType.value = "Internal Transfer"
	} else if (route.query.type === "receive") {
		paymentType.value = "Receive"
	} else if (route.query.type === "pay") {
		paymentType.value = "Pay"
	}

	if (route.query.date) {
		const qDate = dayjs(String(route.query.date))
		if (qDate.isValid()) postingDate.value = qDate.format("YYYY-MM-DD")
	}
}

watch(paymentType, (value) => {
	if (value === "Internal Transfer") {
		party.value = ""
		return
	}
	if (!partyTypeOptions.value.find((option) => option.value === partyType.value)) {
		partyType.value = "Supplier"
		party.value = ""
	}
})

watch(
	() => props.id,
	(value) => {
		if (value && isImprestEnabled.value) {
			loadForEdit()
			return
		}
		if (!value) {
			applyCreateRouteDefaults(contextResource.data, true)
		}
	},
	{ immediate: true }
)

watch(
	() => route.query.doctype,
	() => {
		if (props.id && isImprestEnabled.value) {
			loadForEdit()
		}
	}
)

watch(
	() => route.query.date,
	() => applyCreateRouteDefaults(contextResource.data, true)
)

watch(
	() => route.query.account,
	() => applyCreateRouteDefaults(contextResource.data, true)
)

watch(
	() => route.query.accounts,
	() => applyCreateRouteDefaults(contextResource.data, true)
)

function onAttachmentError(message) {
	errorMessage.value = message
}

function loadCompanyAccounts() {
	companyAccountsResource.fetch(
		{},
		{
			onSuccess(data) {
				companyCashBankAccounts.value = data || []
			},
			onError() {
				companyCashBankAccounts.value = []
			},
		}
	)
}

function loadAllCompanyAccounts() {
	allCompanyAccountsResource.fetch(
		{},
		{
			onSuccess(data) {
				companyAccounts.value = data || []
			},
			onError() {
				companyAccounts.value = []
			},
		}
	)
}

function loadPartyOptions(type) {
	partyOptionsResource.fetch(
		{
			party_type: type,
			limit: 500,
		},
		{
			onSuccess(data) {
				const options = (data || []).map((row) => ({
					label: row.label || row.value,
					value: row.value,
				}))
				if (type === "Employee") {
					employeePartyOptions.value = options
					return
				}
				supplierPartyOptions.value = options
			},
			onError() {
				if (type === "Employee") {
					employeePartyOptions.value = []
					return
				}
				supplierPartyOptions.value = []
			},
		}
	)
}

function ensureLookupResourcesLoaded(force = false) {
	if (force || !companyCashBankAccounts.value.length) {
		loadCompanyAccounts()
	}
	if (force || !companyAccounts.value.length) {
		loadAllCompanyAccounts()
	}
	if (force || !supplierPartyOptions.value.length) {
		loadPartyOptions("Supplier")
	}
	if (force || !employeePartyOptions.value.length) {
		loadPartyOptions("Employee")
	}
}

function loadForEdit() {
	errorMessage.value = ""
	entryResource.fetch(
		{ name: props.id, doctype: route.query.doctype || null },
		{
			onSuccess(data) {
				editingDocName.value = data?.name || props.id
				editingDoctype.value = data?.doctype || route.query.doctype || "Payment Entry"
				paymentType.value = data?.payment_type || "Pay"
				postingDate.value = data?.posting_date || dayjs().format("YYYY-MM-DD")
				amount.value = data?.amount || data?.paid_amount || 0
				paidFrom.value =
					data?.payment_type === "Receive" ? data?.paid_to || "" : data?.paid_from || ""
				paidTo.value = data?.paid_to || ""
				partyType.value = data?.party_type || "Supplier"
				party.value = data?.party || ""
				remarks.value = data?.remarks || ""
				referenceNo.value = data?.reference_no || ""
				existingAttachments.value = data?.attachments || []
			},
			onError(error) {
				errorMessage.value = extractErrorMessage(error, __("خطا در دریافت سند"))
			},
		}
	)
}

async function submitEntry() {
	if (!canSubmit.value) return
	saving.value = true
	errorMessage.value = ""

	const payload = {
		payment_type: paymentType.value,
		posting_date: postingDate.value,
		amount: Number(amount.value || 0),
		doctype: editingDoctype.value || route.query.doctype || undefined,
		paid_from: paidFrom.value,
		paid_to: paymentType.value === "Internal Transfer" ? paidTo.value : null,
		party_type: paymentType.value === "Internal Transfer" ? null : partyType.value,
		party: paymentType.value === "Internal Transfer" ? null : party.value,
		remarks: remarks.value || "",
		reference_no: String(referenceNo.value || "").trim(),
	}

	try {
		const resource = props.id ? updateResourceEntry : createResourceEntry
		const params = props.id
			? { name: props.id, payload: JSON.stringify(payload) }
			: { payload: JSON.stringify(payload) }
		const result = await submitResource(resource, params)
		const entry = result?.entry || result?.payment_entry || result?.journal_entry || result
		const entryName = entry?.name || props.id
		const entryDoctype = entry?.doctype || editingDoctype.value || route.query.doctype || "Payment Entry"

		if (selectedFiles.value.length && entryName) {
			await uploadSelectedFiles(entryName, entryDoctype)
		}

		toast({
			title: __("Success"),
			text: __("سند تنخواه با موفقیت ثبت شد."),
			icon: "check-circle",
			iconClasses: "text-green-600",
			position: "bottom-center",
		})

			if (props.id) {
				router.replace({
					name: "ImprestQuickEntryEditView",
					params: { id: entryName },
					query: { doctype: entryDoctype },
				})
			} else {
				const calendarQuery = {
					date: postingDate.value,
					refresh: String(Date.now()),
				}
				const routeAccount = String(route.query.account || "").trim()
				if (routeAccount) {
					calendarQuery.account = routeAccount
				} else {
					const queryAccounts = getAccountFiltersFromQuery()
					if (queryAccounts.length === 1) {
						calendarQuery.account = queryAccounts[0]
					} else if (queryAccounts.length > 1) {
						calendarQuery.accounts = JSON.stringify(queryAccounts)
					}
				}

				router.replace({
					name: "ImprestCalendarView",
					query: calendarQuery,
				})
			}
	} catch (error) {
		errorMessage.value = extractErrorMessage(error, __("ثبت سند ناموفق بود."))
	} finally {
		saving.value = false
	}
}

async function cancelEntry() {
	if (!props.id || cancelling.value) return
	const confirmed = typeof window === "undefined" ? true : window.confirm(__("آیا از لغو این سند مطمئن هستید؟"))
	if (!confirmed) return

	cancelling.value = true
	errorMessage.value = ""
	try {
		await callImprest("cancel_imprest_entry", {
			name: props.id,
			doctype: editingDoctype.value || route.query.doctype || "Payment Entry",
		})
		toast({
			title: __("Success"),
			text: __("سند با موفقیت لغو شد."),
			icon: "check-circle",
			iconClasses: "text-green-600",
			position: "bottom-center",
		})
		router.replace({
			name: "ImprestCalendarView",
			query: {
				date: postingDate.value || dayjs().format("YYYY-MM-DD"),
				refresh: String(Date.now()),
			},
		})
	} catch (error) {
		errorMessage.value = extractErrorMessage(error, __("لغو سند ناموفق بود."))
	} finally {
		cancelling.value = false
	}
}

async function uploadSelectedFiles(entryName, doctype) {
	const uploaded = []
	for (const file of selectedFiles.value) {
		const encoded = await readFileAsDataUrl(file)
		const attachment = await submitResource(attachImageResource, {
			name: entryName,
			doctype: doctype || editingDoctype.value || "Payment Entry",
			file_name: file.name,
			file_content: encoded,
		})
		uploaded.push(attachment)
	}
	existingAttachments.value = [...uploaded, ...existingAttachments.value]
	selectedFiles.value = []
}

function readFileAsDataUrl(file) {
	return new Promise((resolve, reject) => {
		const reader = new FileReader()
		reader.onload = () => resolve(reader.result)
		reader.onerror = () => reject(new Error(__("خطا در خواندن فایل")))
		reader.readAsDataURL(file)
	})
}

function submitResource(resource, params) {
	return new Promise((resolve, reject) => {
		resource.submit(params, {
			onSuccess(data) {
				resolve(data)
			},
			onError(error) {
				reject(error)
			},
		})
	})
}

function getAccountFiltersFromQuery() {
	const allowedSet = new Set((allowedAccounts.value || []).map((row) => row.account))
	const result = []

	if (route.query.accounts) {
		try {
			const parsed = JSON.parse(String(route.query.accounts))
			if (Array.isArray(parsed)) {
				for (const account of parsed) {
					const normalized = String(account || "").trim()
					if (normalized && allowedSet.has(normalized) && !result.includes(normalized)) {
						result.push(normalized)
					}
				}
			}
		} catch (_) {
			// ignore invalid query
		}
	}

	return result
}

onIonViewWillEnter(() => {
	// Ionic keeps pages alive, so refresh dropdown sources on each entry.
	ensureLookupResourcesLoaded(true)
	if (typeof contextResource.reload === "function") {
		contextResource.reload()
	} else {
		contextResource.fetch()
	}
	if (props.id && isImprestEnabled.value) {
		loadForEdit()
	}
})
</script>
