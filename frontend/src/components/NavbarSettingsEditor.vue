<template>
	<div class="flex flex-col gap-4">
		<div class="rounded bg-white p-4">
			<div class="mb-3 flex items-start justify-between gap-3">
				<div>
					<div class="text-sm font-bold text-gray-900">{{ __("Navbar Designer") }}</div>
					<div class="mt-1 text-xs text-gray-500">
						{{ __("Bottom navbar editing for mobile users with easier add/remove workflow.") }}
					</div>
				</div>
				<div class="flex items-center gap-2">
					<Button
						variant="outline"
						class="py-3 text-sm"
						:disabled="navbarLoading || navbarSaving || !canCustomizeEmployeeDeskGlobal"
						@click="handleNavbarReset"
					>
						{{ __("Reset") }}
					</Button>
					<Button
						variant="solid"
						class="py-3 text-sm"
						:disabled="navbarLoading || navbarSaving || !canCustomizeEmployeeDeskGlobal || !navbarHasUnsavedChanges"
						@click="saveNavbarDraft"
					>
						{{ __("Save Navbar for Everyone") }}
					</Button>
				</div>
			</div>

			<div
				v-if="!canCustomizeEmployeeDeskGlobal"
				class="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700"
			>
				{{ __("Only the site administrator can save global navbar settings.") }}
			</div>

			<div v-if="navbarLoading" class="mb-3 flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-600">
				<LoadingIndicator class="h-3 w-3 text-gray-700" />
				<span>{{ __("Loading navbar settings...") }}</span>
			</div>

			<div class="mb-3 rounded-xl border border-gray-200 p-3">
				<div class="mb-2 text-xs font-bold text-gray-600">{{ __("Preview") }}</div>
				<div class="flex items-center gap-2 overflow-x-auto rounded-xl border border-gray-200 bg-white px-2 py-2">
					<div
						v-for="item in navbarPreviewItems"
						:key="`preview-${item.key}`"
						class="flex min-w-[70px] flex-col items-center gap-1 rounded-lg px-2 py-1 text-center text-[11px] text-gray-700"
					>
						<component v-if="item.icon" :is="item.icon" class="h-4 w-4" />
						<FeatherIcon v-else :name="item.featherIcon" class="h-4 w-4" />
						<div class="line-clamp-1">{{ item.title }}</div>
					</div>
					<div
						v-if="navbarVisibleCount < MAX_VISIBLE_TABS"
						class="flex min-w-[70px] flex-col items-center gap-1 rounded-lg border border-dashed border-emerald-300 bg-emerald-50 px-2 py-1 text-center text-[11px] text-emerald-700"
					>
						<div class="flex h-4 w-4 items-center justify-center rounded-full border border-emerald-400 text-[10px]">+</div>
						<div>{{ __("Add") }}</div>
					</div>
				</div>
				<div class="mt-2 text-[11px] text-gray-500">
					{{ __("Visible tabs: {0} (min {1}, max {2})", [navbarVisibleCount, MIN_VISIBLE_TABS, MAX_VISIBLE_TABS]) }}
				</div>
			</div>

			<div class="mb-3">
				<div class="flex items-center justify-between gap-2">
					<div class="text-xs font-bold text-gray-600">{{ __("Visible Navbar Items") }}</div>
					<Button
						variant="outline"
						class="!px-2 !py-1 text-xs"
						:disabled="!canOpenNavbarAddMenu"
						@click="showNavbarAddMenu = !showNavbarAddMenu"
					>
						{{ __("Add Item +") }}
					</Button>
				</div>
				<div
					v-if="showNavbarAddMenu"
					class="mt-2 rounded-xl border border-gray-200 bg-white p-2"
				>
					<div v-if="navbarAddableGroups.length" class="space-y-2">
						<div v-for="group in navbarAddableGroups" :key="`navbar-add-${group.key}`" class="space-y-1">
							<div class="px-1 text-[10px] font-bold text-gray-400">{{ group.title }}</div>
							<button
								v-for="item in group.items"
								:key="`navbar-add-item-${item.key}`"
								type="button"
								class="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-right text-xs text-gray-700 hover:bg-gray-100"
								@click="addNavbarItem(item.key)"
							>
								<component v-if="item.icon" :is="item.icon" class="h-4 w-4" />
								<FeatherIcon v-else :name="item.featherIcon" class="h-4 w-4" />
								<span class="flex-1">{{ item.title }}</span>
							</button>
						</div>
					</div>
					<div v-else class="px-2 py-1 text-xs text-gray-500">{{ __("No hidden items are available to add.") }}</div>
				</div>
			</div>

			<div class="space-y-1">
				<div
					v-for="item in navbarVisibleItems"
					:key="`navbar-visible-${item.key}`"
					class="flex items-center gap-2 rounded-lg border border-gray-100 bg-white px-2 py-1.5"
				>
					<component v-if="item.icon" :is="item.icon" class="h-4 w-4 shrink-0" />
					<FeatherIcon v-else :name="item.featherIcon" class="h-4 w-4 shrink-0" />
					<div class="min-w-0 flex-1 text-xs font-medium text-gray-800">{{ item.title }}</div>
					<div class="flex items-center gap-1">
						<button
							type="button"
							class="rounded border border-gray-200 bg-white px-1.5 py-0.5 text-[10px] text-gray-600"
							@click="removeNavbarItem(item.key)"
						>
							-
						</button>
						<button
							type="button"
							class="rounded border border-gray-200 bg-white px-1.5 py-0.5 text-[10px] text-gray-600"
							@click="renameNavbarItem(item)"
						>
							✎
						</button>
						<button
							type="button"
							class="rounded border border-gray-200 bg-white px-1.5 py-0.5 text-[10px] text-gray-600"
							@click="moveNavbarItem(item.key, -1)"
						>
							↑
						</button>
						<button
							type="button"
							class="rounded border border-gray-200 bg-white px-1.5 py-0.5 text-[10px] text-gray-600"
							@click="moveNavbarItem(item.key, 1)"
						>
							↓
						</button>
					</div>
				</div>
			</div>
		</div>

		<div class="rounded bg-white p-4">
			<div class="mb-3 flex items-start justify-between gap-3">
				<div>
					<div class="text-sm font-bold text-gray-900">{{ __("Sidebar Designer") }}</div>
					<div class="mt-1 text-xs text-gray-500">
						{{ __("Edit sidebar items for all users using add/remove, rename and reorder controls.") }}
					</div>
				</div>
				<div class="flex items-center gap-2">
					<Button
						variant="outline"
						class="py-3 text-sm"
						:disabled="sidebarLoading || sidebarSaving || !canCustomizeEmployeeDeskGlobal"
						@click="handleSidebarReset"
					>
						{{ __("Reset") }}
					</Button>
					<Button
						variant="solid"
						class="py-3 text-sm"
						:disabled="sidebarLoading || sidebarSaving || !canCustomizeEmployeeDeskGlobal || !sidebarHasUnsavedChanges"
						@click="saveSidebarDraft"
					>
						{{ __("Save Sidebar for Everyone") }}
					</Button>
				</div>
			</div>

			<div
				v-if="!canCustomizeEmployeeDeskGlobal"
				class="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700"
			>
				{{ __("Only the site administrator can save global sidebar settings.") }}
			</div>

			<div v-if="sidebarLoading" class="mb-3 flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-600">
				<LoadingIndicator class="h-3 w-3 text-gray-700" />
				<span>{{ __("Loading sidebar settings...") }}</span>
			</div>

			<div class="mb-3">
				<div class="flex items-center justify-between gap-2">
					<div class="text-xs font-bold text-gray-600">{{ __("Visible Sidebar Items") }}</div>
					<Button
						variant="outline"
						class="!px-2 !py-1 text-xs"
						:disabled="!sidebarAddableGroups.length"
						@click="showSidebarAddMenu = !showSidebarAddMenu"
					>
						{{ __("Add Item +") }}
					</Button>
				</div>
				<div
					v-if="showSidebarAddMenu"
					class="mt-2 rounded-xl border border-gray-200 bg-white p-2"
				>
					<div v-if="sidebarAddableGroups.length" class="space-y-2">
						<div v-for="group in sidebarAddableGroups" :key="`sidebar-add-${group.title}`" class="space-y-1">
							<div class="px-1 text-[10px] font-bold text-gray-400">{{ group.title }}</div>
							<button
								v-for="item in group.items"
								:key="`sidebar-add-item-${item.route}`"
								type="button"
								class="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-right text-xs text-gray-700 hover:bg-gray-100"
								@click="showSidebarRoute(item.route)"
							>
								<FeatherIcon :name="item.icon" class="h-4 w-4" />
								<span class="flex-1">{{ item.label }}</span>
							</button>
						</div>
					</div>
					<div v-else class="px-2 py-1 text-xs text-gray-500">{{ __("No hidden sidebar items are available to add.") }}</div>
				</div>
			</div>

			<div class="space-y-3">
				<div
					v-for="group in sidebarVisibleGroups"
					:key="`sidebar-group-${group.title}`"
					class="rounded-xl border border-gray-200 p-3"
				>
					<div class="mb-2 text-xs font-bold text-gray-500">{{ group.title }}</div>
					<div class="space-y-1">
						<div
							v-for="item in group.items"
							:key="`sidebar-item-${item.route}`"
							class="flex items-center gap-2 rounded-lg border border-gray-100 bg-white px-2 py-1.5"
						>
							<FeatherIcon :name="item.icon" class="h-4 w-4 shrink-0" />
							<div class="min-w-0 flex-1 text-xs font-medium text-gray-800">{{ item.label }}</div>
							<div class="flex items-center gap-1">
								<button
									type="button"
									class="rounded border border-gray-200 bg-white px-1.5 py-0.5 text-[10px] text-gray-600"
									@click="hideSidebarRoute(item.route)"
								>
									-
								</button>
								<button
									type="button"
									class="rounded border border-gray-200 bg-white px-1.5 py-0.5 text-[10px] text-gray-600"
									@click="renameSidebarRoute(item.route, item.label)"
								>
									✎
								</button>
								<button
									type="button"
									class="rounded border border-gray-200 bg-white px-1.5 py-0.5 text-[10px] text-gray-600"
									@click="moveSidebarRoute(item.route, -1)"
								>
									↑
								</button>
								<button
									type="button"
									class="rounded border border-gray-200 bg-white px-1.5 py-0.5 text-[10px] text-gray-600"
									@click="moveSidebarRoute(item.route, 1)"
								>
									↓
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from "vue"
import { Button, FeatherIcon, LoadingIndicator, toast } from "frappe-ui"

import AppraisalIcon from "@/components/icons/AppraisalIcon.vue"
import AttendanceIcon from "@/components/icons/AttendanceIcon.vue"
import ComplaintIcon from "@/components/icons/ComplaintIcon.vue"
import EmployeeAdvanceIcon from "@/components/icons/EmployeeAdvanceIcon.vue"
import EventIcon from "@/components/icons/EventIcon.vue"
import ExpenseIcon from "@/components/icons/ExpenseIcon.vue"
import HomeIcon from "@/components/icons/HomeIcon.vue"
import ImprestIcon from "@/components/icons/ImprestIcon.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import MealIcon from "@/components/icons/MealIcon.vue"
import MissionIcon from "@/components/icons/MissionIcon.vue"
import NewsletterIcon from "@/components/icons/NewsletterIcon.vue"
import SalaryIcon from "@/components/icons/SalaryIcon.vue"
import ShiftIcon from "@/components/icons/ShiftIcon.vue"
import { employeeDeskVisibility, layoutHasImprestAccess, layoutUnreadNewsletterCount } from "@/data/layout"
import { buildNavbarGroups } from "@/data/navigation"
import {
	canCustomizeEmployeeDeskGlobal,
	employeeDeskGlobalPersonalization,
	saveEmployeeDeskGlobalPersonalization,
} from "@/data/personalization"

const __ = inject("$translate")
const employee = inject("$employee")

const MIN_VISIBLE_TABS = 3
const MAX_VISIBLE_TABS = 5
const GROUP_ORDER = ["main", "shift", "expense", "other", "account"]
const GROUP_TITLES = {
	main: __("اصلی"),
	shift: __("شیفت"),
	expense: __("هزینه"),
	other: __("سایر"),
	account: __("حساب کاربری"),
}

const allNavbarItems = [
	{ key: "home", group: "main", icon: HomeIcon, defaultTitle: __("خانه") },
	{ key: "requests", group: "main", featherIcon: "inbox", defaultTitle: __("درخواست‌ها") },
	{ key: "attendance", group: "shift", icon: AttendanceIcon, defaultTitle: __("تقویم حضور و غیاب") },
	{ key: "missions", group: "shift", icon: MissionIcon, defaultTitle: __("ماموریت‌ها") },
	{ key: "weekly_shift", group: "shift", icon: ShiftIcon, defaultTitle: __("شیفت هفته") },
	{ key: "leaves", group: "shift", icon: LeaveIcon, defaultTitle: __("مرخصی") },
	{ key: "shift_allocator_scheduler", group: "shift", icon: ShiftIcon, defaultTitle: __("تقویم شیفت هفتگی") },
	{ key: "imprest", group: "expense", icon: ImprestIcon, defaultTitle: __("تنخواه") },
	{ key: "expenses", group: "expense", icon: ExpenseIcon, defaultTitle: __("مطالبه هزینه") },
	{ key: "advances", group: "expense", icon: EmployeeAdvanceIcon, defaultTitle: __("درخواست مساعده") },
	{ key: "events", group: "other", icon: EventIcon, defaultTitle: __("رویدادها") },
	{ key: "salary", group: "other", icon: SalaryIcon, defaultTitle: __("حقوق") },
	{ key: "appraisals", group: "other", icon: AppraisalIcon, defaultTitle: __("ارزیابی") },
	{ key: "meals", group: "other", icon: MealIcon, defaultTitle: __("غذا") },
	{ key: "complaints", group: "other", icon: ComplaintIcon, defaultTitle: __("شکایات") },
	{ key: "newsletters", group: "other", icon: NewsletterIcon, defaultTitle: __("خبرنامه") },
	{ key: "profile", group: "account", featherIcon: "user", defaultTitle: __("پروفایل") },
	{ key: "notifications", group: "account", featherIcon: "bell", defaultTitle: __("اعلان‌ها") },
	{ key: "settings", group: "account", featherIcon: "settings", defaultTitle: __("تنظیمات") },
]
const allNavbarKeys = allNavbarItems.map((item) => item.key)

function createDefaultDraft() {
	return {
		home_hidden_sections: [],
		home_hidden_kpis: [],
		home_section_order_keys: [],
		hidden_sidebar_routes: [],
		hidden_tab_keys: [],
		sidebar_order_routes: [],
		tab_order_keys: [],
		kpi_order_keys: [],
		sidebar_labels: {},
		tab_labels: {},
		kpi_labels: {},
	}
}

function clonePreferences(value) {
	const source = value || {}
	return {
		home_hidden_sections: [...(source.home_hidden_sections || [])],
		home_hidden_kpis: [...(source.home_hidden_kpis || [])],
		home_section_order_keys: [...(source.home_section_order_keys || [])],
		hidden_sidebar_routes: [...(source.hidden_sidebar_routes || [])],
		hidden_tab_keys: [...(source.hidden_tab_keys || [])],
		sidebar_order_routes: [...(source.sidebar_order_routes || [])],
		tab_order_keys: [...(source.tab_order_keys || [])],
		kpi_order_keys: [...(source.kpi_order_keys || [])],
		sidebar_labels: { ...(source.sidebar_labels || {}) },
		tab_labels: { ...(source.tab_labels || {}) },
		kpi_labels: { ...(source.kpi_labels || {}) },
	}
}

function navbarSnapshot(preferences) {
	return JSON.stringify({
		hidden_tab_keys: [...(preferences?.hidden_tab_keys || [])].sort(),
		tab_order_keys: preferences?.tab_order_keys || [],
		tab_labels: preferences?.tab_labels || {},
	})
}

function sidebarSnapshot(preferences) {
	return JSON.stringify({
		hidden_sidebar_routes: [...(preferences?.hidden_sidebar_routes || [])].sort(),
		sidebar_order_routes: preferences?.sidebar_order_routes || [],
		sidebar_labels: preferences?.sidebar_labels || {},
	})
}

const navbarLoading = ref(true)
const navbarSaving = ref(false)
const navbarDraft = ref(createDefaultDraft())
const navbarLastSnapshot = ref("")
const showNavbarAddMenu = ref(false)

const sidebarLoading = ref(true)
const sidebarSaving = ref(false)
const sidebarDraft = ref(createDefaultDraft())
const sidebarLastSnapshot = ref("")
const showSidebarAddMenu = ref(false)

const canSeeAllocatorShiftTools = computed(() =>
	Boolean(employee.data?.is_shift_allocator || employee.data?.is_shift_allocator_by_role)
)
const canSeeWeeklyShiftPlanner = computed(() => {
	return Boolean(
		employee.data?.variable_shift
			|| employee.data?.has_rotational_shift
			|| employee.data?.needs_shift_registration
	)
})

const navbarHiddenSet = computed(() => new Set(navbarDraft.value.hidden_tab_keys || []))
const navbarOrderMap = computed(
	() => new Map((navbarDraft.value.tab_order_keys || []).map((key, index) => [key, index]))
)

const navbarOrderedItems = computed(() => {
	const labels = navbarDraft.value.tab_labels || {}
	return [...allNavbarItems]
		.sort((left, right) => {
			const leftOrder = navbarOrderMap.value.has(left.key)
				? navbarOrderMap.value.get(left.key)
				: Number.MAX_SAFE_INTEGER
			const rightOrder = navbarOrderMap.value.has(right.key)
				? navbarOrderMap.value.get(right.key)
				: Number.MAX_SAFE_INTEGER
			if (leftOrder !== rightOrder) return leftOrder - rightOrder
			return 0
		})
		.map((item) => ({
			...item,
			title: labels[item.key] || item.defaultTitle,
			hidden: navbarHiddenSet.value.has(item.key),
		}))
})

const navbarVisibleItems = computed(() => navbarOrderedItems.value.filter((item) => !item.hidden))
const navbarPreviewItems = computed(() => navbarVisibleItems.value.slice(0, MAX_VISIBLE_TABS))
const navbarVisibleCount = computed(() => navbarVisibleItems.value.length)
const navbarAddableGroups = computed(() => {
	const groups = []
	for (const groupKey of GROUP_ORDER) {
		const items = navbarOrderedItems.value.filter((item) => item.group === groupKey && item.hidden)
		if (!items.length) continue
		groups.push({ key: groupKey, title: GROUP_TITLES[groupKey], items })
	}
	return groups
})
const canOpenNavbarAddMenu = computed(
	() => navbarVisibleCount.value < MAX_VISIBLE_TABS && navbarAddableGroups.value.length > 0
)

const navbarHasUnsavedChanges = computed(
	() => navbarSnapshot(navbarDraft.value) !== navbarLastSnapshot.value
)

const visibilityMap = computed(() => employeeDeskVisibility.data || {})

const activeSidebarGlobalPreferences = computed(
	() => employeeDeskGlobalPersonalization.data?.preferences || createDefaultDraft()
)

const sidebarCatalogGroups = computed(() => {
	return buildNavbarGroups(__, {
		unreadNewsletterCount: 0,
		hasImprestAccess: true,
		canSeeAllocatorShiftTools: true,
		canSeeWeeklyShiftPlanner: true,
		visibility: {},
		hiddenRoutes: [],
		routeOrder: activeSidebarGlobalPreferences.value.sidebar_order_routes || [],
		customLabels: activeSidebarGlobalPreferences.value.sidebar_labels || {},
	})
})

const sidebarVisibleGroups = computed(() => {
	return buildNavbarGroups(__, {
		unreadNewsletterCount: layoutUnreadNewsletterCount.value,
		hasImprestAccess: layoutHasImprestAccess.value,
		canSeeAllocatorShiftTools: canSeeAllocatorShiftTools.value,
		canSeeWeeklyShiftPlanner: canSeeWeeklyShiftPlanner.value,
		visibility: visibilityMap.value,
		hiddenRoutes: sidebarDraft.value.hidden_sidebar_routes || [],
		routeOrder: sidebarDraft.value.sidebar_order_routes || [],
		customLabels: sidebarDraft.value.sidebar_labels || {},
	})
})

const sidebarHiddenSet = computed(() => new Set(sidebarDraft.value.hidden_sidebar_routes || []))
const sidebarAllRoutes = computed(() =>
	sidebarCatalogGroups.value.flatMap((group) => (group.items || []).map((item) => item.route))
)
const sidebarAddableGroups = computed(() => {
	const groups = []
	for (const group of sidebarCatalogGroups.value) {
		const items = (group.items || []).filter((item) => sidebarHiddenSet.value.has(item.route))
		if (!items.length) continue
		groups.push({ title: group.title, items })
	}
	return groups
})
const sidebarHasUnsavedChanges = computed(
	() => sidebarSnapshot(sidebarDraft.value) !== sidebarLastSnapshot.value
)

function ensureNavbarOrderHasAllKeys() {
	const merged = [...new Set([...(navbarDraft.value.tab_order_keys || []), ...allNavbarKeys])]
	navbarDraft.value = {
		...navbarDraft.value,
		tab_order_keys: merged,
	}
}

function ensureSidebarOrderHasAllRoutes() {
	const merged = [...new Set([...(sidebarDraft.value.sidebar_order_routes || []), ...sidebarAllRoutes.value])]
	sidebarDraft.value = {
		...sidebarDraft.value,
		sidebar_order_routes: merged,
	}
}

function resetNavbarDraft() {
	const source = employeeDeskGlobalPersonalization.data?.preferences || createDefaultDraft()
	navbarDraft.value = clonePreferences(source)
	ensureNavbarOrderHasAllKeys()
	navbarLastSnapshot.value = navbarSnapshot(navbarDraft.value)
	showNavbarAddMenu.value = false
}

function resetSidebarDraft() {
	const source = employeeDeskGlobalPersonalization.data?.preferences || createDefaultDraft()
	sidebarDraft.value = clonePreferences(source)
	ensureSidebarOrderHasAllRoutes()
	sidebarLastSnapshot.value = sidebarSnapshot(sidebarDraft.value)
	showSidebarAddMenu.value = false
}

function buildNavbarSavePayload() {
	const source = clonePreferences(employeeDeskGlobalPersonalization.data?.preferences || createDefaultDraft())
	source.hidden_tab_keys = [...(navbarDraft.value.hidden_tab_keys || [])]
	source.tab_order_keys = [...(navbarDraft.value.tab_order_keys || [])]
	source.tab_labels = { ...(navbarDraft.value.tab_labels || {}) }
	return source
}

function buildNavbarResetPayload() {
	const source = clonePreferences(employeeDeskGlobalPersonalization.data?.preferences || createDefaultDraft())
	source.hidden_tab_keys = []
	source.tab_order_keys = [...allNavbarKeys]
	source.tab_labels = {}
	return source
}

function buildSidebarSavePayload() {
	const source = clonePreferences(employeeDeskGlobalPersonalization.data?.preferences || createDefaultDraft())
	source.hidden_sidebar_routes = [...(sidebarDraft.value.hidden_sidebar_routes || [])]
	source.sidebar_order_routes = [...(sidebarDraft.value.sidebar_order_routes || [])]
	source.sidebar_labels = { ...(sidebarDraft.value.sidebar_labels || {}) }
	return source
}

function buildSidebarResetPayload() {
	const source = clonePreferences(employeeDeskGlobalPersonalization.data?.preferences || createDefaultDraft())
	source.hidden_sidebar_routes = []
	source.sidebar_order_routes = [...sidebarAllRoutes.value]
	source.sidebar_labels = {}
	return source
}

function notifyGlobalNavigationUpdate() {
	if (typeof window === "undefined") return
	window.dispatchEvent(new CustomEvent("hrms:global-navigation-updated"))
}

async function loadNavbarPreferences() {
	navbarLoading.value = true
	try {
		if (!employeeDeskGlobalPersonalization.data) {
			await employeeDeskGlobalPersonalization.reload()
		}
		resetNavbarDraft()
	} finally {
		navbarLoading.value = false
	}
}

async function loadSidebarPreferences() {
	sidebarLoading.value = true
	try {
		if (!employeeDeskGlobalPersonalization.data) {
			await employeeDeskGlobalPersonalization.reload()
		}
		resetSidebarDraft()
	} finally {
		sidebarLoading.value = false
	}
}

async function handleNavbarReset() {
	if (!canCustomizeEmployeeDeskGlobal.value || navbarLoading.value || navbarSaving.value) return
	navbarSaving.value = true
	try {
		await saveEmployeeDeskGlobalPersonalization(buildNavbarResetPayload())
		await employeeDeskGlobalPersonalization.reload()
		resetNavbarDraft()
		notifyGlobalNavigationUpdate()
		toaste("success", __("Global navbar reset for everyone"))
	} catch (error) {
		toaste("error", __(error?.message || "Failed to reset navbar settings"))
	} finally {
		navbarSaving.value = false
	}
}

async function handleSidebarReset() {
	if (!canCustomizeEmployeeDeskGlobal.value || sidebarLoading.value || sidebarSaving.value) return
	sidebarSaving.value = true
	try {
		ensureSidebarOrderHasAllRoutes()
		await saveEmployeeDeskGlobalPersonalization(buildSidebarResetPayload())
		await employeeDeskGlobalPersonalization.reload()
		resetSidebarDraft()
		notifyGlobalNavigationUpdate()
		toaste("success", __("Global sidebar reset for everyone"))
	} catch (error) {
		toaste("error", __(error?.message || "Failed to reset sidebar settings"))
	} finally {
		sidebarSaving.value = false
	}
}

function addNavbarItem(key) {
	if (navbarVisibleCount.value >= MAX_VISIBLE_TABS) {
		window.alert(__("حداکثر ۵ آیتم در نوار پایین مجاز است."))
		return
	}
	const hidden = new Set(navbarDraft.value.hidden_tab_keys || [])
	hidden.delete(key)
	navbarDraft.value = {
		...navbarDraft.value,
		hidden_tab_keys: [...hidden],
	}
	showNavbarAddMenu.value = false
}

function removeNavbarItem(key) {
	if (navbarVisibleCount.value <= MIN_VISIBLE_TABS) {
		window.alert(__("حداقل ۳ آیتم باید در نوار پایین باقی بماند."))
		return
	}
	const hidden = new Set(navbarDraft.value.hidden_tab_keys || [])
	hidden.add(key)
	navbarDraft.value = {
		...navbarDraft.value,
		hidden_tab_keys: [...hidden],
	}
}

function renameNavbarItem(item) {
	const currentValue = navbarDraft.value.tab_labels?.[item.key] || item.defaultTitle || ""
	const nextValue = window.prompt(__("عنوان آیتم نوار پایین"), currentValue)
	if (nextValue === null) return
	const labels = { ...(navbarDraft.value.tab_labels || {}) }
	const normalized = String(nextValue || "").trim()
	if (!normalized) delete labels[item.key]
	else labels[item.key] = normalized
	navbarDraft.value = {
		...navbarDraft.value,
		tab_labels: labels,
	}
}

function moveNavbarItem(key, direction) {
	const merged = [...new Set([...(navbarDraft.value.tab_order_keys || []), ...allNavbarKeys])]
	const currentIndex = merged.indexOf(key)
	if (currentIndex < 0) return
	const nextIndex = currentIndex + direction
	if (nextIndex < 0 || nextIndex >= merged.length) return
	const [moved] = merged.splice(currentIndex, 1)
	merged.splice(nextIndex, 0, moved)
	navbarDraft.value = {
		...navbarDraft.value,
		tab_order_keys: merged,
	}
}

function showSidebarRoute(route) {
	const hidden = new Set(sidebarDraft.value.hidden_sidebar_routes || [])
	hidden.delete(route)
	sidebarDraft.value = {
		...sidebarDraft.value,
		hidden_sidebar_routes: [...hidden],
	}
	showSidebarAddMenu.value = false
}

function hideSidebarRoute(route) {
	const hidden = new Set(sidebarDraft.value.hidden_sidebar_routes || [])
	hidden.add(route)
	sidebarDraft.value = {
		...sidebarDraft.value,
		hidden_sidebar_routes: [...hidden],
	}
}

function renameSidebarRoute(route, fallbackLabel = "") {
	const currentValue = sidebarDraft.value.sidebar_labels?.[route] || fallbackLabel || ""
	const nextValue = window.prompt(__("عنوان آیتم منو"), currentValue)
	if (nextValue === null) return
	const labels = { ...(sidebarDraft.value.sidebar_labels || {}) }
	const normalized = String(nextValue || "").trim()
	if (!normalized) delete labels[route]
	else labels[route] = normalized
	sidebarDraft.value = {
		...sidebarDraft.value,
		sidebar_labels: labels,
	}
}

function moveSidebarRoute(route, direction) {
	const merged = [...new Set([...(sidebarDraft.value.sidebar_order_routes || []), ...sidebarAllRoutes.value])]
	const currentIndex = merged.indexOf(route)
	if (currentIndex < 0) return
	const nextIndex = currentIndex + direction
	if (nextIndex < 0 || nextIndex >= merged.length) return
	const [moved] = merged.splice(currentIndex, 1)
	merged.splice(nextIndex, 0, moved)
	sidebarDraft.value = {
		...sidebarDraft.value,
		sidebar_order_routes: merged,
	}
}

async function saveNavbarDraft() {
	if (!canCustomizeEmployeeDeskGlobal.value || navbarSaving.value) return
	navbarSaving.value = true
	try {
		ensureNavbarOrderHasAllKeys()
		await saveEmployeeDeskGlobalPersonalization(buildNavbarSavePayload())
		await employeeDeskGlobalPersonalization.reload()
		navbarLastSnapshot.value = navbarSnapshot(navbarDraft.value)
		notifyGlobalNavigationUpdate()
		toaste("success", __("Global navbar settings updated"))
	} catch (error) {
		toaste("error", __(error?.message || "Failed to save navbar settings"))
	} finally {
		navbarSaving.value = false
	}
}

async function saveSidebarDraft() {
	if (!canCustomizeEmployeeDeskGlobal.value || sidebarSaving.value) return
	sidebarSaving.value = true
	try {
		ensureSidebarOrderHasAllRoutes()
		await saveEmployeeDeskGlobalPersonalization(buildSidebarSavePayload())
		await employeeDeskGlobalPersonalization.reload()
		sidebarLastSnapshot.value = sidebarSnapshot(sidebarDraft.value)
		notifyGlobalNavigationUpdate()
		toaste("success", __("Global sidebar settings updated"))
	} catch (error) {
		toaste("error", __(error?.message || "Failed to save sidebar settings"))
	} finally {
		sidebarSaving.value = false
	}
}

function toaste(type, text) {
	toast({
		title: type === "success" ? __("Success") : __("Error"),
		text,
		icon: type === "success" ? "check-circle" : "alert-circle",
		position: "bottom-center",
		iconClasses: type === "success" ? "text-green-500" : "text-red-500",
	})
}

onMounted(() => {
	void loadNavbarPreferences()
	void loadSidebarPreferences()
})

watch(
	() => employeeDeskGlobalPersonalization.data?.preferences,
	() => {
		if (navbarLoading.value || navbarSaving.value) return
		resetNavbarDraft()
	},
	{ deep: true }
)

watch(
	() => employeeDeskGlobalPersonalization.data?.preferences,
	() => {
		if (sidebarLoading.value || sidebarSaving.value) return
		resetSidebarDraft()
	},
	{ deep: true }
)
</script>
