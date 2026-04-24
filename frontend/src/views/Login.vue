<template>
	<ion-page>
		<ion-content class="ion-padding">
			<div class="flex min-h-screen w-full flex-col justify-center bg-gradient-to-b from-slate-50 to-white">
					<div class="flex flex-col mx-auto gap-3 items-center">
						<FrappeHRLogo class="h-8 w-8" />
						<div class="text-3xl font-semibold text-gray-900 text-center">
							ورود به فرپه منابع انسانی
						</div>
					</div>

				<div class="mx-auto mt-10 w-full max-w-md px-8 md:max-w-lg">
					<div class="mb-5 grid grid-cols-2 gap-2 rounded-lg bg-gray-100 p-1">
						<button
							type="button"
							class="rounded-md px-3 py-2 text-sm font-medium transition"
							:class="authMode === 'password' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'"
							@click="setAuthMode('password')"
						>
							ورود با رمز
						</button>
						<button
							type="button"
							class="rounded-md px-3 py-2 text-sm font-medium transition"
							:class="authMode === 'mobile_otp' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'"
							@click="setAuthMode('mobile_otp')"
						>
							ورود با کد پیامکی
						</button>
					</div>

					<form v-if="authMode === 'password'" class="flex flex-col space-y-4" @submit.prevent="submit">
							<Input
								label="ایمیل یا نام کاربری"
								placeholder="johndoe@mail.com"
								v-model="email"
								type="text"
								autocomplete="username"
							/>
							<Input
								label="رمز عبور"
								type="password"
								placeholder="••••••"
								v-model="password"
								autocomplete="current-password"
							/>
						<ErrorMessage :message="errorMessage" />
							<Button
								:loading="session.login.loading"
								variant="solid"
								class="disabled:bg-gray-700 disabled:text-white !mt-6"
							>
								ورود
							</Button>
					</form>

					<template v-if="authMode === 'password' && authProviders.data?.length">
							<div class="text-center text-sm text-gray-600 my-4">یا</div>
							<div class="space-y-4">
							<a
								v-for="provider in authProviders.data"
								:key="provider.name"
								class="flex items-center justify-center gap-2 transition-colors focus:outline-none text-gray-800 bg-gray-100 hover:bg-gray-200 active:bg-gray-300 focus-visible:ring focus-visible:ring-gray-400 h-7 text-base p-2 rounded"
								:href="provider.auth_url"
								>
									<img class="h-4 w-4" :src="provider.icon" :alt="provider.provider_name" />
								<span>ورود با {{ provider.provider_name }}</span>
								</a>
							</div>
						</template>

					<form v-if="authMode === 'mobile_otp'" class="flex flex-col space-y-4" @submit.prevent="handleMobileOtpSubmit">
						<Input
							label="شماره موبایل"
							placeholder="0912xxxxxxx"
							v-model="mobileNumber"
							type="tel"
							autocomplete="tel"
						/>
						<Input
							v-if="mobileOtpSent"
							label="کد تایید"
							placeholder="000000"
							v-model="mobileOtpCode"
							type="text"
							autocomplete="one-time-code"
						/>
						<p v-if="mobileStatusMessage" class="text-xs text-green-700">
							{{ mobileStatusMessage }}
						</p>
						<ErrorMessage :message="errorMessage" />
						<Button
							:loading="mobileLoading"
							variant="solid"
							class="disabled:bg-gray-700 disabled:text-white !mt-6"
						>
							{{ mobileOtpSent ? "ورود با کد" : "ارسال کد تایید" }}
						</Button>
						<Button
							v-if="mobileOtpSent"
							type="button"
							variant="subtle"
							@click="sendMobileOtpCode"
							:disabled="mobileLoading || mobileCooldown > 0"
						>
							{{ mobileCooldown > 0 ? `ارسال مجدد کد (${mobileCooldown})` : "ارسال مجدد کد" }}
						</Button>
					</form>
				</div>
			</div>

				<Dialog v-model="resetPassword.showDialog">
					<template #body-title>
						<h2 class="text-lg font-bold">بازنشانی رمز عبور</h2>
					</template>
					<template #body-content>
						<p>
							رمز عبور شما منقضی شده است. لطفا برای ادامه آن را بازنشانی کنید.
						</p>
					</template>
					<template #actions>
					<a
						class="inline-flex items-center justify-center gap-2 transition-colors focus:outline-none text-white bg-gray-900 hover:bg-gray-800 active:bg-gray-700 focus-visible:ring focus-visible:ring-gray-400 h-7 text-base px-2 rounded"
							:href="resetPassword.link"
							target="_blank"
						>
							رفتن به صفحه بازنشانی رمز عبور
						</a>
					</template>
				</Dialog>

				<Dialog v-model="otp.showDialog">
					<template #body-title>
						<h2 class="text-lg font-bold">تایید کد یکبارمصرف</h2>
					</template>
				<template #body-content>
					<p class="mb-4" v-if="otp.verification.prompt">
						{{ otp.verification.prompt }}
					</p>

						<form class="flex flex-col space-y-4" @submit.prevent="submit">
							<Input
								label="کد یکبارمصرف"
								type="text"
								placeholder="000000"
								v-model="otp.code"
							autocomplete="one-time-code"
						/>
						<ErrorMessage :message="errorMessage" />
							<Button
								:loading="session.otp.loading"
								variant="solid"
								class="disabled:bg-gray-700 disabled:text-white !mt-6"
							>
								تایید
							</Button>
						</form>
					</template>
				</Dialog>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { inject, onBeforeUnmount, reactive, ref } from "vue"
import { Input, Button, ErrorMessage, Dialog, createResource } from "frappe-ui"

import FrappeHRLogo from "@/components/icons/FrappeHRLogo.vue"

const email = ref(null)
const password = ref(null)
const errorMessage = ref("")
const authMode = ref("mobile_otp")
const mobileNumber = ref("")
const mobileOtpCode = ref("")
const mobileChallengeId = ref("")
const mobileOtpSent = ref(false)
const mobileLoading = ref(false)
const mobileCooldown = ref(0)
const mobileStatusMessage = ref("")

const resetPassword = reactive({
	showDialog: false,
	link: "",
})
const otp = reactive({
	showDialog: false,
	tmp_id: "",
	code: "",
	verification: {},
})

const session = inject("$session")
let mobileCooldownInterval = null

function normalizeMobile(value) {
	if (!value) return ""
	const persianToEnglish = {
		"۰": "0",
		"۱": "1",
		"۲": "2",
		"۳": "3",
		"۴": "4",
		"۵": "5",
		"۶": "6",
		"۷": "7",
		"۸": "8",
		"۹": "9",
	}

	let output = ""
	for (const ch of String(value).trim()) {
		if (persianToEnglish[ch]) {
			output += persianToEnglish[ch]
		} else if (/[0-9+]/.test(ch)) {
			output += ch
		}
	}
	return output
}

function clearMobileCooldown() {
	if (mobileCooldownInterval) {
		clearInterval(mobileCooldownInterval)
		mobileCooldownInterval = null
	}
}

function startMobileCooldown(seconds = 60) {
	clearMobileCooldown()
	mobileCooldown.value = Math.max(parseInt(seconds, 10) || 0, 0)
	if (!mobileCooldown.value) return

	mobileCooldownInterval = setInterval(() => {
		if (mobileCooldown.value <= 1) {
			mobileCooldown.value = 0
			clearMobileCooldown()
			return
		}
		mobileCooldown.value -= 1
	}, 1000)
}

function getErrorMessage(error) {
	if (Array.isArray(error?.messages) && error.messages.length) {
		return error.messages.join("\n")
	}

	const response = error?.responseJSON || error?.response?.data
	if (response?._server_messages) {
		try {
			const messages = JSON.parse(response._server_messages || "[]")
			if (Array.isArray(messages) && messages.length) {
				return messages
					.map((item) => {
						try {
							return JSON.parse(item)?.message || item
						} catch {
							return item
						}
					})
					.join("\n")
			}
		} catch {
			return "خطایی در ارتباط با سرور رخ داد."
		}
	}

	return error?.message || "خطایی در ارتباط با سرور رخ داد."
}

function setAuthMode(mode) {
	authMode.value = mode
	errorMessage.value = ""
	mobileStatusMessage.value = ""
	if (mode === "mobile_otp") {
		return
	}
	mobileOtpCode.value = ""
}

async function sendMobileOtpCode() {
	const normalizedMobile = normalizeMobile(mobileNumber.value)
	if (!normalizedMobile || !/^(\+?98|0098|0)?9\d{9}$/.test(normalizedMobile)) {
		errorMessage.value = "شماره موبایل معتبر وارد کنید."
		return
	}

	mobileNumber.value = normalizedMobile
	errorMessage.value = ""
	mobileStatusMessage.value = ""
	mobileLoading.value = true
	try {
		const response = await session.sendMobileOtp(normalizedMobile)
		const payload = response?.message || {}
		if (!payload?.challenge_id) {
			throw new Error("کد ورود ایجاد نشد. دوباره تلاش کنید.")
		}

		mobileChallengeId.value = payload.challenge_id
		mobileOtpSent.value = true
		mobileStatusMessage.value = payload.message || "کد تایید ارسال شد."
		startMobileCooldown(payload.retry_after || 60)
	} catch (error) {
		errorMessage.value = getErrorMessage(error)
	} finally {
		mobileLoading.value = false
	}
}

async function verifyMobileOtpCode() {
	const normalizedMobile = normalizeMobile(mobileNumber.value)
	if (!normalizedMobile || !mobileChallengeId.value) {
		errorMessage.value = "ابتدا کد تایید را دریافت کنید."
		return
	}
	if (!mobileOtpCode.value?.trim()) {
		errorMessage.value = "کد تایید را وارد کنید."
		return
	}

	errorMessage.value = ""
	mobileStatusMessage.value = ""
	mobileLoading.value = true
	try {
		const response = await session.mobileOtpLogin(
			normalizedMobile,
			mobileOtpCode.value.trim(),
			mobileChallengeId.value
		)
		const payload = response?.message || {}
		if (!payload.logged_in) {
			throw new Error("ورود ناموفق بود.")
		}
	} catch (error) {
		errorMessage.value = getErrorMessage(error)
	} finally {
		mobileLoading.value = false
	}
}

async function handleMobileOtpSubmit() {
	if (mobileOtpSent.value) {
		await verifyMobileOtpCode()
		return
	}
	await sendMobileOtpCode()
}

async function submit() {
	try {
		let response
		if (otp.showDialog) {
			response = await session.otp(otp.tmp_id, otp.code)
		} else {
			response = await session.login(email.value, password.value)
		}

		if (response.message === "Password Reset") {
			resetPassword.showDialog = true
			resetPassword.link = response.redirect_to
		} else {
			resetPassword.showDialog = false
			resetPassword.link = ""
		}

		// OTP verification
		if (response.verification) {
			if (response.verification.setup) {
				otp.showDialog = true
				otp.tmp_id = response.tmp_id
				otp.verification = response.verification
			} else {
				// Don't bother handling impossible OTP setup (e.g. no phone number).
				window.open("/login?redirect-to=" + encodeURIComponent(window.location.pathname), "_blank")
			}
		}
	} catch (error) {
		errorMessage.value = getErrorMessage(error)
	}
}

const authProviders = createResource({
	url: "hrms.api.oauth.oauth_providers",
	auto: true,
})

onBeforeUnmount(() => {
	clearMobileCooldown()
})
</script>
