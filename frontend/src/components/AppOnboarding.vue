<template>
	<button
		v-if="showHelpLauncher && !isOpen"
		type="button"
		class="fixed right-4 z-[950] h-11 w-11 rounded-full border border-gray-200 bg-white text-gray-700 shadow-lg transition hover:bg-gray-50 bottom-[calc(5.5rem+env(safe-area-inset-bottom))]"
		@click="startGuide()"
		aria-label="باز کردن راهنمای سریع"
	>
		<FeatherIcon name="help-circle" class="mx-auto h-5 w-5" />
	</button>

	<div v-if="isOpen" class="fixed inset-0 z-[1000]">
		<div class="absolute inset-0 bg-slate-950/60" @click="closeGuide"></div>
		<div
			v-if="highlightStyle"
			class="absolute rounded-xl border-2 border-white/90 shadow-[0_0_0_9999px_rgba(15,23,42,0.62)] transition-all duration-200"
			:style="highlightStyle"
		></div>

		<div
			class="absolute left-1/2 w-[min(23rem,calc(100vw-1.5rem))] -translate-x-1/2 rounded-2xl bg-white p-4 shadow-2xl bottom-[calc(1rem+env(safe-area-inset-bottom))]"
		>
			<div class="text-xs font-medium text-gray-500">
				{{ `مرحله ${currentStepIndex + 1} از ${currentSteps.length}` }}
			</div>
			<h3 class="mt-1 text-lg font-semibold text-gray-900">{{ currentStep?.title }}</h3>
			<p class="mt-2 text-sm leading-6 text-gray-600">{{ currentStep?.description }}</p>

			<div class="mt-4 flex items-center justify-end gap-2">
				<Button variant="ghost" @click="closeGuide">بستن</Button>
				<Button variant="subtle" :disabled="currentStepIndex === 0" @click="goToPrevious">
					قبلی
				</Button>
				<Button variant="solid" @click="goToNext">
					{{ currentStepIndex === currentSteps.length - 1 ? "پایان" : "بعدی" }}
				</Button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { useRoute } from "vue-router"

import { session } from "@/data/session"
import {
	ONBOARDING_OPEN_EVENT,
	ONBOARDING_STORAGE_KEY,
	getGuideByKey,
	getGuideByPath,
} from "@/data/trainingGuides"

const route = useRoute()

const HIGHLIGHT_PADDING = 8

const autoGuideStarted = ref(false)
const isOpen = ref(false)
const currentStepIndex = ref(0)
const currentSteps = ref([])
const highlightStyle = ref(null)
const highlightTimer = ref(null)
const selectedGuideKey = ref(null)

const hiddenRouteNames = new Set(["Login", "InvalidEmployee"])

const showHelpLauncher = computed(() => {
	const routeName = String(route.name || "")
	return session.isLoggedIn && !hiddenRouteNames.has(routeName)
})

const activeGuide = computed(() => {
	if (selectedGuideKey.value) {
		return getGuideByKey(selectedGuideKey.value)
	}
	return getGuideByPath(route.path)
})

const currentStep = computed(() => currentSteps.value[currentStepIndex.value])

function isElementVisible(target) {
	if (!target) return false

	const style = window.getComputedStyle(target)
	if (style.display === "none" || style.visibility === "hidden") return false

	const rect = target.getBoundingClientRect()
	if (rect.width === 0 && rect.height === 0) return false

	// Ionic keeps old pages in DOM with this class; skip those.
	const hiddenPage = target.closest(".ion-page-hidden")
	if (hiddenPage) return false

	return true
}

function getStepTarget(selector) {
	if (!selector) return null
	const targets = Array.from(document.querySelectorAll(selector))
	return targets.find((target) => isElementVisible(target)) || null
}

function hasSeenGuide() {
	try {
		return localStorage.getItem(ONBOARDING_STORAGE_KEY) === "1"
	} catch (_) {
		return false
	}
}

function markGuideAsSeen() {
	try {
		localStorage.setItem(ONBOARDING_STORAGE_KEY, "1")
	} catch (_) {
		return
	}
}

function getOverviewStep() {
	if (activeGuide.value) {
		return {
			id: "guide-overview",
			title: activeGuide.value.title,
			description: activeGuide.value.shortDescription,
		}
	}

	return {
		id: "generic-overview",
		title: "راهنمای سریع صفحه",
		description:
			"در این صفحه می‌توانید اطلاعات مرتبط با ماژول فعلی را ببینید و عملیات موردنیاز خود را انجام دهید.",
	}
}

function getCommonGuideSteps() {
	return [
		{
			id: "header",
			title: "عنوان صفحه",
			description: "عنوان صفحه نشان می‌دهد در کدام بخش از نرم‌افزار هستید.",
			selector: '[data-tour="header-title"]',
		},
		{
			id: "notifications",
			title: "اعلان‌ها",
			description: "از این بخش هشدارهای جدید را می‌بینید و وارد جزئیات هر مورد می‌شوید.",
			selector: '[data-tour="notifications-link"]',
		},
		{
			id: "profile",
			title: "پروفایل",
			description: "برای مشاهده اطلاعات کاربر، تنظیمات و ورود به صفحه آموزش از این بخش استفاده کنید.",
			selector: '[data-tour="profile-link"]',
		},
		{
			id: "bottom-tabs",
			title: "ناوبری اصلی",
			description: "تب‌های پایین، سریع‌ترین راه جابه‌جایی بین ماژول‌های اصلی هستند.",
			selector: '[data-tour="bottom-tabs"]',
		},
		{
			id: "page-content",
			title: "ناحیه کاری",
			description: "تمام فرم‌ها، لیست‌ها و اقدام‌های اصلی شما در این بخش نمایش داده می‌شود.",
			selector: '[data-tour="page-content"]',
		},
	]
}

function buildSteps() {
	const steps = [getOverviewStep()]
	const shouldShowCommonGuide = !activeGuide.value || activeGuide.value.key === "general"
	if (shouldShowCommonGuide) {
		steps.push(...getCommonGuideSteps())
	}

	const moduleSteps = activeGuide.value?.onboardingSteps || []
	steps.push(...moduleSteps)
	steps.push({
		id: "reopen-help",
		title: "بازکردن دوباره راهنما",
		description:
			"هر زمان خواستید می‌توانید با دکمه علامت سوال پایین صفحه یا از بخش «آموزش»، این راهنما را دوباره باز کنید.",
	})

	return steps
}

function resolveAvailableSteps() {
	const steps = buildSteps().filter((step) => {
		if (!step.selector) return true
		return Boolean(getStepTarget(step.selector))
	})

	return steps.length
		? steps
		: [
				{
					id: "fallback",
					title: "راهنمای سریع",
					description:
						"الان راهنمای گرافیکی برای این صفحه در دسترس نیست، اما می‌توانید از بخش «آموزش» مراحل کامل را ببینید.",
				},
		  ]
}

function updateHighlight() {
	if (!isOpen.value) return

	const step = currentStep.value
	if (!step?.selector) {
		highlightStyle.value = null
		return
	}

	const target = getStepTarget(step.selector)
	if (!target) {
		highlightStyle.value = null
		return
	}

	const rect = target.getBoundingClientRect()
	const isInsideViewport =
		rect.top >= 0 &&
		rect.left >= 0 &&
		rect.bottom <= window.innerHeight &&
		rect.right <= window.innerWidth

	if (!isInsideViewport) {
		target.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" })
	}

	if (highlightTimer.value) {
		clearTimeout(highlightTimer.value)
	}

	highlightTimer.value = setTimeout(() => {
		const freshRect = target.getBoundingClientRect()
		highlightStyle.value = {
			top: `${Math.max(freshRect.top - HIGHLIGHT_PADDING, 6)}px`,
			left: `${Math.max(freshRect.left - HIGHLIGHT_PADDING, 6)}px`,
			width: `${Math.max(freshRect.width + HIGHLIGHT_PADDING * 2, 24)}px`,
			height: `${Math.max(freshRect.height + HIGHLIGHT_PADDING * 2, 24)}px`,
		}
	}, 130)
}

async function startGuide(options = {}) {
	if (!showHelpLauncher.value) return

	selectedGuideKey.value = options.guideKey || null

	await nextTick()
	currentSteps.value = resolveAvailableSteps()
	currentStepIndex.value = 0
	isOpen.value = true

	await nextTick()
	updateHighlight()
}

function closeGuide() {
	isOpen.value = false
	highlightStyle.value = null
	selectedGuideKey.value = null
	markGuideAsSeen()
}

function goToPrevious() {
	if (currentStepIndex.value === 0) return
	currentStepIndex.value -= 1
}

function goToNext() {
	if (currentStepIndex.value >= currentSteps.value.length - 1) {
		closeGuide()
		return
	}
	currentStepIndex.value += 1
}

function handleOpenGuideEvent(event) {
	startGuide({ guideKey: event?.detail?.guideKey })
}

function handleResizeOrScroll() {
	if (!isOpen.value) return
	updateHighlight()
}

watch(
	() => currentStepIndex.value,
	async () => {
		if (!isOpen.value) return
		await nextTick()
		updateHighlight()
	}
)

watch(
	() => route.fullPath,
	async () => {
		if (!isOpen.value) return
		await nextTick()
		currentSteps.value = resolveAvailableSteps()
		currentStepIndex.value = 0
		updateHighlight()
	}
)

watch(
	() => showHelpLauncher.value,
	(canShow) => {
		if (!canShow || autoGuideStarted.value || hasSeenGuide()) return

		autoGuideStarted.value = true
		setTimeout(() => startGuide(), 450)
	},
	{ immediate: true }
)

onMounted(() => {
	window.addEventListener("resize", handleResizeOrScroll)
	window.addEventListener("scroll", handleResizeOrScroll, true)
	window.addEventListener(ONBOARDING_OPEN_EVENT, handleOpenGuideEvent)
})

onBeforeUnmount(() => {
	window.removeEventListener("resize", handleResizeOrScroll)
	window.removeEventListener("scroll", handleResizeOrScroll, true)
	window.removeEventListener(ONBOARDING_OPEN_EVENT, handleOpenGuideEvent)
	if (highlightTimer.value) {
		clearTimeout(highlightTimer.value)
	}
})
</script>
