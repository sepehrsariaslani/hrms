<template>
	<BaseLayout :pageTitle="__('کد QR شرکت')">
		<template #body>
			<div class="flex flex-col items-center mt-7 mb-7 py-4 px-4 w-full gap-6">
				<div
					v-if="qrData"
					class="flex flex-col items-center gap-4 w-full bg-white rounded-lg p-6 border border-gray-200"
				>
					<div class="text-sm text-gray-500 font-medium">
						{{ __("کد QR شرکت") }}
					</div>

					<div class="text-base font-bold text-gray-800 text-center">
						{{ qrData.company }}
					</div>

					<div class="bg-white p-4 rounded-xl border-2 border-gray-200 shadow-sm">
						<img
							:src="qrCodeUrl"
							alt="QR Code"
							class="w-56 h-56"
						/>
					</div>

					<div class="text-xs text-gray-400 text-center leading-5">
						{{ __("این کد را چاپ کنید و در محل مجاز شرکت قرار دهید.") }}
					</div>

					<Button
						@click="downloadQR"
						variant="solid"
						class="w-full py-3 text-base"
					>
						{{ __("دانلود کد QR") }}
					</Button>

					<Button
						@click="shareQR"
						variant="outline"
						class="w-full py-3 text-base"
					>
						{{ __("اشتراک‌گذاری لینک") }}
					</Button>
				</div>

				<div v-else-if="loading" class="flex items-center gap-2 text-gray-500">
					<LoadingIndicator class="h-5 w-5" />
					<span class="text-sm">{{ __("در حال تولید کد QR...") }}</span>
				</div>

				<div v-else-if="error" class="flex items-center gap-2 text-red-500">
					<span class="text-sm">{{ error }}</span>
				</div>

				<div class="flex flex-col gap-3 w-full bg-blue-50 rounded-lg p-4 border border-blue-200">
					<div class="text-sm font-bold text-blue-800">
						{{ __("راهنمای استفاده") }}
					</div>
					<div class="flex flex-col gap-2 text-xs text-blue-700 leading-5">
						<div class="flex items-start gap-2">
							<span class="font-bold">۱.</span>
							<span>{{ __("کد QR شرکت را دانلود و چاپ کنید.") }}</span>
						</div>
						<div class="flex items-start gap-2">
							<span class="font-bold">۲.</span>
							<span>{{ __("کارمندان با دوربین گوشی QR را باز می‌کنند.") }}</span>
						</div>
						<div class="flex items-start gap-2">
							<span class="font-bold">۳.</span>
							<span>{{ __("ثبت فقط با لوکیشن داخل محدوده شرکت انجام می‌شود.") }}</span>
						</div>
					</div>
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { inject, ref, onMounted } from "vue"
import { Button, LoadingIndicator } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"

const __ = inject("$translate")

const qrData = ref(null)
const qrCodeUrl = ref("")
const qrContentUrl = ref("")
const loading = ref(false)
const error = ref("")

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

function getQRCodeContent(data) {
	const params = new URLSearchParams({ qr_data: data })
	return `${window.location.origin}/hrms/qr-scan?${params.toString()}`
}

const fetchQRCode = async () => {
	loading.value = true
	error.value = ""
	try {
		const res = await apiCall("hrms.api.qr_attendance.get_company_qr_code")
		if (res.message?.qr_data) {
			qrData.value = res.message
			qrContentUrl.value = getQRCodeContent(res.message.qr_data)
			qrCodeUrl.value = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(qrContentUrl.value)}`
		} else {
			error.value = getResponseMessage(res, __("خطا در تولید کد QR"))
		}
	} catch (e) {
		console.error("QR code generation failed:", e)
		error.value = __("خطا در ارتباط با سرور")
	} finally {
		loading.value = false
	}
}

const downloadQR = () => {
	if (!qrCodeUrl.value) return
	const link = document.createElement("a")
	link.href = qrCodeUrl.value
	link.download = `qr_attendance_company_${qrData.value?.company || "company"}.png`
	document.body.appendChild(link)
	link.click()
	document.body.removeChild(link)
}

const shareQR = async () => {
	if (!qrContentUrl.value) return
	if (navigator.share) {
		try {
			await navigator.share({
				title: __("کد QR حضور و غیاب"),
				text: __("این لینک برای ثبت حضور با QR شرکت است"),
				url: qrContentUrl.value,
			})
		} catch (e) {
			console.error("Share failed:", e)
		}
	} else {
		try {
			await navigator.clipboard.writeText(qrContentUrl.value)
			alert(__("لینک کد QR در کلیپ‌بورد کپی شد"))
		} catch (e) {
			console.error("Copy failed:", e)
		}
	}
}

onMounted(() => {
	fetchQRCode()
})
</script>
