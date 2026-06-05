import { createApp } from "vue"
import App from "./App.vue"
import router from "./router"
import { initSocket } from "./socket"

import {
	Button,
	Input,
	setConfig,
	frappeRequest,
	resourcesPlugin,
	FormControl,
} from "frappe-ui"
import { translationsPlugin } from "./plugins/translationsPlugin.js"
import EmptyState from "@/components/EmptyState.vue"

import { IonicVue } from "@ionic/vue"

import { session } from "@/data/session"
import { userResource } from "@/data/user"
import { employeeResource } from "@/data/employee"
import { employeeDeskVisibility } from "@/data/layout"
import {
	employeeDeskGlobalPersonalization,
	employeeDeskPersonalization,
} from "@/data/personalization"

import dayjs from "@/utils/dayjs"
import getIonicConfig from "@/utils/ionicConfig"
import { initializeAccentTheme } from "@/utils/accentTheme"
import { initializeColorMode } from "@/utils/colorMode"

import FrappePushNotification from "../public/frappe-push-notification"

/* Core CSS required for Ionic components to work properly */
import "@ionic/vue/css/core.css"

/* Theme variables */
import "./theme/variables.css"

import "./main.css"

const app = createApp(App)
const socket = initSocket()

setConfig("resourceFetcher", frappeRequest)
app.use(resourcesPlugin)
app.use(translationsPlugin)

app.component("Button", Button)
app.component("Input", Input)
app.component("FormControl", FormControl)
app.component("EmptyState", EmptyState)

app.use(router)
app.use(IonicVue, getIonicConfig())

if (session?.isLoggedIn && !employeeResource?.data) {
	employeeResource.reload()
}

app.provide("$session", session)
app.provide("$user", userResource)
app.provide("$employee", employeeResource)
app.provide("$socket", socket)
app.provide("$dayjs", dayjs)

const ALLOCATOR_SHIFT_ROUTES = new Set(["TeamWeeklyShiftBoardView", "ShiftAllocatorSchedulerView"])
const WEEKLY_SHIFT_ROUTES = new Set(["WeeklyShiftPlannerView"])
const WEEKLY_SHIFT_ROUTE_PREFIXES = ["/weekly-shift-planner"]
const VISIBILITY_ROUTE_RULES = [
	{
		key: "enable_requests_center",
		prefixes: ["/dashboard/requests"],
	},
	{
		key: "enable_attendance",
		prefixes: [
			"/dashboard/attendance",
			"/attendance-requests",
			"/shift-requests",
			"/shift-assignments",
			"/employee-checkins",
			"/weekly-shift-planner",
			"/team-weekly-shifts",
			"/shift-allocator-scheduler",
		],
	},
	{
		key: "enable_leaves",
		prefixes: ["/dashboard/leaves", "/leave-applications"],
	},
	{
		key: "enable_missions",
		prefixes: ["/dashboard/missions", "/missions"],
	},
	{
		key: "enable_expense_claims",
		prefixes: ["/dashboard/expense-claims", "/expense-claims"],
	},
	{
		key: "enable_employee_advances",
		prefixes: ["/employee-advances"],
	},
	{
		key: "enable_salary_slips",
		prefixes: ["/dashboard/salary-slips", "/salary-slips"],
	},
	{
		key: "enable_complaints",
		prefixes: ["/dashboard/complaints", "/employee-grievances"],
	},
	{
		key: "enable_meals",
		prefixes: ["/dashboard/meals", "/meal-plans", "/meal-coordinator"],
	},
	{
		key: "enable_appraisals",
		prefixes: ["/dashboard/appraisals", "/appraisals"],
	},
	{
		key: "enable_newsletters",
		prefixes: ["/dashboard/newsletters", "/newsletters"],
	},
	{
		key: "enable_events",
		prefixes: ["/dashboard/events", "/events"],
	},
	{
		key: "enable_imprest",
		prefixes: ["/dashboard/imprest", "/imprest"],
	},
]
const VISIBILITY_FALLBACK_ORDER = [
	"/home",
	"/dashboard/attendance",
	"/dashboard/leaves",
	"/dashboard/expense-claims",
	"/dashboard/salary-slips",
	"/dashboard/requests",
	"/profile",
	"/notifications",
	"/settings",
]
const CHUNK_LOAD_RETRY_KEY = "hrms:chunk-load-retried"
const CHUNK_LOAD_HARD_RETRY_KEY = "hrms:chunk-load-hard-retried"
let chunkRecoveryInProgress = false

function hasAllocatorShiftAccess(employee) {
	return Boolean(employee?.is_shift_allocator || employee?.is_shift_allocator_by_role)
}

function hasWeeklyShiftPlannerAccess(employee) {
	return Boolean(
		employee?.variable_shift
		|| employee?.has_rotational_shift
		|| employee?.needs_shift_registration
	)
}

function pathMatchesPrefix(path, prefix) {
	return path === prefix || path.startsWith(`${prefix}/`)
}

function isWeeklyShiftRoute(routeName, path) {
	return (
		WEEKLY_SHIFT_ROUTES.has(String(routeName || ""))
		|| WEEKLY_SHIFT_ROUTE_PREFIXES.some((prefix) => pathMatchesPrefix(path, prefix))
	)
}

function isPathAllowedByVisibility(path) {
	const visibility = employeeDeskVisibility.data || {}
	const rule = VISIBILITY_ROUTE_RULES.find((candidate) =>
		(candidate.prefixes || []).some((prefix) => pathMatchesPrefix(path, prefix))
	)

	if (!rule) return true
	return visibility?.[rule.key] !== false
}

function getVisibilityFallbackPath() {
	for (const path of VISIBILITY_FALLBACK_ORDER) {
		if (isPathAllowedByVisibility(path)) return path
	}
	return "/profile"
}

function isChunkLoadError(error) {
	const message = String(error?.message || "")
	return (
		message.includes("Failed to fetch dynamically imported module")
		|| message.includes("Importing a module script failed")
		|| message.includes("error loading dynamically imported module")
	)
}

async function hardRefreshAfterChunkError() {
	try {
		if ("serviceWorker" in navigator) {
			const registrations = await navigator.serviceWorker.getRegistrations()
			await Promise.all(registrations.map((registration) => registration.unregister()))
		}
	} catch (error) {
		console.warn("Failed to unregister service workers", error)
	}

	try {
		if ("caches" in window) {
			const cacheKeys = await caches.keys()
			await Promise.all(cacheKeys.map((cacheKey) => caches.delete(cacheKey)))
		}
	} catch (error) {
		console.warn("Failed to clear browser caches", error)
	}

	const nextURL = new URL(window.location.href)
	nextURL.searchParams.set("_hrms_reload", String(Date.now()))
	window.location.replace(nextURL.toString())
}

function recoverFromChunkLoadError() {
	if (chunkRecoveryInProgress) return
	chunkRecoveryInProgress = true

	if (!sessionStorage.getItem(CHUNK_LOAD_RETRY_KEY)) {
		sessionStorage.setItem(CHUNK_LOAD_RETRY_KEY, "1")
		window.location.reload()
		return
	}

	if (!sessionStorage.getItem(CHUNK_LOAD_HARD_RETRY_KEY)) {
		sessionStorage.setItem(CHUNK_LOAD_HARD_RETRY_KEY, "1")
		void hardRefreshAfterChunkError()
		return
	}

	sessionStorage.removeItem(CHUNK_LOAD_RETRY_KEY)
	sessionStorage.removeItem(CHUNK_LOAD_HARD_RETRY_KEY)
	chunkRecoveryInProgress = false
}

function applyLocaleSettings() {
	const bootLocale = String(window.frappe?.boot?.lang || "").toLowerCase()
	const locale = bootLocale.startsWith("fa") ? bootLocale : "fa"
	const dayjsLocale = locale.startsWith("fa") ? "fa" : "en"
	const textDirection = locale.startsWith("fa") ? "rtl" : "ltr"

	if (!window.frappe) window.frappe = {}
	if (!window.frappe.boot) window.frappe.boot = {}
	window.frappe.boot.lang = locale

	dayjs.locale(dayjsLocale)
	document.documentElement.setAttribute("lang", locale)
	document.documentElement.setAttribute("dir", textDirection)
}

const registerServiceWorker = async () => {
	window.frappePushNotification = new FrappePushNotification("hrms")

	if ("serviceWorker" in navigator) {
		let serviceWorkerURL = "/assets/hrms/frontend/sw.js"
		let config = ""

		try {
			config = await window.frappePushNotification.fetchWebConfig()
			serviceWorkerURL = `${serviceWorkerURL}?config=${encodeURIComponent(
				JSON.stringify(config)
			)}`
		} catch (err) {
			console.error("Failed to fetch FCM config", err)
		}

		navigator.serviceWorker
			.register(serviceWorkerURL, {
				type: "classic",
			})
			.then((registration) => {
				if (config) {
					window.frappePushNotification.initialize(registration).then(() => {
						console.log("Frappe Push Notification initialized")
					})
				}
			})
			.catch((err) => {
				console.error("Failed to register service worker", err)
			})
	} else {
		console.error("Service worker not enabled/supported by the browser")
	}
}

router.isReady().then(async () => {
	if (import.meta.env.DEV) {
		await frappeRequest({
			url: "/api/method/hrms.www.hrms.get_context_for_dev",
		}).then(async (values) => {
			if (!window.frappe) window.frappe = {}
			window.frappe.boot = values
		})
	}

	applyLocaleSettings()
	initializeColorMode()
	initializeAccentTheme()
	await translationsPlugin.isReady();
	registerServiceWorker()
	app.mount("#app")
})

router.beforeEach(async (to, _, next) => {
	let isLoggedIn = session.isLoggedIn

	try {
		// avoid re-fetching session/user data on every route change
		if (isLoggedIn && !userResource.data) await userResource.reload()
	} catch (error) {
		isLoggedIn = false
	}

	if (!isLoggedIn) {
		// password reset page is outside the PWA scope
		if (to.path === "/update-password") {
			return next(false)
		}
		if (to.name !== "Login") {
			return next({ name: "Login" })
		}
		return next()
	}

	if (to.name === "InvalidEmployee") return next()

	if (!employeeResource.data) await employeeResource.reload()
	if (!employeeDeskVisibility.data) await employeeDeskVisibility.reload()
	if (!employeeDeskPersonalization.data) await employeeDeskPersonalization.reload()
	if (!employeeDeskGlobalPersonalization.data) await employeeDeskGlobalPersonalization.reload()

	// user should be an employee to access the app since all views are employee specific
	const currentUser = userResource.data?.name || session.user
	if (
		!employeeResource?.data
		|| employeeResource?.data?.user_id !== currentUser
	) {
		return next({ name: "InvalidEmployee" })
	}

	if (isWeeklyShiftRoute(to.name, to.path) && !hasWeeklyShiftPlannerAccess(employeeResource?.data)) {
		return next({ name: "AttendanceDashboard" })
	}

	if (
		ALLOCATOR_SHIFT_ROUTES.has(String(to.name || ""))
		&& !hasAllocatorShiftAccess(employeeResource?.data)
	) {
		return next({ name: "AttendanceDashboard" })
	}

	if (!isPathAllowedByVisibility(to.path)) {
		const fallbackPath = getVisibilityFallbackPath()
		if (fallbackPath !== to.path) {
			return next({ path: fallbackPath })
		}
		return next({ name: "Profile" })
	}

	if (to.name === "Login") {
		return next({ name: "Home" })
	}

	return next()
})

router.afterEach(() => {
	sessionStorage.removeItem(CHUNK_LOAD_RETRY_KEY)
	sessionStorage.removeItem(CHUNK_LOAD_HARD_RETRY_KEY)
	chunkRecoveryInProgress = false
})

router.onError((error) => {
	if (isChunkLoadError(error)) {
		recoverFromChunkLoadError()
		return
	}
	console.error("Router navigation error", error)
})

window.addEventListener("unhandledrejection", (event) => {
	if (isChunkLoadError(event.reason)) {
		event.preventDefault()
		recoverFromChunkLoadError()
	}
})
