<template>
	<ion-page>
		<ion-content class="ion-no-padding">
			<ion-refresher slot="fixed" @ionRefresh="handlePullToRefresh">
				<ion-refresher-content
					pulling-text="برای بروزرسانی بکشید"
					refreshing-text="در حال بروزرسانی..."
				/>
			</ion-refresher>

			<div class="min-h-screen bg-slate-100">
				<div class="flex min-h-screen w-full">
					<aside
						class="hidden w-72 shrink-0 flex-col border-l border-slate-200 bg-white"
						:class="desktopSidebarOpen ? 'lg:flex' : 'lg:hidden'"
					>
						<div class="flex items-center gap-3 border-b border-slate-200 px-6 py-5">
							<div
								class="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-amber-600 to-orange-600 text-white shadow"
							>
								<FeatherIcon name="grid" class="h-5 w-5" />
							</div>
							<div>
								<div class="text-sm font-semibold text-slate-500">{{ __("Hamyar") }}</div>
								<div class="text-lg font-bold text-slate-900">{{ __("همیار") }}</div>
							</div>
						</div>

						<div class="border-b border-slate-100 p-4">
							<div class="flex items-center gap-3 rounded-2xl bg-slate-50 p-3">
								<Avatar
									:image="profileImage"
									:label="employeeName"
									size="xl"
								/>
								<div class="min-w-0">
									<div class="truncate text-sm font-semibold text-slate-900">
										{{ employeeName }}
									</div>
									<div class="truncate text-xs text-slate-500">
										{{ employeeRole }}
									</div>
								</div>
							</div>
						</div>

						<nav class="flex-1 space-y-4 overflow-y-auto px-4 py-4">
							<div v-for="group in menuGroups" :key="group.title">
								<p class="mb-2 px-3 text-[11px] font-bold tracking-wide text-slate-400">
									{{ group.title }}
								</p>
								<div class="space-y-1">
									<router-link
										v-for="item in group.items"
										:key="item.route"
										:to="item.route"
										class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition"
										:class="
											isActive(item.route)
												? 'bg-amber-50 text-amber-700'
												: 'text-slate-600 hover:bg-slate-100'
										"
									>
										<FeatherIcon :name="item.icon" class="h-4 w-4" />
										<span class="flex-1">{{ item.label }}</span>
										<span
											v-if="item.badge"
											class="inline-flex min-w-6 items-center justify-center rounded-full bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-700"
										>
											{{ toPersianDigits(item.badge) }}
										</span>
									</router-link>
								</div>
							</div>
						</nav>
					</aside>

					<div class="flex min-w-0 flex-1 flex-col">
						<header class="sticky top-0 z-10 border-b border-slate-200 bg-white/95 backdrop-blur">
							<div class="flex items-center gap-3 px-4 py-3 md:px-6">
								<Button
									variant="ghost"
									class="!rounded-xl"
									@click="toggleSidebar"
								>
									<FeatherIcon name="menu" class="h-5 w-5" />
								</Button>
								<div class="min-w-0">
									<h2 class="truncate text-base font-bold text-slate-900 md:text-lg" data-tour="header-title">
										{{ props.pageTitle || __("Hamyar") }}
									</h2>
									<div class="truncate text-xs text-slate-500 md:text-sm">
										{{ todayLabel }}
									</div>
								</div>
								<div class="mr-auto flex items-center gap-2">
									<router-link
										:to="{ name: 'Notifications' }"
										class="relative rounded-xl border border-slate-200 p-2.5"
										data-tour="notifications-link"
									>
										<FeatherIcon name="bell" class="h-4 w-4 text-slate-600" />
										<span
											v-if="unreadNotificationsCount.data"
											class="absolute -right-2 -top-2 inline-flex min-w-5 items-center justify-center rounded-full bg-red-600 px-1.5 py-0.5 text-[10px] font-bold text-white"
										>
											{{ unreadCountLabel }}
										</span>
									</router-link>
									<router-link
										:to="{ name: 'Profile' }"
										class="flex items-center gap-2 rounded-xl border border-slate-200 px-2 py-1.5"
										data-tour="profile-link"
									>
										<Avatar
											:image="profileImage"
											:label="employeeName"
											size="md"
										/>
										<div class="hidden sm:block text-right leading-tight">
											<div class="max-w-32 truncate text-xs font-semibold text-slate-800">
												{{ employeeName }}
											</div>
											<div class="text-[11px] text-slate-500">
												{{ __("کاربر") }}
											</div>
										</div>
									</router-link>
								</div>
							</div>
						</header>

						<div
							class="flex flex-col min-h-screen w-full px-0 md:pt-4 md:pb-6"
							data-tour="page-content"
						>
							<slot name="body"></slot>
						</div>
					</div>
				</div>
			</div>
		</ion-content>

		<Teleport to="body">
			<Transition name="fade">
				<div
					v-if="sidebarOpen"
					class="fixed inset-0 z-40 bg-black/40 lg:hidden"
					@click="sidebarOpen = false"
				/>
			</Transition>
			<Transition name="slide-right">
				<aside
					v-if="sidebarOpen"
					class="fixed top-0 right-0 z-50 flex h-full w-72 flex-col bg-white shadow-xl lg:hidden"
				>
					<div class="flex items-center justify-between border-b border-slate-200 px-4 py-4">
						<div class="text-base font-bold text-slate-900">{{ __("منو") }}</div>
						<Button variant="ghost" class="!rounded-xl" @click="sidebarOpen = false">
							<FeatherIcon name="x" class="h-5 w-5" />
						</Button>
					</div>
					<nav class="flex-1 space-y-4 overflow-y-auto px-4 py-4">
						<div v-for="group in menuGroups" :key="`${group.title}-mobile`">
							<p class="mb-2 px-3 text-[11px] font-bold tracking-wide text-slate-400">
								{{ group.title }}
							</p>
							<div class="space-y-1">
								<router-link
									v-for="item in group.items"
									:key="`mobile-${item.route}`"
									:to="item.route"
									class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition"
									:class="
										isActive(item.route)
											? 'bg-amber-50 text-amber-700'
											: 'text-slate-600 hover:bg-slate-100'
									"
									@click="onSidebarItemClick(true)"
								>
									<FeatherIcon :name="item.icon" class="h-4 w-4" />
									<span class="flex-1">{{ item.label }}</span>
									<span
										v-if="item.badge"
										class="inline-flex min-w-6 items-center justify-center rounded-full bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-700"
									>
										{{ toPersianDigits(item.badge) }}
									</span>
								</router-link>
							</div>
						</div>
					</nav>
				</aside>
			</Transition>
		</Teleport>
	</ion-page>
</template>

<script setup>
import { computed, inject, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { useRoute } from "vue-router"
import { IonContent, IonPage, IonRefresher, IonRefresherContent } from "@ionic/vue"
import { FeatherIcon, Avatar } from "frappe-ui"

import { unreadNotificationsCount } from "@/data/notifications"
import { employeeDeskVisibility, layoutHasImprestAccess, layoutUnreadNewsletterCount } from "@/data/layout"
import { buildNavbarGroups } from "@/data/navigation"
import { employeeDeskGlobalPersonalization } from "@/data/personalization"
import { formatJalaliDate, toPersianDigits } from "@/utils/jalali"

const user = inject("$user")
const employee = inject("$employee")
const __ = inject("$translate")
const route = useRoute()

const sidebarOpen = ref(false)
const desktopSidebarOpen = ref(true)
watch(
	() => route.path,
	() => {
		sidebarOpen.value = false
	}
)

const props = defineProps({
	pageTitle: {
		type: String,
		required: false,
		default: "",
	},
})

const employeeName = computed(
	() => employee.data?.employee_name || user.data?.full_name || __("کاربر")
)
const employeeRole = computed(
	() => employee.data?.designation || employee.data?.department || __("کارمند")
)
const profileImage = computed(() => employee.data?.image || user.data?.user_image || "")
const todayLabel = computed(() => formatJalaliDate(new Date(), { withWeekday: true }))
const unreadCountLabel = computed(() => {
	const count = Number(unreadNotificationsCount.data || 0)
	if (!count) return ""
	return toPersianDigits(count > 99 ? "99+" : String(count))
})

const canSeeAllocatorShiftTools = computed(() => {
	return Boolean(employee.data?.is_shift_allocator || employee.data?.is_shift_allocator_by_role)
})

const canSeeWeeklyShiftPlanner = computed(() => {
	return Boolean(
		employee.data?.variable_shift
			|| employee.data?.has_rotational_shift
			|| employee.data?.needs_shift_registration
	)
})

const sidebarPreferences = computed(() => {
	return employeeDeskGlobalPersonalization.data?.preferences || {}
})

const menuGroups = computed(() => {
	return buildNavbarGroups(__, {
		unreadNewsletterCount: layoutUnreadNewsletterCount.value,
		hasImprestAccess: layoutHasImprestAccess.value,
		canSeeAllocatorShiftTools: canSeeAllocatorShiftTools.value,
		canSeeWeeklyShiftPlanner: canSeeWeeklyShiftPlanner.value,
		visibility: employeeDeskVisibility.data || {},
		hiddenRoutes: sidebarPreferences.value.hidden_sidebar_routes || [],
		routeOrder: sidebarPreferences.value.sidebar_order_routes || [],
		customLabels: sidebarPreferences.value.sidebar_labels || {},
	})
})

function onSidebarItemClick(closeMobile = false) {
	if (closeMobile) {
		sidebarOpen.value = false
	}
}

function isActive(path) {
	return route.path === path || route.path.startsWith(`${path}/`)
}

function toggleSidebar() {
	if (window.innerWidth >= 1024) {
		desktopSidebarOpen.value = !desktopSidebarOpen.value
		return
	}
	sidebarOpen.value = true
}

function handlePullToRefresh(event) {
	const complete = event?.detail?.complete || event?.target?.complete
	if (typeof complete === "function") {
		complete.call(event?.detail || event?.target)
	}

	setTimeout(() => {
		window.location.reload()
	}, 120)
}

function handleGlobalNavigationUpdated() {
	employeeDeskGlobalPersonalization.reload()
}

onMounted(() => {
	if (typeof window === "undefined") return
	window.addEventListener("hrms:global-navigation-updated", handleGlobalNavigationUpdated)
})

onBeforeUnmount(() => {
	if (typeof window === "undefined") return
	window.removeEventListener("hrms:global-navigation-updated", handleGlobalNavigationUpdated)
})
</script>
