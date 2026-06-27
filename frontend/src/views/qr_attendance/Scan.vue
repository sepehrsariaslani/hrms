<template>
	<BaseLayout :pageTitle="__('ثبت حضور با QR')">
		<template #body>
			<div class="flex flex-col items-center mt-7 mb-7 py-4 px-4 w-full gap-6">
				<div class="flex flex-col gap-3 w-full bg-white rounded-lg p-5 border border-gray-200">
					<div class="text-base font-bold text-gray-800">
						{{ __("ثبت ورود و خروج") }}
					</div>
					<div class="text-sm text-gray-500 leading-6">
						{{ statusText }}
					</div>
					<Button
						v-if="manualCode && !scanResult"
						@click="submitManualCode"
						variant="solid"
						class="w-full py-3 text-base"
						:loading="submitting"
					>
						{{ __("ثبت حضور") }}
					</Button>
				</div>

				<div
					v-if="!manualCode"
					class="flex flex-col gap-3 w-full bg-white rounded-lg p-4 border border-gray-200"
				>
					<div class="text-sm font-bold text-gray-700">
						{{ __("ورود دستی کد") }}
					</div>
					<div class="flex gap-2">
						<input
							v-model="manualCode"
							type="text"
							:placeholder="__('کد QR را اینجا وارد کنید...')"
							class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
						/>
						<Button
							@click="submitManualCode"
							variant="solid"
							:disabled="!manualCode || submitting"
							:loading="submitting"
						>
							{{ __("ثبت") }}
						</Button>
					</div>
				</div>

				<div
					v-if="scanResult"
					class="flex flex-col gap-3 w-full rounded-lg p-4 border"
					:class="scanResult.status === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'"
				>
					<div
						class="text-base font-bold"
						:class="scanResult.status === 'success' ? 'text-green-800' : 'text-red-800'"
					>
						{{ scanResult.status === 'success' ? __("ثبت شد") : __("خطا") }}
					</div>
					<div
						v-if="scanResult.status === 'success'"
						class="flex flex-col gap-1 text-sm text-green-700"
					>
						<span>{{ __("کارمند") }}: {{ scanResult.employee_name || scanResult.employee }}</span>
						<span>{{ __("عملیات") }}: {{ scanResult.action }}</span>
						<span>{{ __("زمان") }}: {{ dayjs(scanResult.time).format("YYYY-MM-DD HH:mm") }}</span>
					</div>
					<div v-else class="text-sm text-red-700 leading-6">
						{{ scanResult.message || __("خطا در پردازش کد QR") }}
					</div>
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref, onMounted } from "vue"
import { useRoute } from "vue-router"
import { Button } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import dayjs from "@/utils/dayjs"

const __ = inject("$translate")
const route = useRoute()

const manualCode = ref("")
const scanResult = ref(null)
const submitting = ref(false)
const locationStatus = ref("")

const statusText = computed(() => {
	if (submitting.value) return locationStatus.value || __("در حال دریافت لوکیشن و ثبت حضور...")
	if (scanResult.value?.status === "success") return __("ثبت حضور شما با موفقیت انجام شد.")
	if (scanResult.value?.status === "error") return __("ثبت حضور انجام نشد.")
	if (manualCode.value) return __("برای ثبت حضور، دسترسی لوکیشن را تأیید کنید.")
	return __("برای ثبت حضور، QR چاپ‌شده شرکت را با دوربین گوشی اسکن کنید.")
})

function getResponseMessage(response, fallback) {
	if (response?.message?.message) return response.message.message
	if (typeof response?.message === "string") return response.message
	if (response?.error) return response.error
	try {
		const messages = JSON.parse(response?._server_messages || "[]")
		const firstMessage = messages
			.map((item) => {
				try {
					return JSON.parse(item)?.message || item
				} catch {
					return item
				}
			})
			.find(Boolean)
		if (firstMessage) return firstMessage
	} catch {
		// ignore malformed server messages
	}
	return fallback
}

function normalizeQRCodeValue(value) {
	const text = String(value || "").trim()
	if (!text) return ""
	try {
		const url = new URL(text)
		return url.searchParams.get("qr_data") || text
	} catch {
		return text
	}
}

function apiCall(method, args = {}) {
	const base = window.location.origin
	return fetch(`${base}/api/method/${method}`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			"X-Frappe-CSRF-Token": window.csrf_token || "",
		},
		body: JSON.stringify(args),
	}).then((r) => r.json())
}

function getCurrentPosition() {
	return new Promise((resolve, reject) => {
		if (!navigator.geolocation) {
			reject(new Error(__("مرورگر شما دریافت لوکیشن را پشتیبانی نمی‌کند.")))
			return
		}
		locationStatus.value = __("در حال دریافت لوکیشن...")
		navigator.geolocation.getCurrentPosition(resolve, reject, {
			enableHighAccuracy: true,
			timeout: 15000,
			maximumAge: 0,
		})
	})
}

function getLocationErrorMessage(error) {
	if (error?.code === 1) return __("برای ثبت ورود و خروج باید دسترسی لوکیشن را فعال کنید.")
	if (error?.code === 2) return __("لوکیشن شما قابل دریافت نیست. GPS یا اینترنت گوشی را بررسی کنید.")
	if (error?.code === 3) return __("دریافت لوکیشن بیش از حد طول کشید. دوباره تلاش کنید.")
	return error?.message || __("خطا در دریافت لوکیشن")
}

const submitManualCode = async () => {
	manualCode.value = normalizeQRCodeValue(manualCode.value)
	if (!manualCode.value || submitting.value) return
	scanResult.value = null
	submitting.value = true
	try {
		const position = await getCurrentPosition()
		locationStatus.value = __("در حال ثبت حضور...")
		const res = await apiCall("hrms.api.qr_attendance.scan_qr_attendance", {
			qr_data: manualCode.value,
			latitude: position.coords.latitude,
			longitude: position.coords.longitude,
		})
		if (res.message?.status === "success") {
			scanResult.value = res.message
		} else {
			scanResult.value = {
				status: "error",
				message: getResponseMessage(res, __("خطا در پردازش کد QR")),
			}
		}
	} catch (e) {
		scanResult.value = {
			status: "error",
			message: getLocationErrorMessage(e),
		}
	} finally {
		submitting.value = false
		locationStatus.value = ""
	}
}

onMounted(() => {
	const qrDataFromUrl = route.query.qr_data
	if (typeof qrDataFromUrl === "string" && qrDataFromUrl) {
		manualCode.value = normalizeQRCodeValue(qrDataFromUrl)
		submitManualCode()
	}
})
</script>
