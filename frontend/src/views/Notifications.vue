<template>
	<BaseLayout :pageTitle="__('Notifications')">
		<template #body>
			<div class="w-full max-w-5xl mx-auto flex flex-col gap-4 mt-7 mb-7 p-4">
				<div class="flex flex-row justify-between items-center">
					<div
						class="text-lg text-gray-800 font-semibold"
						v-if="unreadNotificationsCount.data"
					>
						{{ __("{0} Unread", [unreadNotificationsCount.data]) }}
					</div>
					<div class="flex ml-auto gap-1">
						<Button
							v-if="allowPushNotifications"
							variant="outline"
							@click="router.push({ name: 'Settings' })"
						>
							<template #prefix>
								<FeatherIcon name="settings" class="w-4" />
							</template>
							{{ __("Settings") }}
						</Button>
						<Button
							v-if="unreadNotificationsCount.data"
							variant="outline"
							@click="markAllAsRead.submit"
							:loading="markAllAsRead.loading"
						>
							<template #prefix>
								<FeatherIcon name="check-circle" class="w-4" />
							</template>
							{{ __("Mark all as read") }}
						</Button>
					</div>
				</div>

				<div class="grid grid-cols-1 gap-2">
					<Button variant="solid" @click="createReminderForSelf">
						<template #prefix>
							<FeatherIcon name="bell" class="w-4" />
						</template>
						{{ __("یادآور برای خودم") }}
					</Button>
				</div>

				<div
					v-if="showEnablePushBanner"
					class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3"
				>
					<div class="text-sm font-semibold text-amber-900">
						{{ __("برای دریافت اعلان لحظه‌ای، دسترسی نوتیفیکیشن را فعال کنید.") }}
					</div>
						<div class="mt-1 text-xs text-amber-800">
							{{
								isInsecureContext
									? __("این آدرس امن نیست و مرورگر اجازه اعلان نمی‌دهد. از HTTPS یا localhost استفاده کنید.")
									: notificationPermission === "denied"
									? __("دسترسی اعلان در مرورگر شما بسته است. ابتدا آن را از تنظیمات مرورگر باز کنید.")
									: allowPushNotifications
										? __("پس از فعال‌سازی، یادآورها و اعلان‌ها سریع‌تر به شما نمایش داده می‌شوند.")
										: __("با فعال‌سازی این دسترسی، اعلان سیستمی و صدای اعلان داخل برنامه فعال می‌شود.")
						}}
					</div>
					<div class="mt-3 flex flex-wrap gap-2">
						<Button
							variant="solid"
							:loading="enablePushLoading"
							@click="enablePushNotifications"
						>
							{{ __("فعال‌سازی دسترسی اعلان") }}
						</Button>
						<Button
							v-if="isInsecureContext"
							variant="outline"
							@click="openLocalhostVersion"
						>
							{{ __("باز کردن نسخه localhost") }}
						</Button>
						<Button
							v-if="notificationPermission === 'denied'"
							variant="outline"
							@click="openBrowserNotificationSettings"
						>
							{{ __("باز کردن تنظیمات مرورگر") }}
						</Button>
						<Button
							v-if="allowPushNotifications"
							variant="outline"
							@click="router.push({ name: 'Settings' })"
						>
							{{ __("تنظیمات اعلان") }}
						</Button>
					</div>
				</div>

				<div
					class="flex flex-col bg-white rounded border border-slate-200"
					v-if="reminders.data?.length"
				>
					<div class="px-4 py-3 border-b border-slate-100 text-sm font-semibold text-slate-800">
						{{ __("یادآورهای قبلی من") }}
					</div>
					<div
						v-for="item in reminders.data"
						:key="`reminder-${item.name}`"
						class="flex flex-col gap-1 px-4 py-3 border-b last:border-b-0 border-slate-100"
					>
						<div class="text-sm text-slate-800">
							{{ item.description || __("یادآور بدون توضیح") }}
						</div>
						<div class="text-xs text-slate-500 flex items-center gap-2">
							<span>{{ formatReminderDate(item.remind_at) }}</span>
							<span
								class="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold"
								:class="item.notified ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'"
							>
								{{ item.notified ? __("انجام شده") : __("در انتظار") }}
							</span>
						</div>
					</div>
				</div>

				<div
					class="flex flex-col bg-white rounded"
					v-if="notifications.data?.length"
				>
					<router-link
						:class="[
							'flex flex-row items-start p-4 justify-between border-b before:mt-3',
							`before:content-[''] before:mr-2 before:shrink-0 before:w-1.5 before:h-1.5 before:rounded-full`,
							item.read ? 'bg-white-500' : 'before:bg-blue-500',
						]"
						v-for="item in notifications.data"
						:key="item.name"
						:to="getItemRoute(item)"
						@click="markAsRead(item.name)"
					>
						<EmployeeAvatar :userID="item.from_user" size="lg" />
						<div class="flex flex-col gap-0.5 grow ml-3">
							<div
								class="text-sm leading-5 font-normal text-gray-800"
								v-html="item.message"
							></div>
							<div class="text-xs font-normal text-gray-500">
								{{ dayjs(item.creation).fromNow() }}
							</div>
						</div>
					</router-link>
				</div>
				<div v-if="notifications.data?.length && notifications.hasNextPage" class="flex">
					<Button
						variant="outline"
						class="ml-auto"
						@click="loadMore"
					>
						{{ __('Load more') }}
					</Button>
				</div>
				<EmptyState
					v-if="!notifications.data?.length && !reminders.data?.length"
					:message="__('You have no notifications')"
				/>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { useRouter } from "vue-router"
import { createListResource, createResource, FeatherIcon, toast } from "frappe-ui"

import { computed, inject, onMounted, ref, watch } from "vue"
import BaseLayout from "@/components/BaseLayout.vue"
import EmployeeAvatar from "@/components/EmployeeAvatar.vue"
import EmptyState from "@/components/EmptyState.vue"

import {
	unreadNotificationsCount,
	notifications,
	arePushNotificationsEnabled,
} from "@/data/notifications"
import { userResource } from "@/data/user"
import { formatJalaliDateTime } from "@/utils/jalali"

const dayjs = inject("$dayjs")
const router = useRouter()
const __ = inject("$translate")
const currentStart = ref(0)
const pageLength = 10
const reminderPageLength = 20
const enablePushLoading = ref(false)
const notificationPermission = ref(
	typeof Notification === "undefined" ? "unsupported" : Notification.permission
)
const pushSubscriptionEnabled = ref(
	Boolean(window.frappePushNotification?.isNotificationEnabled?.())
)
const isInsecureContext = computed(() => !window.isSecureContext)

const reminders = createListResource({
	doctype: "Reminder",
	filters: {},
	fields: ["name", "description", "remind_at", "notified", "creation", "user"],
	auto: false,
	orderBy: "remind_at desc",
})


const allowPushNotifications = computed(
	() =>
		window.frappe?.boot.push_relay_server_url &&
		arePushNotificationsEnabled.data
)
const showEnablePushBanner = computed(() => {
	if (notificationPermission.value === "unsupported") return false
	if (notificationPermission.value !== "granted") return true
	return allowPushNotifications.value && !pushSubscriptionEnabled.value
})

const markAllAsRead = createResource({
	url: "hrms.api.mark_all_notifications_as_read",
	onSuccess() {
		notifications.reload()
	},
})

function markAsRead(name) {
	notifications.setValue.submit(
		{ name, read: 1 },
		{
			onSuccess: () => {
				unreadNotificationsCount.reload()
			},
		}
	)
}

function getItemRoute(item) {
	const doctype = String(item?.reference_document_type || "").trim()
	const docname = String(item?.reference_document_name || "").trim()

	if (!doctype || !docname) {
		return { name: "Notifications" }
	}
	if (doctype === "Reminder") {
		return { name: "Notifications" }
	}

	return {
		name: `${doctype.replace(/\s+/g, "")}DetailView`,
		params: { id: docname },
	}
}

function createReminderForSelf() {
	router.push({
		name: "EventFormView",
		query: { mode: "reminder" },
	})
}

function syncPushStatus() {
	notificationPermission.value =
		typeof Notification === "undefined" ? "unsupported" : Notification.permission
	pushSubscriptionEnabled.value = Boolean(
		window.frappePushNotification?.isNotificationEnabled?.()
	)
}

function openLocalhostVersion() {
	const { protocol, port, pathname, search } = window.location
	const localhostUrl = `${protocol}//localhost${port ? `:${port}` : ""}${pathname}${search}`
	window.location.href = localhostUrl
}

function openBrowserNotificationSettings() {
	const userAgent = navigator.userAgent.toLowerCase()
	const origin = window.location.origin

	let settingsUrl = ""
	if (userAgent.includes("edg")) {
		settingsUrl = "edge://settings/content/notifications"
	} else if (userAgent.includes("chrome")) {
		settingsUrl = `chrome://settings/content/siteDetails?site=${encodeURIComponent(origin)}`
	} else if (userAgent.includes("firefox")) {
		settingsUrl = "about:preferences#privacy"
	}

	if (settingsUrl) {
		try {
			window.open(settingsUrl, "_blank", "noopener")
		} catch (_error) {
			// Ignore failures and show fallback guide.
		}
	}

	toast({
		title: __("راهنما"),
		text: __(
			"در تنظیمات مرورگر، Notifications را برای این سایت روی Allow بگذارید و صفحه را دوباره باز کنید."
		),
		icon: "info",
		position: "bottom-center",
		iconClasses: "text-blue-500",
	})
}

async function enablePushNotifications() {
	syncPushStatus()
	if (isInsecureContext.value) {
		toast({
			title: __("خطا"),
			text: __("در این آدرس امن، امکان گرفتن دسترسی اعلان نیست. صفحه را با localhost یا HTTPS باز کنید."),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
		return
	}

	if (notificationPermission.value === "unsupported") {
		toast({
			title: __("خطا"),
			text: __("مرورگر شما از اعلان پشتیبانی نمی‌کند."),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
		return
	}

	const pushClient = window.frappePushNotification

	enablePushLoading.value = true
	try {
		let permissionResult = notificationPermission.value
		if (permissionResult !== "granted") {
			permissionResult = await Notification.requestPermission()
			syncPushStatus()
		}
		if (permissionResult !== "granted") {
			toast({
				title: __("خطا"),
				text: __(
					"دسترسی اعلان تایید نشد. اگر قبلا آن را Block کرده‌اید، از تنظیمات مرورگر روی Allow بگذارید."
				),
				icon: "alert-circle",
				position: "bottom-center",
				iconClasses: "text-red-500",
			})
			return
		}

		if (!allowPushNotifications.value) {
			toast({
				title: __("Success"),
				text: __("دسترسی اعلان مرورگر با موفقیت فعال شد."),
				icon: "check-circle",
				position: "bottom-center",
				iconClasses: "text-green-500",
			})
			return
		}

		if (!pushClient?.enableNotification) {
			toast({
				title: __("Success"),
				text: __("دسترسی اعلان مرورگر فعال شد."),
				icon: "check-circle",
				position: "bottom-center",
				iconClasses: "text-green-500",
			})
			return
		}

		const result = await pushClient.enableNotification()
		syncPushStatus()

		if (!result?.permission_granted) {
			toast({
				title: __("هشدار"),
				text: __("دسترسی مرورگر فعال است ولی اتصال اعلان پوش کامل نشد."),
				icon: "alert-triangle",
				position: "bottom-center",
				iconClasses: "text-amber-500",
			})
			return
		}

		toast({
			title: __("Success"),
			text: __("اعلان با موفقیت فعال شد."),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
	} catch (error) {
		toast({
			title: __("خطا"),
			text:
				(typeof error?.message === "string" && error.message)
				|| __("فعال‌سازی اعلان ناموفق بود."),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
	} finally {
		enablePushLoading.value = false
	}
}

function formatReminderDate(value) {
	if (!value) return __("زمان نامشخص")
	return formatJalaliDateTime(value)
}

onMounted(() => {
	const userName = userResource.data?.name
	notifications.filters.to_user = userName
	notifications.start = 0
	notifications.pageLength = 10
	notifications.fetch()

	reminders.filters.user = userName
	reminders.start = 0
	reminders.pageLength = reminderPageLength
	reminders.fetch()
	syncPushStatus()
})

watch(
	() => userResource.data?.name,
	(userName) => {
		if (!userName) return
		notifications.filters.to_user = userName
		currentStart.value = 0
		notifications.start = 0
		notifications.pageLength = 10
		notifications.fetch()

		reminders.filters.user = userName
		reminders.start = 0
		reminders.pageLength = reminderPageLength
		reminders.fetch()
		syncPushStatus()
	},
	{ immediate: true }
)

function loadMore() {
	currentStart.value += pageLength
	notifications.start = currentStart.value
	notifications.pageLength = pageLength
	notifications.list.fetch()
}
</script>
