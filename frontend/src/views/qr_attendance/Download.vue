<template>
	<BaseLayout :pageTitle="__('کد QR')">
		<template #body>
			<div class="flex flex-col items-center my-7 p-4">
				<div class="flex flex-col w-full max-w-md bg-white rounded-lg py-6 px-5 gap-5">

					<div class="text-center mb-2">
						<h1 class="text-xl font-bold text-gray-800 mb-1">{{ __('دانلود کد QR') }}</h1>
						<p class="text-gray-500 text-sm">{{ __('نوع کد QR را انتخاب کنید') }}</p>
					</div>

					<div class="flex flex-col gap-3">
						<!-- Company QR -->
						<button
							@click="downloadCompanyQR"
							:disabled="loading"
							class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
						>
							<svg v-if="!loading || mode !== 'company'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
							</svg>
							<div v-else class="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
							<span>{{ __('کد QR شرکت') }}</span>
						</button>
						<p class="text-xs text-gray-400 text-center -mt-1">
							{{ __('برای اسکن توسط کارکنان سایر مجموعه‌ها') }}
						</p>

						<!-- Personal QR -->
						<button
							@click="downloadPersonalQR"
							:disabled="loading"
							class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
						>
							<svg v-if="!loading || mode !== 'personal'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
							</svg>
							<div v-else class="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
							<span>{{ __('کد QR شخصی') }}</span>
						</button>
						<p class="text-xs text-gray-400 text-center -mt-1">
							{{ __('برای اسکن توسط مدیر یا خودتان') }}
						</p>
					</div>

					<!-- QR Preview -->
					<div v-if="qrPreview" class="flex flex-col items-center mt-4 p-4 bg-gray-50 rounded-lg">
						<img :src="qrPreview" :alt="__('کد QR')" class="w-48 h-48 border rounded mb-3" />
						<p class="text-sm text-gray-600 mb-3 text-center">{{ qrMessage }}</p>

						<div class="flex gap-2">
							<a
								:href="qrPreview"
								:download="qrFilename"
								class="inline-flex items-center gap-2 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 transition-colors text-sm"
							>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
								</svg>
								<span>{{ __('دانلود تصویر') }}</span>
							</a>
						</div>
					</div>

					<!-- Instruction -->
					<div v-if="qrPreview" class="bg-blue-50 border border-blue-100 rounded-lg p-3">
						<p class="text-blue-700 text-sm text-center leading-relaxed">
							{{ __('این کد QR را به مدیر خود نشان دهید تا ورود/خروج شما ثبت شود.') }}
						</p>
					</div>

					<ErrorMessage v-if="error" :message="error" class="mt-3" />
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { ref, inject } from "vue"
import { ErrorMessage } from "frappe-ui"
import BaseLayout from "@/components/BaseLayout.vue"

const __ = inject("$translate")

const loading = ref(false)
const mode = ref("")
const error = ref("")
const qrPreview = ref("")
const qrMessage = ref("")
const qrFilename = ref("")

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

async function downloadCompanyQR() {
	loading.value = true
	mode.value = "company"
	error.value = ""
	qrPreview.value = ""
	qrMessage.value = ""

	try {
		const res = await apiCall("hrms.api.qr_attendance.get_company_qr_code")
		const data = await res.json()

		if (res.ok && data.message) {
			const result = data.message
			if (result.qr_code) {
				qrPreview.value = result.qr_code
				qrMessage.value = result.message || __('کد QR شرکت با موفقیت تولید شد')
				qrFilename.value = `qr-company-${result.company}.png`
			} else {
				error.value = __('خطا در دریافت تصویر QR')
			}
		} else if (res.status === 417) {
			error.value = __('خطای پروکسی: لطفاً تنظیمات سرور را بررسی کنید')
		} else {
			error.value = data.message || data.exc || __('خطا در تولید کد QR شرکت')
		}
	} catch (e) {
		error.value = __('خطا در ارتباط با سرور')
		console.error(e)
	} finally {
		loading.value = false
		mode.value = ""
	}
}

async function downloadPersonalQR() {
	loading.value = true
	mode.value = "personal"
	error.value = ""
	qrPreview.value = ""
	qrMessage.value = ""

	try {
		const res = await apiCall("hrms.api.qr_attendance.get_employee_qr_code")
		const data = await res.json()

		if (res.ok && data.message) {
			const result = data.message
			if (result.qr_code) {
				qrPreview.value = result.qr_code
				qrMessage.value = result.message || __('کد QR شخصی شما تولید شد')
				qrFilename.value = `qr-personal-${result.employee}.png`
			} else {
				error.value = __('خطا در دریافت تصویر QR')
			}
		} else if (res.status === 417) {
			error.value = __('خطای پروکسی: لطفاً تنظیمات سرور را بررسی کنید')
		} else {
			error.value = data.message || data.exc || __('خطا در تولید کد QR شخصی')
		}
	} catch (e) {
		error.value = __('خطا در ارتباط با سرور')
		console.error(e)
	} finally {
		loading.value = false
		mode.value = ""
	}
}
</script>
