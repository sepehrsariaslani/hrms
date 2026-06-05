<template>
	<BaseLayout :pageTitle="pageTitle">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-4">
				<div class="rounded-xl border border-slate-100 bg-white p-4">
					<div class="mb-4 flex items-center justify-between">
						<div>
							<div class="text-sm font-semibold text-slate-900">{{ __('اطلاعات سفر') }}</div>
							<div class="mt-1 text-xs text-slate-500">{{ __('کد سفر') }}: {{ form.id || __('ثبت‌نشده') }}</div>
						</div>
						<span class="rounded-full px-2.5 py-1 text-[11px] font-semibold" :class="statusStyle">
							{{ form.status }}
						</span>
					</div>

					<div class="grid gap-3 sm:grid-cols-2">
						<div class="sm:col-span-2">
							<label class="mb-1 block text-xs text-slate-500">{{ __('عنوان سفر') }}</label>
							<input
								v-model="form.title"
								type="text"
								class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-amber-400"
								:placeholder="__('مثال: ماموریت بازدید از شعبه مرکزی')"
							/>
						</div>

						<div>
							<label class="mb-1 block text-xs text-slate-500">{{ __('نوع جریان سفر') }}</label>
							<SearchableDropdown
								v-model="form.flow_type"
								:options="flowTypeDropdownOptions"
								:placeholder="__('انتخاب نوع جریان سفر')"
							/>
						</div>

						<div>
							<label class="mb-1 block text-xs text-slate-500">{{ __('نوع ماموریت') }}</label>
							<SearchableDropdown
								v-model="form.mission_type"
								:options="missionTypeDropdownOptions"
								:placeholder="__('انتخاب نوع ماموریت')"
							/>
						</div>

						<div>
							<label class="mb-1 block text-xs text-slate-500">{{ __('مقصد') }}</label>
							<input
								v-model="form.destination"
								type="text"
								class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-amber-400"
								:placeholder="__('مثال: شیراز')"
							/>
						</div>

						<template v-if="isHourlyMission">
							<div>
								<label class="mb-1 block text-xs text-slate-500">{{ __('روز ماموریت ساعتی') }}</label>
								<JalaliDatePicker v-model="form.hourly_date" />
							</div>
							<div>
								<label class="mb-1 block text-xs text-slate-500">{{ __('از ساعت') }}</label>
								<input
									v-model="form.hourly_from_time"
									type="time"
									class="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-gray-500 focus:outline-none"
								/>
							</div>
							<div>
								<label class="mb-1 block text-xs text-slate-500">{{ __('تا ساعت') }}</label>
								<input
									v-model="form.hourly_to_time"
									type="time"
									class="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-gray-500 focus:outline-none"
								/>
							</div>
						</template>

						<template v-else>
							<div>
								<label class="mb-1 block text-xs text-slate-500">{{ __('تاریخ شروع') }}</label>
								<JalaliDatePicker v-model="form.start_date" />
							</div>
							<div>
								<label class="mb-1 block text-xs text-slate-500">{{ __('تاریخ پایان') }}</label>
								<JalaliDatePicker v-model="form.end_date" :minDate="form.start_date" />
							</div>
						</template>

						<div class="sm:col-span-2">
							<label class="mb-1 block text-xs text-slate-500">{{ __('مبلغ درخواستی/دریافتی سفر (ریال)') }}</label>
							<PersianNumberInput
								v-model="form.mission_allowance"
								:showWords="false"
								suffix="ریال"
								suffixPosition="right"
								inputClass="w-full px-4 py-3 rounded-lg border border-slate-200 bg-white text-gray-900 focus:ring-2 focus:ring-amber-500 focus:border-transparent text-base font-semibold"
							/>
						</div>

						<div class="sm:col-span-2">
							<label class="mb-1 block text-xs text-slate-500">{{ __('هدف سفر') }}</label>
							<textarea
								v-model="form.purpose"
								rows="3"
								class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-amber-400"
								:placeholder="__('دلیل این سفر و کارهایی که باید انجام شود')"
							></textarea>
						</div>

						<div class="sm:col-span-2">
							<label class="mb-1 block text-xs text-slate-500">{{ __('توضیحات') }}</label>
							<textarea
								v-model="form.notes"
								rows="3"
								class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-amber-400"
								:placeholder="__('هر توضیح تکمیلی برای سرپرست یا حسابداری')"
							></textarea>
						</div>
					</div>
				</div>

				<div class="rounded-xl border border-slate-100 bg-white p-4">
					<div class="mb-2 text-sm font-semibold text-slate-900">{{ __('گردش کار سفر') }}</div>
					<div class="text-xs text-slate-500">{{ workflowHint }}</div>
					<div class="mt-3 flex flex-wrap gap-2">
						<Button
							v-for="action in topWorkflowActions"
							:key="action.id"
							:variant="action.variant"
							:theme="action.theme"
							class="!text-xs !px-3 !py-2"
							:loading="actionLoading"
							@click="applyWorkflowAction(action)"
						>
							{{ action.label }}
						</Button>
					</div>
				</div>

				<div class="rounded-xl border border-slate-100 bg-white p-4">
					<div class="mb-3 text-sm font-semibold text-slate-900">{{ __('ثبت هزینه سفر') }}</div>
					<div class="grid gap-3 sm:grid-cols-2">
						<div>
							<label class="mb-1 block text-xs text-slate-500">{{ __('تاریخ') }}</label>
							<JalaliDatePicker v-model="expenseDraft.date" />
						</div>
						<div>
							<label class="mb-1 block text-xs text-slate-500">{{ __('نوع هزینه') }}</label>
							<SearchableDropdown
								v-model="expenseDraft.category"
								:options="expenseTypeDropdownOptions"
								:placeholder="__('انتخاب نوع هزینه')"
							/>
						</div>
						<div class="sm:col-span-2">
							<label class="mb-1 block text-xs text-slate-500">{{ __('شرح هزینه') }}</label>
							<input
								v-model="expenseDraft.description"
								type="text"
								class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-amber-400"
								:placeholder="__('مثال: بلیط رفت، اقامت، حمل‌ونقل درون‌شهری')"
							/>
						</div>
						<div class="sm:col-span-2">
							<label class="mb-1 block text-xs text-slate-500">{{ __('مبلغ هزینه (ریال)') }}</label>
							<PersianNumberInput
								v-model="expenseDraft.amount"
								:showWords="false"
								suffix="ریال"
								suffixPosition="right"
								inputClass="w-full px-4 py-3 rounded-lg border border-slate-200 bg-white text-gray-900 focus:ring-2 focus:ring-amber-500 focus:border-transparent text-base font-semibold"
							/>
						</div>
							<div class="sm:col-span-2">
								<AttachmentDropzone
									v-model="selectedExpenseFiles"
									:existing-files="editingExpenseExistingFiles"
								:label="__('عکس رسید هزینه')"
								accept="image/*"
								:multiple="false"
									:max-file-size-m-b="5"
									@error="onExpenseAttachmentError"
								/>
								<div class="mt-1 text-[11px] text-slate-500">
									{{ __('رسید هزینه بعد از ذخیره سفر به‌صورت خودکار آپلود می‌شود.') }}
								</div>
							</div>
						<div class="sm:col-span-2">
							<Button class="w-full py-4" @click="addExpense">
								{{ editingExpenseId ? __('ثبت ویرایش هزینه') : __('افزودن هزینه') }}
							</Button>
							<div v-if="editingExpenseId" class="mt-2">
								<Button variant="ghost" class="w-full py-3" @click="cancelExpenseEdit">
									{{ __('لغو ویرایش هزینه') }}
								</Button>
							</div>
						</div>
					</div>
				</div>

				<div class="rounded-xl border border-slate-100 bg-white p-4">
					<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
						<div class="text-sm font-semibold text-slate-900">{{ __('ریز هزینه‌های سفر') }}</div>
						<div class="text-xs text-slate-500">{{ __('جمع ثبت‌شده') }}: {{ formatAmount(totalExpense) }}</div>
					</div>

					<div v-if="form.expenses.length" class="overflow-x-auto">
						<table class="w-full min-w-[560px] text-right text-xs">
							<thead>
								<tr class="border-b border-slate-100 text-slate-500">
									<th class="py-2 font-medium">{{ __('تاریخ') }}</th>
									<th class="py-2 font-medium">{{ __('نوع هزینه') }}</th>
									<th class="py-2 font-medium">{{ __('شرح') }}</th>
									<th class="py-2 font-medium">{{ __('مبلغ') }}</th>
									<th class="py-2 font-medium">{{ __('رسید') }}</th>
									<th class="py-2 font-medium">{{ __('عملیات') }}</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="expense in form.expenses" :key="expense.id" class="border-b border-slate-50 last:border-b-0">
									<td class="py-2 text-slate-700">{{ formatJalaliDateShort(expense.date) }}</td>
									<td class="py-2 text-slate-700">{{ expenseLabel(expense.category) }}</td>
									<td class="py-2 text-slate-700">{{ expense.description }}</td>
									<td class="py-2 font-semibold text-slate-800">{{ formatAmount(expense.amount) }}</td>
									<td class="py-2 text-[11px]">
										<a
											v-if="expense.receipt_file_url"
											:href="expense.receipt_file_url"
											target="_blank"
											rel="noopener noreferrer"
											class="font-medium text-amber-700 underline"
										>
											{{ __('مشاهده رسید') }}
										</a>
										<span v-else-if="hasPendingExpenseReceipt(expense.id)" class="text-blue-600">
											{{ __('در انتظار آپلود') }}
										</span>
										<span v-else class="text-slate-400">—</span>
									</td>
									<td class="py-2">
										<div class="flex flex-wrap gap-1">
											<button
												type="button"
												class="rounded-md bg-amber-50 px-2 py-1 text-amber-700 transition hover:bg-amber-100"
												@click="editExpense(expense.id)"
											>
												{{ __('ویرایش') }}
											</button>
											<button
												type="button"
												class="rounded-md bg-rose-50 px-2 py-1 text-rose-700 transition hover:bg-rose-100"
												@click="removeExpense(expense.id)"
											>
												{{ __('حذف') }}
											</button>
										</div>
									</td>
								</tr>
							</tbody>
						</table>
					</div>
					<EmptyState v-else :message="__('هنوز هزینه‌ای برای این سفر ثبت نشده است')" />
				</div>

				<div class="rounded-xl border border-slate-100 bg-white p-4">
					<div class="grid grid-cols-1 gap-3 text-sm sm:grid-cols-3">
						<div>
							<div class="text-slate-500">{{ __('مبلغ دریافتی/درخواستی') }}</div>
							<div class="mt-1 font-semibold text-slate-800">{{ formatAmount(form.mission_allowance) }}</div>
						</div>
						<div>
							<div class="text-slate-500">{{ __('جمع هزینه') }}</div>
							<div class="mt-1 font-semibold text-slate-800">{{ formatAmount(totalExpense) }}</div>
						</div>
						<div>
							<div class="text-slate-500">{{ __('اختلاف') }}</div>
							<div class="mt-1 font-semibold" :class="remainingBudget >= 0 ? 'text-emerald-700' : 'text-rose-700'">
								{{ formatSignedAmount(remainingBudget) }}
							</div>
						</div>
					</div>
				</div>

				<div class="rounded-xl border p-4" :class="isSupervisorApproved ? settlementClass : 'border-slate-100 bg-white'">
					<div class="text-sm font-semibold text-slate-900">{{ __('نتیجه تسویه پس از تایید نهایی') }}</div>
					<div v-if="isSupervisorApproved" class="mt-2 text-sm" :class="settlementTextClass">
						{{ settlementResult.message }}
					</div>
					<div v-else class="mt-2 text-xs text-slate-500">
						{{ __('پس از تایید نهایی سرپرست، بدهکار/بستانکار بودن به‌صورت خودکار ثبت می‌شود.') }}
					</div>
					<div v-if="form.linked_expense_claim" class="mt-2 text-xs text-slate-600">
						{{ __('سند هزینه ایجادشده') }}: {{ form.linked_expense_claim }}
					</div>
				</div>

				<div v-if="errorMessage" class="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ errorMessage }}</div>
				<div v-if="successMessage" class="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{{ successMessage }}</div>

				<div v-if="bottomCompleteAction" class="rounded-xl p-3 hr-accent-soft hr-accent-border">
					<div class="mb-2 text-xs hr-accent-text">
						{{ __('پس از ثبت تمام هزینه‌ها، سفر را تکمیل کنید تا برای بررسی سرپرست ارسال شود.') }}
					</div>
					<Button
						class="w-full py-5"
						variant="solid"
						theme="amber"
						:loading="actionLoading"
						@click="applyWorkflowAction(bottomCompleteAction)"
					>
						{{ bottomCompleteAction.label }}
					</Button>
				</div>

				<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
					<Button variant="outline" class="w-full py-5" @click="goToList">{{ __('بازگشت به فهرست سفرها') }}</Button>
					<Button class="w-full py-5" :loading="saveLoading" @click="saveMission()">{{ isExisting ? __('ذخیره تغییرات') : __('ذخیره سفر') }}</Button>
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, reactive, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"

import BaseLayout from "@/components/BaseLayout.vue"
import AttachmentDropzone from "@/components/AttachmentDropzone.vue"
import JalaliDatePicker from "@/components/JalaliDatePicker.vue"
import PersianNumberInput from "@/components/PersianNumberInput.vue"
import SearchableDropdown from "@/components/SearchableDropdown.vue"
import {
	attachMissionExpenseImage,
	applyMissionAction,
	buildMissionDraft,
	calculateMissionSettlement,
	expenseTypeOptions,
	fetchMissionById,
	getMissionById,
	missionFlowTypeOptions,
	missionTypeOptions,
	upsertMission,
} from "@/data/missions"
import { employeeResource } from "@/data/employee"
import { formatGregorianDate, formatJalaliDateShort, toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")

const route = useRoute()
const router = useRouter()

const form = reactive(buildMissionDraft())
const expenseDraft = reactive(createEmptyExpense())
const selectedExpenseFiles = ref([])
const pendingExpenseFiles = ref({})

const errorMessage = ref("")
const successMessage = ref("")
const saveLoading = ref(false)
const actionLoading = ref(false)
const initialDateFromQuery = computed(() => {
	const queryDate = String(route.query?.date || "")
	return /^\d{4}-\d{2}-\d{2}$/.test(queryDate) ? queryDate : ""
})

const isExisting = computed(() => Boolean(route.params.id))
const isHourlyMission = computed(() => form.mission_type === "ساعتی")
const isSupervisorApproved = computed(() => form.status === "تایید نهایی سرپرست")
const editingExpenseId = ref("")

const currentEmployeeName = computed(() => employeeResource.data?.name || "")
const isOwner = computed(() => Boolean(form.employee && form.employee === currentEmployeeName.value))
const isSupervisorReviewer = computed(() => Boolean(form.can_review && form.supervisor_employee === currentEmployeeName.value))

const pageTitle = computed(() => (isExisting.value ? __("جزئیات سفر") : __("ثبت سفر")))

const flowTypeDropdownOptions = missionFlowTypeOptions.map((item) => ({ label: item, value: item }))
const missionTypeDropdownOptions = missionTypeOptions.map((item) => ({ label: item, value: item }))

const expenseTypeDropdownOptions = computed(() => {
	if (expenseTypeOptions.value.length) return expenseTypeOptions.value
	return [{ label: __("ابتدا نوع هزینه تعریف کنید"), value: "" }]
})

const statusClassMap = {
	"در انتظار تایید برنامه سفر": "bg-blue-100 text-blue-700",
	"تایید برنامه سفر": "bg-sky-100 text-sky-700",
	"در حال انجام سفر": "bg-amber-100 text-amber-700",
	"در انتظار تایید نهایی سرپرست": "bg-indigo-100 text-indigo-700",
	"نیازمند اصلاح": "bg-orange-100 text-orange-700",
	"تایید نهایی سرپرست": "bg-emerald-100 text-emerald-700",
	ردشده: "bg-rose-100 text-rose-700",
}

const statusStyle = computed(() => statusClassMap[form.status] || "bg-slate-100 text-slate-700")

const totalExpense = computed(() =>
	(form.expenses || []).reduce((total, item) => total + normalizeAmount(item.amount), 0)
)

const remainingBudget = computed(
	() => normalizeAmount(form.mission_allowance) - normalizeAmount(totalExpense.value)
)

const settlementResult = computed(() => {
	if (form.settlement_message) {
		return {
			type: form.settlement_type,
			amount: normalizeAmount(form.settlement_amount),
			message: form.settlement_message,
		}
	}
	return calculateMissionSettlement(form.mission_allowance, totalExpense.value, form.status)
})

const settlementClass = computed(() => {
	if (settlementResult.value.type === "company_debt") return "border-emerald-200 bg-emerald-50"
	if (settlementResult.value.type === "employee_debt") return "border-rose-200 bg-rose-50"
	return "border-sky-200 bg-sky-50"
})

const settlementTextClass = computed(() => {
	if (settlementResult.value.type === "company_debt") return "text-emerald-700"
	if (settlementResult.value.type === "employee_debt") return "text-rose-700"
	return "text-sky-700"
})

const workflowHint = computed(() => {
	if (form.status === "در انتظار تایید برنامه سفر") {
		return __("این سفر برنامه‌ریزی‌شده است و باید ابتدا توسط سرپرست تایید شود.")
	}
	if (form.status === "تایید برنامه سفر") {
		return __("برنامه سفر تایید شده و کارمند می‌تواند سفر را شروع کند.")
	}
	if (form.status === "در حال انجام سفر") {
		return __("کارمند می‌تواند هر بار هزینه جدید اضافه کند و در پایان سفر آن را تکمیل کند.")
	}
	if (form.status === "در انتظار تایید نهایی سرپرست") {
		return __("سفر تکمیل شده و منتظر بررسی نهایی سرپرست است.")
	}
	if (form.status === "نیازمند اصلاح") {
		return __("سرپرست نیاز به اصلاح اعلام کرده است. پس از اصلاح، مجدد ارسال کنید.")
	}
	if (form.status === "تایید نهایی سرپرست") {
		return __("سرپرست سفر را تایید نهایی کرده و اسناد هزینه ثبت شده‌اند.")
	}
	return __("سفر در وضعیت رد شده قرار دارد.")
})

const workflowActions = computed(() => {
	const actions = []

	if (isOwner.value) {
		if (form.status === "تایید برنامه سفر") {
			actions.push({
				id: "start_trip",
				label: __("شروع سفر"),
				variant: "solid",
				theme: "amber",
				requiresValidation: true,
				saveBeforeAction: true,
			})
		}
		if (form.status === "در حال انجام سفر") {
			actions.push({
				id: "complete_trip",
				label: __("تکمیل سفر"),
				variant: "solid",
				theme: "amber",
				requiresValidation: true,
				saveBeforeAction: true,
				confirmText: __("آیا مطمئن هستید سفر شما تمام شده و برای بررسی سرپرست ارسال شود؟"),
			})
		}
		if (form.status === "نیازمند اصلاح") {
			actions.push({
				id: "resubmit_after_edit",
				label: __("ارسال مجدد برای تایید نهایی"),
				variant: "solid",
				theme: "blue",
				requiresValidation: true,
				saveBeforeAction: true,
			})
		}
	}

	if (isSupervisorReviewer.value) {
		if (form.status === "در انتظار تایید برنامه سفر") {
			actions.push(
				{
					id: "approve_plan",
					label: __("تایید برنامه سفر"),
					variant: "solid",
					theme: "green",
					requiresValidation: false,
					saveBeforeAction: true,
				},
				{
					id: "reject_plan",
					label: __("رد برنامه سفر"),
					variant: "subtle",
					theme: "red",
					requiresValidation: false,
					saveBeforeAction: false,
				}
			)
		}
		if (form.status === "در انتظار تایید نهایی سرپرست") {
			actions.push(
				{
					id: "approve_final",
					label: __("تایید نهایی سرپرست"),
					variant: "solid",
					theme: "green",
					requiresValidation: false,
					saveBeforeAction: true,
				},
				{
					id: "send_for_correction",
					label: __("برگشت برای اصلاح"),
					variant: "outline",
					theme: "gray",
					requiresValidation: false,
					saveBeforeAction: false,
				},
				{
					id: "reject_final",
					label: __("رد نهایی"),
					variant: "subtle",
					theme: "red",
					requiresValidation: false,
					saveBeforeAction: false,
				}
			)
		}
	}

	return actions
})

const topWorkflowActions = computed(() =>
	workflowActions.value.filter((action) => action.id !== "complete_trip")
)

const bottomCompleteAction = computed(
	() => workflowActions.value.find((action) => action.id === "complete_trip") || null
)

const editingExpenseExistingFiles = computed(() => {
	if (!editingExpenseId.value) return []
	const editingExpense = (form.expenses || []).find((expense) => expense.id === editingExpenseId.value)
	if (!editingExpense?.receipt_file_url) return []
	return [
		{
			name: editingExpense.receipt_file || editingExpense.id,
			file_name: editingExpense.receipt_file || __("رسید هزینه"),
			file_url: editingExpense.receipt_file_url,
		},
	]
})

watch(
	() => route.params.id,
	() => {
		loadMission()
	},
	{ immediate: true }
)

watch(
	() => expenseTypeOptions.value,
	(options) => {
		if (!expenseDraft.category && options.length) {
			expenseDraft.category = options[0].value
		}
	},
	{ immediate: true, deep: true }
)

watch(
	() => form.flow_type,
	(value) => {
		if (!value || isExisting.value) return
		if (value === "برنامه‌ریزی‌شده") {
			form.status = "در انتظار تایید برنامه سفر"
		} else if (value === "بدون برنامه‌ریزی") {
			form.status = "در حال انجام سفر"
		}
	}
)

watch(
	() => form.mission_type,
	(value) => {
		if (value === "ساعتی") {
			form.hourly_date = form.hourly_date || form.start_date || formatGregorianDate(new Date())
			form.start_date = form.hourly_date
			form.end_date = form.hourly_date
			return
		}

		if (!form.start_date) form.start_date = formatGregorianDate(new Date())
		if (!form.end_date) form.end_date = form.start_date
		form.hourly_from_time = ""
		form.hourly_to_time = ""
	},
	{ immediate: true }
)

watch(
	() => form.hourly_date,
	(value) => {
		if (!isHourlyMission.value || !value) return
		form.start_date = value
		form.end_date = value
	}
)

watch(
	() => route.query?.date,
	(value) => {
		if (isExisting.value) return
		const queryDate = String(value || "")
		if (!/^\d{4}-\d{2}-\d{2}$/.test(queryDate)) return
		form.start_date = queryDate
		form.end_date = queryDate
		form.hourly_date = queryDate
	},
	{ immediate: true }
)

function createEmptyExpense() {
	return {
		date: formatGregorianDate(new Date()),
		category: "",
		description: "",
		amount: 0,
		receipt_file: "",
		receipt_file_url: "",
	}
}

function setMessage(type, text) {
	errorMessage.value = type === "error" ? text : ""
	successMessage.value = type === "success" ? text : ""
}

function assignMissionData(sourceMission, options = {}) {
	const { keepPendingExpenseFiles = false } = options
	const normalized = buildMissionDraft(sourceMission)
	Object.keys(form).forEach((key) => {
		delete form[key]
	})
	Object.assign(form, normalized)
	form.expenses = [...(normalized.expenses || [])]
	Object.assign(expenseDraft, createEmptyExpense())
	editingExpenseId.value = ""
	selectedExpenseFiles.value = []
	if (!keepPendingExpenseFiles) {
		pendingExpenseFiles.value = {}
	}
}

async function loadMission() {
	setMessage("success", "")
	setMessage("error", "")

	const missionId = String(route.params.id || "")
	if (!missionId) {
		const selectedDate = initialDateFromQuery.value
		assignMissionData(
			buildMissionDraft(
				selectedDate
					? { start_date: selectedDate, end_date: selectedDate, hourly_date: selectedDate }
					: {}
			)
		)
		return
	}

	const localMission = getMissionById(missionId)
	if (localMission) {
		assignMissionData(localMission)
		return
	}

	try {
		const remoteMission = await fetchMissionById(missionId)
		assignMissionData(remoteMission)
	} catch (error) {
		assignMissionData(buildMissionDraft())
		setMessage("error", error?.message || __("سفر انتخاب‌شده پیدا نشد."))
	}
}

function normalizeAmount(value) {
	if (typeof value === "number") return Number.isFinite(value) ? value : 0
	if (value === null || value === undefined) return 0
	const englishDigits = String(value).replace(/[۰-۹]/g, (digit) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit)))
	const cleaned = englishDigits.replace(/[,\u066C]/g, "").trim()
	const parsed = Number(cleaned)
	return Number.isFinite(parsed) ? parsed : 0
}

function formatAmount(value) {
	const amount = Math.round(normalizeAmount(value))
	return `${toPersianDigits(new Intl.NumberFormat("en-US").format(amount))} ${__("ریال")}`
}

function formatSignedAmount(value) {
	const amount = normalizeAmount(value)
	const prefix = amount < 0 ? "-" : "+"
	return `${prefix}${formatAmount(Math.abs(amount))}`
}

function expenseLabel(value) {
	const option = expenseTypeOptions.value.find((entry) => String(entry.value) === String(value))
	return option?.label || value || "-"
}

function hasPendingExpenseReceipt(expenseId) {
	return Boolean(pendingExpenseFiles.value?.[expenseId])
}

function onExpenseAttachmentError(message) {
	setMessage("error", message || __("آپلود فایل با خطا مواجه شد."))
}

function addExpense() {
	setMessage("success", "")
	setMessage("error", "")

	if (!expenseDraft.category) {
		setMessage("error", __("نوع هزینه را انتخاب کنید."))
		return
	}
	if (!expenseDraft.description.trim()) {
		setMessage("error", __("برای هزینه، شرح وارد کنید."))
		return
	}

	const amount = normalizeAmount(expenseDraft.amount)
	if (!amount || amount <= 0) {
		setMessage("error", __("مبلغ هزینه باید بیشتر از صفر باشد."))
		return
	}

	const baseExpense = {
		date: expenseDraft.date || formatGregorianDate(new Date()),
		category: expenseDraft.category,
		description: expenseDraft.description.trim(),
		amount,
		receipt_file: expenseDraft.receipt_file || "",
		receipt_file_url: expenseDraft.receipt_file_url || "",
	}
	const selectedReceiptFile = selectedExpenseFiles.value?.[0] || null
	if (editingExpenseId.value) {
		form.expenses = (form.expenses || []).map((expense) =>
			expense.id === editingExpenseId.value ? { ...expense, ...baseExpense } : expense
		)
		if (selectedReceiptFile) {
			pendingExpenseFiles.value = {
				...pendingExpenseFiles.value,
				[editingExpenseId.value]: selectedReceiptFile,
			}
			form.expenses = (form.expenses || []).map((expense) =>
				expense.id === editingExpenseId.value
					? { ...expense, receipt_file: "", receipt_file_url: "" }
					: expense
			)
		}
		setMessage("success", __("هزینه سفر ویرایش شد."))
	} else {
		const expenseId = `MEX-${Date.now().toString(36).toUpperCase()}`
		const nextExpense = {
			id: expenseId,
			...baseExpense,
		}
		form.expenses = [...(form.expenses || []), nextExpense]
		if (selectedReceiptFile) {
			pendingExpenseFiles.value = {
				...pendingExpenseFiles.value,
				[expenseId]: selectedReceiptFile,
			}
		}
		setMessage("success", __("هزینه سفر اضافه شد."))
	}
	Object.assign(expenseDraft, createEmptyExpense())
	editingExpenseId.value = ""
	selectedExpenseFiles.value = []
	if (expenseTypeOptions.value.length) {
		expenseDraft.category = expenseTypeOptions.value[0].value
	}
}

function removeExpense(expenseId) {
	if (editingExpenseId.value === expenseId) {
		Object.assign(expenseDraft, createEmptyExpense())
		editingExpenseId.value = ""
		selectedExpenseFiles.value = []
	}
	if (pendingExpenseFiles.value?.[expenseId]) {
		const nextPendingFiles = { ...pendingExpenseFiles.value }
		delete nextPendingFiles[expenseId]
		pendingExpenseFiles.value = nextPendingFiles
	}
	form.expenses = (form.expenses || []).filter((expense) => expense.id !== expenseId)
	setMessage("success", __("آیتم هزینه حذف شد."))
}

function editExpense(expenseId) {
	const targetExpense = (form.expenses || []).find((expense) => expense.id === expenseId)
	if (!targetExpense) return
	Object.assign(expenseDraft, {
		date: targetExpense.date || formatGregorianDate(new Date()),
		category: targetExpense.category || "",
		description: targetExpense.description || "",
		amount: normalizeAmount(targetExpense.amount),
		receipt_file: targetExpense.receipt_file || "",
		receipt_file_url: targetExpense.receipt_file_url || "",
	})
	editingExpenseId.value = expenseId
	selectedExpenseFiles.value = pendingExpenseFiles.value?.[expenseId]
		? [pendingExpenseFiles.value[expenseId]]
		: []
	setMessage("success", __("برای این هزینه حالت ویرایش فعال شد."))
}

function cancelExpenseEdit() {
	Object.assign(expenseDraft, createEmptyExpense())
	editingExpenseId.value = ""
	selectedExpenseFiles.value = []
	if (expenseTypeOptions.value.length) {
		expenseDraft.category = expenseTypeOptions.value[0].value
	}
}

function readFileAsDataUrl(file) {
	return new Promise((resolve, reject) => {
		const reader = new FileReader()
		reader.onload = () => resolve(reader.result)
		reader.onerror = () => reject(new Error(__("خطا در خواندن فایل")))
		reader.readAsDataURL(file)
	})
}

async function uploadPendingExpenseReceipts(missionId) {
	const entries = Object.entries(pendingExpenseFiles.value || {})
	if (!entries.length) return null

	for (const [expenseId, file] of entries) {
		if (!file) continue
		const encoded = await readFileAsDataUrl(file)
		await attachMissionExpenseImage(missionId, expenseId, file.name, encoded)
	}

	pendingExpenseFiles.value = {}
	const refreshedMission = await fetchMissionById(missionId)
	return refreshedMission
}

function parseTimeToMinutes(value) {
	if (!value) return Number.NaN
	const [hours, minutes] = String(value).split(":").map(Number)
	if (!Number.isFinite(hours) || !Number.isFinite(minutes)) return Number.NaN
	return hours * 60 + minutes
}

function validateMission() {
	if (!String(form.title || "").trim()) {
		setMessage("error", __("عنوان سفر الزامی است."))
		return false
	}
	if (!String(form.destination || "").trim()) {
		setMessage("error", __("مقصد سفر الزامی است."))
		return false
	}
	if (!String(form.purpose || "").trim()) {
		setMessage("error", __("هدف سفر را ثبت کنید."))
		return false
	}

	if (isHourlyMission.value) {
		if (!form.hourly_date) {
			setMessage("error", __("برای ماموریت ساعتی، روز ماموریت را انتخاب کنید."))
			return false
		}
		if (!form.hourly_from_time || !form.hourly_to_time) {
			setMessage("error", __("برای ماموریت ساعتی، ساعت شروع و پایان را کامل کنید."))
			return false
		}
		const fromMinutes = parseTimeToMinutes(form.hourly_from_time)
		const toMinutes = parseTimeToMinutes(form.hourly_to_time)
		if (!Number.isFinite(fromMinutes) || !Number.isFinite(toMinutes) || toMinutes <= fromMinutes) {
			setMessage("error", __("ساعت پایان باید بعد از ساعت شروع باشد."))
			return false
		}
		return true
	}

	if (!form.start_date || !form.end_date) {
		setMessage("error", __("تاریخ شروع و پایان سفر الزامی است."))
		return false
	}
	if (new Date(form.end_date).getTime() < new Date(form.start_date).getTime()) {
		setMessage("error", __("تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد."))
		return false
	}
	return true
}

async function saveMission(options = {}) {
	const { silent = false, skipValidation = false } = options
	setMessage("success", "")
	setMessage("error", "")

	if (!skipValidation && !validateMission()) return null

	const payload = {
		id: form.id || undefined,
		title: String(form.title || "").trim(),
		destination: String(form.destination || "").trim(),
		purpose: String(form.purpose || "").trim(),
		notes: String(form.notes || "").trim(),
		flow_type: form.flow_type,
		mission_type: form.mission_type,
		start_date: form.start_date,
		end_date: form.end_date,
		hourly_date: form.hourly_date,
		hourly_from_time: form.hourly_from_time,
		hourly_to_time: form.hourly_to_time,
		mission_allowance: normalizeAmount(form.mission_allowance),
		expenses: (form.expenses || []).map((expense) => ({
			id: expense.id,
			date: expense.date,
			category: expense.category,
			description: expense.description,
			amount: normalizeAmount(expense.amount),
			receipt_file: expense.receipt_file || "",
		})),
	}

	if (saveLoading.value && !silent) return null
	if (!silent) saveLoading.value = true

	try {
		const savedMission = await upsertMission(payload)
		const hasPendingReceipts = Object.keys(pendingExpenseFiles.value || {}).length > 0
		assignMissionData(savedMission, { keepPendingExpenseFiles: hasPendingReceipts })

		if (hasPendingReceipts) {
			const refreshedMission = await uploadPendingExpenseReceipts(savedMission.id)
			if (refreshedMission) {
				assignMissionData(refreshedMission)
			}
		}
		if (!silent) {
			setMessage("success", __("سفر با موفقیت ذخیره شد."))
		}
		if (!isExisting.value) {
			router.replace({ name: "MissionDetailView", params: { id: savedMission.id } })
		}
		return savedMission
	} catch (error) {
		setMessage("error", error?.message || __("ذخیره سفر ناموفق بود."))
		return null
	} finally {
		if (!silent) saveLoading.value = false
	}
}

async function applyWorkflowAction(action) {
	if (!action || actionLoading.value) return
	setMessage("success", "")
	setMessage("error", "")

	if (action.confirmText && !window.confirm(action.confirmText)) return
	if (action.requiresValidation && !validateMission()) return

	actionLoading.value = true
	try {
		let missionId = form.id
		if (action.saveBeforeAction || !missionId) {
			const savedMission = await saveMission({ silent: true, skipValidation: !action.requiresValidation })
			if (!savedMission?.id) return
			missionId = savedMission.id
		}

		const updatedMission = await applyMissionAction(missionId, action.id)
		assignMissionData(updatedMission)
		setMessage("success", __("وضعیت سفر به‌روزرسانی شد."))
	} catch (error) {
		setMessage("error", error?.message || __("اجرای عملیات گردش کار ناموفق بود."))
	} finally {
		actionLoading.value = false
	}
}

function goToList() {
	router.push({ name: "MissionListView" })
}
</script>
