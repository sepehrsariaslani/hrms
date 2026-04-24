<template>
	<ion-page>
		<ion-content class="ion-padding">
			<div class="flex flex-col min-h-screen w-full">
				<div class="w-full max-w-7xl mx-auto px-0 md:px-4">
					<header
						class="flex flex-row bg-white shadow-sm py-4 px-3 items-center justify-between border-b sticky top-0 z-10 md:rounded-b-xl"
					>
						<div class="flex flex-row items-center">
							<Button variant="ghost" class="!pl-0 hover:bg-white" @click="router.back()">
								<FeatherIcon name="chevron-left" class="h-5 w-5" />
							</Button>
							<h2 class="text-xl font-semibold text-gray-900">آموزش</h2>
						</div>
					</header>

					<div class="flex flex-col gap-4 mt-5 p-4">
						<div class="rounded-xl bg-white p-4 shadow-sm">
							<h3 class="text-base font-semibold text-gray-900">راهنمای شروع کار</h3>
							<p class="mt-2 text-sm leading-6 text-gray-600">
								می‌توانید آموزش اولیه را الان ببینید، آن را کامل ببندید یا هر زمان دوباره باز کنید.
							</p>
							<div class="mt-4 flex flex-wrap gap-2">
								<Button variant="solid" @click="openInAppGuide(generalGuide)">
									شروع آموزش اولیه
								</Button>
								<Button variant="outline" @click="reopenAutoGuide">
									نمایش دوباره آموزش خودکار
								</Button>
								<Button variant="ghost" @click="disableAutoGuide">
									بستن آموزش خودکار
								</Button>
							</div>
						</div>

						<div
							v-for="guide in moduleGuides"
							:key="guide.key"
							class="rounded-xl bg-white shadow-sm"
						>
							<button
								type="button"
								class="w-full p-4 text-right flex items-center justify-between"
								@click="toggleGuide(guide.key)"
							>
								<div class="flex flex-col gap-1">
									<div class="text-base font-semibold text-gray-900">{{ guide.title }}</div>
									<div class="text-sm text-gray-600">{{ guide.shortDescription }}</div>
								</div>
								<FeatherIcon
									:name="expandedGuideKey === guide.key ? 'chevron-up' : 'chevron-down'"
									class="h-5 w-5 text-gray-500"
								/>
							</button>

							<div v-if="expandedGuideKey === guide.key" class="px-4 pb-4">
								<ol class="space-y-2 text-sm text-gray-700 list-decimal pr-4">
									<li v-for="step in guide.steps" :key="step">{{ step }}</li>
								</ol>

								<div class="mt-4 flex flex-wrap items-center gap-2">
									<Button variant="solid" @click="openInAppGuide(guide)">
										شروع راهنمای داخل برنامه
									</Button>
									<Button variant="outline" @click="goToModule(guide.route)">
										رفتن به ماژول
									</Button>
									<Button
										variant="ghost"
										@click="toggleCompleted(guide.key)"
									>
										{{ isCompleted(guide.key) ? "علامت‌گذاری به‌عنوان ناتمام" : "علامت‌گذاری به‌عنوان تکمیل‌شده" }}
									</Button>
								</div>
								<div
									v-if="isCompleted(guide.key)"
									class="mt-2 text-xs font-medium text-emerald-700"
								>
									این آموزش برای شما به‌عنوان تکمیل‌شده ذخیره شده است.
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { FeatherIcon, toast } from "frappe-ui"
import { IonPage, IonContent } from "@ionic/vue"
import { computed, nextTick, ref } from "vue"
import { useRoute, useRouter } from "vue-router"

import {
	ONBOARDING_OPEN_EVENT,
	ONBOARDING_STORAGE_KEY,
	TRAINING_GUIDES,
	getGuideByKey,
} from "@/data/trainingGuides"

const TRAINING_COMPLETED_KEY = "hrms:training-completed:v1"

const router = useRouter()
const route = useRoute()

const expandedGuideKey = ref("employee-advance")
const completedGuides = ref(loadCompletedGuides())

const generalGuide = getGuideByKey("general")

const moduleGuides = computed(() =>
	TRAINING_GUIDES.filter((guide) => guide.key !== "general")
)

function loadCompletedGuides() {
	try {
		return JSON.parse(localStorage.getItem(TRAINING_COMPLETED_KEY) || "{}")
	} catch (_) {
		return {}
	}
}

function saveCompletedGuides() {
	try {
		localStorage.setItem(
			TRAINING_COMPLETED_KEY,
			JSON.stringify(completedGuides.value || {})
		)
	} catch (_) {
		return
	}
}

function toggleGuide(guideKey) {
	expandedGuideKey.value = expandedGuideKey.value === guideKey ? null : guideKey
}

function isCompleted(guideKey) {
	return Boolean(completedGuides.value[guideKey])
}

function toggleCompleted(guideKey) {
	completedGuides.value = {
		...completedGuides.value,
		[guideKey]: !completedGuides.value[guideKey],
	}
	saveCompletedGuides()
}

function disableAutoGuide() {
	try {
		localStorage.setItem(ONBOARDING_STORAGE_KEY, "1")
	} catch (_) {
		return
	}
	toast({
		title: "انجام شد",
		text: "نمایش خودکار آموزش اولیه غیرفعال شد.",
		icon: "check-circle",
		position: "bottom-center",
		iconClasses: "text-green-600",
	})
}

async function reopenAutoGuide() {
	try {
		localStorage.removeItem(ONBOARDING_STORAGE_KEY)
	} catch (_) {
		return
	}
	await openInAppGuide(generalGuide)
}

async function goToModule(path) {
	if (!path) return
	if (route.path === path) return
	await router.push(path)
}

async function openInAppGuide(guide) {
	if (!guide) return
	if (guide.route && route.path !== guide.route) {
		await router.push(guide.route)
	}
	await nextTick()
	setTimeout(() => {
		window.dispatchEvent(
			new CustomEvent(ONBOARDING_OPEN_EVENT, {
				detail: { guideKey: guide.key },
			})
		)
	}, 250)
}
</script>
