<template>
	<div class="min-h-screen bg-gray-50 flex flex-col">
		<!-- Header -->
		<div class="bg-white border-b px-4 py-3 flex items-center justify-between">
			<h1 class="text-lg font-semibold text-gray-800">{{ __('اسکن کد QR') }}</h1>
			<button
				v-if="state !== 'loading'"
				@click="resetState"
				class="text-sm text-blue-500 hover:text-blue-700"
			>
				{{ __('شروع مجدد') }}
			</button>
		</div>

		<div class="flex-1 flex flex-col items-center justify-center p-4">

			<!-- State: Loading (auth check / processing) -->
			<div v-if="state === 'loading'" class="text-center py-12">
				<div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent mb-4"></div>
				<p class="text-gray-500">{{ loadingMessage }}</p>
			</div>

			<!-- State: Scanning (camera active) -->
			<div v-if="state === 'scanning'" class="text-center w-full max-w-sm">
				<div class="relative inline-block mb-4">
					<video
						ref="videoRef"
						class="w-64 h-64 rounded-xl bg-black object-cover mx-auto"
						autoplay
						playsinline
						muted
					></video>
					<div class="absolute inset-0 border-2 border-blue-400 rounded-xl pointer-events-none mx-auto" style="width:256px;height:256px">
						<!-- Corner markers -->
						<div class="absolute top-0 left-0 w-6 h-6 border-t-3 border-l-3 border-blue-500 rounded-tl-lg"></div>
						<div class="absolute top-0 right-0 w-6 h-6 border-t-3 border-r-3 border-blue-500 rounded-tr-lg"></div>
						<div class="absolute bottom-0 left-0 w-6 h-6 border-b-3 border-l-3 border-blue-500 rounded-bl-lg"></div>
						<div class="absolute bottom-0 right-0 w-6 h-6 border-b-3 border-r-3 border-blue-500 rounded-br-lg"></div>
					</div>
				</div>
				<p class="text-gray-500 text-sm">{{ __('کد QR را مقابل دوربین قرار دهید') }}</p>
			</div>

			<!-- State: Success -->
			<div v-if="state === 'success'" class="text-center py-8 w-full max-w-sm">
				<div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 mb-4">
					<svg class="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
					</svg>
				</div>
				<p class="text-xl font-bold text-green-600 mb-1">{{ result.action }}</p>
				<p v-if="result.employee" class="text-gray-600 text-sm mb-1">{{ result.employee }}</p>
				<p v-if="result.time" class="text-gray-400 text-sm dir-ltr">{{ result.time }}</p>

				<!-- Auto-dismiss countdown or tap to continue -->
				<p class="text-gray-300 text-xs mt-6">{{ __('برای اسکن جدید کلیک کنید') }}</p>
				<button
					@click="resetState"
					class="mt-2 px-6 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600"
				>
					{{ __('اسکن مجدد') }}
				</button>
			</div>

			<!-- State: Error -->
			<div v-if="state === 'error'" class="text-center py-8 w-full max-w-sm">
				<div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-red-100 mb-4">
					<svg class="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</div>
				<p class="text-lg font-medium text-red-600 mb-4">{{ result.message }}</p>
				<button
					@click="resetState"
					class="px-6 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600"
				>
					{{ __('تلاش مجدد') }}
				</button>
			</div>

			<!-- State: Camera denied -->
			<div v-if="state === 'camera_denied'" class="text-center py-8 w-full max-w-sm">
				<div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gray-100 mb-4">
					<svg class="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
							d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
					</svg>
				</div>
				<p class="text-gray-700 font-medium mb-1">{{ __('دسترسی به دوربین رد شد') }}</p>
				<p class="text-gray-500 text-sm">{{ __('لطفا کد QR را به صورت دستی وارد کنید') }}</p>
			</div>

			<!-- Manual Input (shown when camera denied, error, or as fallback) -->
			<div
				v-if="showManualInput || state === 'camera_denied' || state === 'error' || state === 'idle'"
				class="w-full max-w-sm mt-6"
			>
				<div class="bg-white rounded-xl shadow-sm border p-4">
					<p class="text-sm text-gray-500 text-center mb-3">{{ __('یا کد را دستی وارد کنید:') }}</p>
					<div class="flex gap-2">
						<input
							v-model="manualCode"
							type="text"
							:placeholder="__('کد QR یا شناسه کارمند را وارد کنید...')"
							class="flex-1 px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
							@keyup.enter="submitManual"
							:disabled="state === 'loading'"
						/>
						<button
							@click="submitManual"
							:disabled="!manualCode || state === 'loading'"
							class="px-5 py-2.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 text-sm font-medium"
						>
							{{ __('ثبت') }}
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, inject } from "vue"
import { useRoute, useRouter } from "vue-router"
import dayjs from "@/utils/dayjs"

const __ = inject("$translate")

const route = useRoute()
const router = useRouter()

// State machine: 'idle' | 'loading' | 'scanning' | 'success' | 'error' | 'camera_denied'
const state = ref("loading")
const loadingMessage = ref(__("در حال بررسی احراز هویت..."))
const manualCode = ref("")
const showManualInput = ref(false)
const result = ref({ action: "", time: "", employee: "", message: "" })
const videoRef = ref(null)
let videoStream = null

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

async function processAttendance(employeeId) {
	state.value = "loading"
	loadingMessage.value = __("در حال ثبت ورود/خروج...")
	showManualInput.value = false

	try {
		const res = await apiCall("hrms.api.attendance.qr_checkin", {
			employee_id: employeeId,
		})
		const data = await res.json()

		if (res.ok && data.message) {
			const msg = data.message
			result.value = {
				action: msg.message || (msg.action === "In" ? __("ورود ثبت شد") : __("خروج ثبت شد")),
				time: msg.time ? dayjs(msg.time).format("YYYY/MM/DD HH:mm:ss") : dayjs().format("YYYY/MM/DD HH:mm:ss"),
				employee: msg.employee_name || "",
				message: "",
			}
			state.value = "success"

			// Auto-reset after 5 seconds for next scan
			setTimeout(() => {
				if (state.value === "success") {
					resetState()
				}
			}, 5000)
		} else {
			result.value = {
				action: "",
				time: "",
				employee: "",
				message: data.message || data.exc || __("خطا در ثبت ورود/خروج"),
			}
			state.value = "error"
			showManualInput.value = true
		}
	} catch (e) {
		result.value = {
			action: "",
			time: "",
			employee: "",
			message: e.message === "Failed to fetch" ? __("خطا در ارتباط با سرور") : (e.message || __("خطا در ثبت ورود/خروج")),
		}
		state.value = "error"
		showManualInput.value = true
		console.error(e)
	}
}

async function submitManual() {
	if (!manualCode.value || state.value === "loading") return

	const code = manualCode.value.trim()
	manualCode.value = ""

	// Extract employee_id from input — could be:
	// 1. Just the employee ID (e.g. "EMP-001")
	// 2. A full URL (e.g. "https://site/app/attendance/scan?employee_id=EMP-001")
	// 3. A token string
	let employeeId = code

	// Try to extract from URL
	try {
		if (code.includes("employee_id=")) {
			const url = new URL(code)
			employeeId = url.searchParams.get("employee_id") || code
		} else if (code.includes("?")) {
			// Might be a relative URL or query string
			const parts = code.split("?")
			const params = new URLSearchParams(parts[1])
			employeeId = params.get("employee_id") || params.get("token") || code
		}
	} catch {
		// Not a valid URL, use as-is
	}

	await processAttendance(employeeId)
}

function resetState() {
	// Stop camera if running
	if (videoStream) {
		videoStream.getTracks().forEach((track) => track.stop())
		videoStream = null
	}

	result.value = { action: "", time: "", employee: "", message: "" }
	manualCode.value = ""
	showManualInput.value = false

	// Check if we have a token in URL to process immediately
	const employeeId = route.query.employee_id || route.query.token
	if (employeeId) {
		processAttendance(employeeId)
	} else {
		state.value = "idle"
		showManualInput.value = true
	}
}

async function startCamera() {
	try {
		videoStream = await navigator.mediaDevices.getUserMedia({
			video: { facingMode: "environment" },
		})
		if (videoRef.value) {
			videoRef.value.srcObject = videoStream
		}
		state.value = "scanning"
		showManualInput.value = true
	} catch (err) {
		if (
			err.name === "NotAllowedError" ||
			err.name === "PermissionDeniedError"
		) {
			state.value = "camera_denied"
			showManualInput.value = true
		} else {
			state.value = "error"
			result.value.message = __("خطا در راه‌اندازی دوربین")
			showManualInput.value = true
		}
	}
}

onMounted(async () => {
	// Step 1: Check auth
	loadingMessage.value = __("در حال بررسی احراز هویت...")

	// The router's beforeEach already handles auth redirect,
	// but we double-check here for direct access
	const user = window.frappe?.boot?.user
	if (!user || user === "Guest") {
		// Redirect to login with return URL
		const returnUrl = encodeURIComponent(route.fullPath)
		router.push({
			name: "Login",
			query: { "redirect-to": returnUrl },
		})
		return
	}

	// Step 2: Check if employee_id is in URL query
	const employeeId = route.query.employee_id || route.query.token

	if (employeeId) {
		// Direct scan link — process immediately
		await processAttendance(employeeId)
	} else {
		// Show camera for scanning
		await startCamera()
	}
})

onBeforeUnmount(() => {
	if (videoStream) {
		videoStream.getTracks().forEach((track) => track.stop())
	}
})
</script>

<style scoped>
.dir-ltr {
	direction: ltr;
	text-align: center;
}
</style>
