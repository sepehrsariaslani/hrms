<template>
	<BaseLayout :pageTitle="'داشبورد هماهنگ‌کننده غذا'">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-4">
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
					<router-link
						:to="plan?.name ? { name: 'MealPlanDetailView', params: { id: plan.name } } : { name: 'MealPlanFormView' }"
						v-slot="{ navigate }"
					>
							<Button @click="navigate" variant="solid" class="py-5 text-base w-full">
								ویرایش برنامه غذایی هفتگی
							</Button>
						</router-link>
						<router-link :to="{ name: 'MealsDashboard' }" v-slot="{ navigate }">
							<Button @click="navigate" variant="outline" class="py-5 text-base w-full">
								بازگشت به برنامه غذا
							</Button>
						</router-link>
					</div>

					<div class="bg-white rounded p-4 grid grid-cols-1 sm:grid-cols-3 gap-2 items-end">
						<div class="sm:col-span-2">
							<div class="text-sm text-gray-800 font-semibold">زمان پایان رزرو روزانه</div>
							<div class="text-xs text-gray-600 mt-1">
								کارمندان فقط تا این ساعت می‌توانند برای هر روز رزرو غذا ثبت کنند.
							</div>
							<div class="text-[11px] text-gray-500 mt-1">
								ساعت فعلی پایان رزرو: {{ cutoffTimeLabel }}
							</div>
						</div>
					<div class="grid grid-cols-2 gap-2">
						<input
							v-model="cutoffInput"
							type="time"
							class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
						/>
						<Button
							variant="solid"
							:loading="cutoffResource.loading"
							:disabled="!cutoffInput"
							@click="saveCutoffSettings"
							>
								ذخیره
							</Button>
						</div>
					</div>

					<div v-if="!plan" class="bg-white rounded p-4 text-sm text-gray-600">
						برای این هفته هنوز برنامه غذایی منتشر نشده است.
					</div>

					<template v-else>
						<div class="bg-white rounded p-4">
							<div class="text-sm text-gray-800 font-semibold">
								خلاصه تقاضای غذا
							</div>
							<div class="text-xs text-gray-600 mt-1">
								تعداد کل کارمندان فعال: {{ toPersianDigits(totalEmployees) }}
							</div>
							<div class="mt-1 text-xs text-blue-700">
								مجموع ثبت‌نام‌ها: {{ toPersianDigits(totalSignups) }}
							</div>
						<div class="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
							<select
								v-model="selectedDate"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 w-full"
							>
								<option
									v-for="row in summaryRows"
									:key="row.meal_date"
									:value="row.meal_date"
								>
									{{ formatJalaliDateShort(row.meal_date) }} - {{ row.meal_title }}
								</option>
							</select>
								<select
									v-model="statusFilter"
									class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 w-full"
								>
									<option value="registered">فقط رزرو/تحویل‌شده</option>
									<option value="all">همه وضعیت‌ها</option>
								</select>
							</div>
						</div>

						<div v-if="currentSummary" class="grid grid-cols-3 gap-2">
							<div class="bg-white rounded p-3 text-center">
								<div class="text-xs text-gray-500">رزرو شده</div>
								<div class="text-lg font-semibold text-blue-700">
									{{ toPersianDigits(currentSummary.reserved_count) }}
								</div>
							</div>
							<div class="bg-white rounded p-3 text-center">
								<div class="text-xs text-gray-500">تحویل شده</div>
								<div class="text-lg font-semibold text-green-700">
									{{ toPersianDigits(currentSummary.delivered_count) }}
								</div>
							</div>
							<div class="bg-white rounded p-3 text-center">
								<div class="text-xs text-gray-500">نیاز ندارد</div>
								<div class="text-lg font-semibold text-gray-700">
									{{ toPersianDigits(currentSummary.not_required_count) }}
								</div>
						</div>
					</div>

					<div class="bg-white rounded border border-gray-200 divide-y">
						<div
							v-for="row in filteredReservations"
							:key="row.name"
							class="p-3 flex items-center justify-between gap-3"
						>
							<div>
								<div class="text-sm font-medium text-gray-900">
									{{ row.employee_name || row.employee }}
									</div>
									<div class="text-xs text-gray-500 mt-1">
										{{ row.meal_title || '-' }} · {{ getReservationStatusLabel(row.reservation_status) }}
									</div>
								</div>
								<div class="flex items-center gap-2">
								<Button
									v-if="row.reservation_status === 'Reserved'"
									variant="solid"
										:loading="deliveryResource.loading"
										@click="markDelivery(row, 1)"
									>
										ثبت تحویل
									</Button>
									<Button
										v-else-if="row.reservation_status === 'Delivered'"
									variant="outline"
										:loading="deliveryResource.loading"
										@click="markDelivery(row, 0)"
									>
										لغو تحویل
									</Button>
								</div>
							</div>
							<div v-if="!filteredReservations.length" class="p-4 text-sm text-gray-500 text-center">
								برای تاریخ انتخاب‌شده رزروی پیدا نشد.
							</div>
						</div>
					</template>

				<ErrorMessage :message="errorMessage" />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { createResource, ErrorMessage, toast } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import { formatJalaliDateShort, toPersianDigits } from "@/utils/jalali"

const selectedDate = ref("")
const statusFilter = ref("registered")
const cutoffInput = ref("10:00")
const summaryRows = ref([])
const reservations = ref([])
const totalEmployees = ref(0)
const errorMessage = ref("")

const contextResource = createResource({
	url: "hrms.api.meal.get_meal_plan_context",
	auto: true,
	cache: "hrms:meal_coordinator_context",
	onSuccess(data) {
		cutoffInput.value = normalizeTimeInput(data?.plan?.cutoff_time || data?.default_cutoff_time || "10:00:00")
		if (data?.plan?.name) {
			loadSummary(data.plan.name)
		}
	},
})

const summaryResource = createResource({
	url: "hrms.api.meal.get_meal_demand_summary",
	auto: false,
})

const reservationResource = createResource({
	url: "hrms.api.meal.list_company_meal_reservations",
	auto: false,
})

const deliveryResource = createResource({
	url: "hrms.api.meal.mark_meal_delivery",
	auto: false,
})

const cutoffResource = createResource({
	url: "hrms.api.meal.update_meal_cutoff_settings",
	auto: false,
})

const context = computed(() => contextResource.data || {})
const plan = computed(() => context.value.plan || null)
const cutoffTimeLabel = computed(() => {
	const raw = String(plan.value?.cutoff_time || context.value.default_cutoff_time || "")
	return raw ? raw.slice(0, 5) : "-"
})
const currentSummary = computed(() =>
	summaryRows.value.find((row) => row.meal_date === selectedDate.value)
)
const totalSignups = computed(() => {
	return summaryRows.value.reduce((sum, row) => sum + Number(row.total_requests || 0), 0)
})
const filteredReservations = computed(() => {
	if (statusFilter.value === "all") return reservations.value
	return reservations.value.filter(
		(row) => row.reservation_status === "Reserved" || row.reservation_status === "Delivered"
	)
})

watch(selectedDate, (value) => {
	if (!value || !plan.value?.name) return
	loadReservations(plan.value.name, value)
})

function loadSummary(planName) {
	errorMessage.value = ""
	summaryResource.fetch(
		{
			plan_name: planName,
		},
		{
			onSuccess(data) {
				summaryRows.value = data?.summary || []
				totalEmployees.value = Number(data?.total_active_employees || 0)
				if (!selectedDate.value && summaryRows.value.length) {
					selectedDate.value = summaryRows.value[0].meal_date
				} else if (selectedDate.value) {
					loadReservations(planName, selectedDate.value)
				}
				},
				onError(error) {
					errorMessage.value = extractErrorMessage(error, "بارگذاری خلاصه تقاضای غذا ناموفق بود.")
				},
			}
		)
}

function loadReservations(planName, mealDate) {
	reservationResource.fetch(
		{
			plan_name: planName,
			meal_date: mealDate,
		},
			{
				onSuccess(data) {
					reservations.value = data || []
				},
				onError(error) {
					errorMessage.value = extractErrorMessage(error, "بارگذاری رزروها ناموفق بود.")
				},
			}
		)
}

function markDelivery(row, delivered) {
	if (!plan.value?.name) return
	errorMessage.value = ""
	deliveryResource.submit(
		{
			plan_name: plan.value.name,
			meal_date: row.reservation_date,
			employee: row.employee,
			delivered,
		},
			{
				onSuccess() {
					loadSummary(plan.value.name)
					loadReservations(plan.value.name, selectedDate.value)
					toast({
						title: "موفق",
						text: "وضعیت تحویل غذا به‌روزرسانی شد.",
						icon: "check-circle",
						position: "bottom-center",
						iconClasses: "text-green-500",
					})
				},
				onError(error) {
					errorMessage.value = extractErrorMessage(error, "به‌روزرسانی وضعیت تحویل ناموفق بود.")
				},
			}
		)
}

function saveCutoffSettings() {
	if (!cutoffInput.value) return
	errorMessage.value = ""

	const payload = {
		cutoff_time: normalizeTimePayload(cutoffInput.value),
		company: context.value.company,
		apply_to_company_default: 1,
	}
	if (plan.value?.name) {
		payload.plan_name = plan.value.name
	}

	cutoffResource.submit(payload, {
			onSuccess() {
				contextResource.reload()
				if (plan.value?.name) {
				loadSummary(plan.value.name)
				if (selectedDate.value) {
					loadReservations(plan.value.name, selectedDate.value)
				}
				}
				toast({
					title: "موفق",
					text: "تنظیمات زمان پایان رزرو به‌روزرسانی شد.",
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			},
			onError(error) {
				errorMessage.value = extractErrorMessage(error, "به‌روزرسانی تنظیمات زمان رزرو ناموفق بود.")
			},
		})
	}

function getReservationStatusLabel(status) {
	const normalized = String(status || "").trim()
	if (normalized === "Reserved") return "رزرو شده"
	if (normalized === "Delivered") return "تحویل شده"
	if (normalized === "Not Required") return "نیاز ندارد"
	return normalized || "-"
}

function normalizeTimeInput(value) {
	return String(value || "10:00:00").slice(0, 5)
}

function normalizeTimePayload(value) {
	const normalized = String(value || "10:00").trim()
	return normalized.length === 5 ? `${normalized}:00` : normalized
}

function extractErrorMessage(error, fallbackMessage) {
	if (Array.isArray(error?.messages) && error.messages.length) return error.messages[0]
	if (typeof error?.message === "string" && error.message.trim()) return error.message
	return fallbackMessage
}
</script>
