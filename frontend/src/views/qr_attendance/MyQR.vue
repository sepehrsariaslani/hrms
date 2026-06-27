<template>
	<BaseLayout :pageTitle="__('کد QR من')">
		<template #body>
			<div class="flex flex-col items-center my-7 p-4">
				<div class="flex flex-col w-full max-w-md bg-white rounded-lg py-6 px-5 gap-5">

					<!-- Header -->
					<div class="text-center">
						<h1 class="text-xl font-bold text-gray-800 mb-1">{{ __('کد QR شخصی') }}</h1>
						<p class="text-gray-500 text-sm">{{ __('این کد را برای ثبت ورود/خروج نشان دهید') }}</p>
					</div>

					<!-- Loading -->
					<div v-if="loading" class="flex flex-col items-center py-8">
						<div class="animate-spin rounded-full h-10 w-10 border-4 border-blue-500 border-t-transparent mb-3"></div>
						<p class="text-gray-500 text-sm">{{ __('در حال تولید کد QR...') }}</p>
					</div>

					<!-- Error -->
					<div v-else-if="error" class="text-center py-6">
						<div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-3">
							<svg class="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</div>
						<p class="text-red-600 mb-3">{{ error }}</p>
						<button @click="fetchQRPayload" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-sm">
							{{ __('تلاش مجدد') }}
						</button>
					</div>

					<!-- QR Content -->
					<div v-else-if="qrData" class="flex flex-col items-center">

						<!-- QR Image from backend -->
						<div v-if="qrImage" class="border-2 border-gray-200 rounded-xl p-3 bg-white shadow-sm mb-3">
							<img :src="qrImage" :alt="__('کد QR')" class="w-56 h-56" />
						</div>

						<!-- Employee name -->
						<p v-if="qrData.employee_name" class="text-lg font-semibold text-gray-800 mb-1">
							{{ qrData.employee_name }}
						</p>
						<p v-if="qrData.employee_id" class="text-sm text-gray-400 mb-4">
							{{ qrData.employee_id }}
						</p>

						<!-- Instruction -->
						<div class="w-full bg-blue-50 border border-blue-100 rounded-lg p-3 mb-4">
							<p class="text-blue-700 text-sm text-center leading-relaxed">
								{{ __('اسکن کنید برای ثبت ورود/خروج') }}
							</p>
						</div>

						<!-- QR URL text (collapsible) -->
						<div class="w-full">
							<button
								@click="showUrl = !showUrl"
								class="w-full text-xs text-gray-400 hover:text-gray-600 text-center py-1"
							>
								{{ showUrl ? __('بستن') : __('نمایش کد') }}
							</button>
							<div v-if="showUrl" class="bg-gray-100 rounded p-2 break-all">
								<code class="text-xs text-gray-600 select-all">{{ qrData.qr_url }}</code>
								<button
									@click="copyUrl"
									class="block mx-auto mt-2 text-xs text-blue-500 hover:text-blue-700"
								>
									{{ copied ? __('کپی شد!') : __('کپی') }}
								</button>
							</div>
						</div>

						<!-- Action buttons -->
						<div class="flex gap-2 mt-4 w-full">
							<button
								@click="fetchEmployeeQRImage"
								:disabled="imgLoading"
								class="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 text-sm"
							>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
								</svg>
								<span>{{ __('دانلود تصویر') }}</span>
							</button>
							<button
								@click="refreshQR"
								:disabled="loading"
								class="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 text-sm"
							>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
								</svg>
								<span>{{ __('تازه‌سازی') }}</span>
							</button>
						</div>

						<!-- Today status -->
						<div v-if="todayStatus !== null" class="w-full mt-4 pt-4 border-t">
							<div v-if="todayStatus.has_checkin" class="text-center">
								<p class="text-sm text-gray-500">{{ __('وضعیت امروز:') }}</p>
								<p class="text-sm font-medium" :class="statusColor">
									{{ statusText }}
								</p>
							</div>
							<div v-else class="text-center">
								<p class="text-sm text-gray-400">{{ __('امروز هنوز ثبت ورود ندارید') }}</p>
							</div>
						</div>
					</div>

					<!-- No data yet -->
					<div v-else class="text-center py-8">
						<div class="inline-block p-4 bg-gray-100 rounded-lg mb-4">
							<svg class="w-20 h-20 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
									d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
							</svg>
						</div>
						<p class="text-gray-400 mb-4">{{ __('برای دیدن کد QR خود دکمه زیر را بزنید') }}</p>
						<button @click="fetchQRPayload" class="px-6 py-2.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
							{{ __('نمایش کد QR') }}
						</button>
					</div>

					<ErrorMessage v-if="apiError" :message="apiError" class="mt-3" />
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { ref, computed, inject, onMounted } from "vue"
import { ErrorMessage } from "frappe-ui"
import BaseLayout from "@/components/BaseLayout.vue"

const __ = inject("$translate")

const loading = ref(false)
const imgLoading = ref(false)
const error = ref("")
const apiError = ref("")
const qrData = ref(null)
const qrImage = ref("")
const showUrl = ref(false)
const copied = ref(false)
const todayStatus = ref(null)

const statusText = computed(() => {
	if (!todayStatus.value) return ""
	const action = todayStatus.value.last_action
	if (action === "Present") return __('حاضر')
	if (action === "Absent") return __('غایب')
	if (action === "On Leave") return __('در مرخصی')
	if (action === "Half Day") return __('نیم‌روز')
	if (action === "Work From Home") return __('دورکاری')
	return action || ""
})

const statusColor = computed(() => {
	if (!todayStatus.value) return "text-gray-600"
	const s = todayStatus.value.last_action
	if (s === "Present") return "text-green-600"
	if (s === "Absent") return "text-red-600"
	if (s === "On Leave") return "text-yellow-600"
	return "text-gray-600"
})

function getCSRFToken() {
	return window.csrf_token || ""
}

async function apiCall(method, params = {}) {
	const res = await fetch(`/api/method/${method}`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			"X-Frappe-CSRF-Token": getCSRFToken(),
		},
		body: JSON.stringify(params),
	})
	return res
}

async function fetchQRPayload() {
	loading.value = true
	error.value = ""
	apiError.value = ""
	qrData.value = null
	qrImage.value = ""

	try {
		const res = await apiCall("hrms.api.attendance.get_qr_payload")
		const data = await res.json()

		if (res.ok && data.message) {
			qrData.value = data.message
			await fetchEmployeeQRImage()
			await fetchTodayStatus()
		} else if (res.status === 417) {
			error.value = __('خطای پروکسی: لطفاً تنظیمات سرور را بررسی کنید')
		} else {
			error.value = data.message || data.exc || __('خطا در دریافت اطلاعات QR')
		}
	} catch (e) {
		error.value = __('خطا در ارتباط با سرور')
		console.error(e)
	} finally {
		loading.value = false
	}
}

async function fetchEmployeeQRImage() {
	imgLoading.value = true
	apiError.value = ""

	try {
		const res = await apiCall("hrms.api.qr_attendance.get_employee_qr_code")
		const data = await res.json()

		if (res.ok && data.message && data.message.qr_code) {
			qrImage.value = data.message.qr_code
		} else if (res.status === 417) {
			apiError.value = __('خطای پروکسی: لطفاً تنظیمات سرور را بررسی کنید (Expect header)')
		} else {
			apiError.value = data.message || data.exc || __('خطا در دریافت تصویر QR')
		}
	} catch (e) {
		apiError.value = __('خطا در ارتباط با سرور')
		console.error("Failed to fetch QR image:", e)
	} finally {
		imgLoading.value = false
	}
}

async function fetchTodayStatus() {
	try {
		const res = await apiCall("hrms.api.attendance.get_today_status")
		const data = await res.json()

		if (res.ok && data.message) {
			todayStatus.value = data.message
		}
	} catch (e) {
		console.error("Failed to fetch today status:", e)
	}
}

function refreshQR() {
	qrImage.value = ""
	fetchQRPayload()
}

function copyUrl() {
	if (qrData.value && qrData.value.qr_url) {
		navigator.clipboard.writeText(qrData.value.qr_url).then(() => {
			copied.value = true
			setTimeout(() => (copied.value = false), 2000)
		})
	}
}

onMounted(() => {
	fetchQRPayload()
})
</script>
