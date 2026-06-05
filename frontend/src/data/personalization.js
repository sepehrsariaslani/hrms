import { computed } from "vue"
import { createResource } from "frappe-ui"

import { employeeResource } from "./employee"

const MIN_VISIBLE_TABS = 3
const MAX_VISIBLE_TABS = 5
const ALL_TAB_KEYS = [
	"home",
	"requests",
	"attendance",
	"missions",
	"weekly_shift",
	"leaves",
	"shift_allocator_scheduler",
	"team_weekly_shifts",
	"imprest",
	"expenses",
	"advances",
	"events",
	"salary",
	"appraisals",
	"meals",
	"complaints",
	"newsletters",
	"profile",
	"notifications",
	"settings",
]

const DEFAULT_HIDDEN_TAB_KEYS = [
	"requests",
	"missions",
	"weekly_shift",
	"shift_allocator_scheduler",
	"team_weekly_shifts",
	"imprest",
	"advances",
	"events",
	"appraisals",
	"meals",
	"complaints",
	"newsletters",
	"profile",
	"notifications",
	"settings",
]

const PERSONALIZATION_DEFAULTS = {
	home_hidden_sections: [],
	home_hidden_kpis: [],
	home_section_order_keys: [],
	hidden_sidebar_routes: [],
	hidden_tab_keys: [...DEFAULT_HIDDEN_TAB_KEYS],
	sidebar_order_routes: [],
	tab_order_keys: [],
	kpi_order_keys: [],
	sidebar_labels: {},
	tab_labels: {},
	kpi_labels: {},
}

function normalizeList(value) {
	if (!Array.isArray(value)) return []
	return value
		.map((item) => String(item || "").trim())
		.filter((item, index, list) => item && list.indexOf(item) === index)
}

function normalizeChoiceList(value, validValues = []) {
	const validSet = new Set(validValues)
	return normalizeList(value).filter((item) => validSet.has(item))
}

function normalizeTabVisibility(hiddenTabKeys = [], tabOrderKeys = []) {
	const orderedKeys = normalizeChoiceList([...(tabOrderKeys || []), ...ALL_TAB_KEYS], ALL_TAB_KEYS)
	const hiddenSet = new Set(normalizeChoiceList(hiddenTabKeys, ALL_TAB_KEYS))
	const visibleKeys = orderedKeys.filter((key) => !hiddenSet.has(key))

	if (visibleKeys.length > MAX_VISIBLE_TABS) {
		for (const key of visibleKeys.slice(MAX_VISIBLE_TABS)) hiddenSet.add(key)
	}

	if (visibleKeys.length < MIN_VISIBLE_TABS) {
		for (const key of orderedKeys) {
			if (!hiddenSet.has(key)) continue
			hiddenSet.delete(key)
			visibleKeys.push(key)
			if (visibleKeys.length >= MIN_VISIBLE_TABS) break
		}
	}

	return normalizeChoiceList(orderedKeys.filter((key) => hiddenSet.has(key)), ALL_TAB_KEYS)
}

function normalizePreferences(value) {
	const source = value || {}
	const tabOrderKeys = normalizeChoiceList(source.tab_order_keys, ALL_TAB_KEYS)
	const rawHiddenTabKeys = source.hidden_tab_keys
	const hiddenTabKeys = normalizeChoiceList(rawHiddenTabKeys ?? DEFAULT_HIDDEN_TAB_KEYS, ALL_TAB_KEYS)
	if (rawHiddenTabKeys != null) {
		const hiddenSet = new Set(hiddenTabKeys)
		const orderSet = new Set(tabOrderKeys)
		for (const key of DEFAULT_HIDDEN_TAB_KEYS) {
			if (hiddenSet.has(key) || orderSet.has(key)) continue
			hiddenTabKeys.push(key)
			hiddenSet.add(key)
		}
	}
	const normalizedHiddenTabKeys = normalizeTabVisibility(hiddenTabKeys, tabOrderKeys)

	return {
		home_hidden_sections: normalizeList(source.home_hidden_sections),
		home_hidden_kpis: normalizeList(source.home_hidden_kpis),
		home_section_order_keys: normalizeList(source.home_section_order_keys),
		hidden_sidebar_routes: normalizeList(source.hidden_sidebar_routes),
		hidden_tab_keys: normalizedHiddenTabKeys,
		sidebar_order_routes: normalizeList(source.sidebar_order_routes),
		tab_order_keys: tabOrderKeys,
		kpi_order_keys: normalizeList(source.kpi_order_keys),
		sidebar_labels: { ...(source.sidebar_labels || {}) },
		tab_labels: { ...(source.tab_labels || {}) },
		kpi_labels: { ...(source.kpi_labels || {}) },
	}
}

function clonePreferences(value) {
	return {
		home_hidden_sections: [...(value?.home_hidden_sections || [])],
		home_hidden_kpis: [...(value?.home_hidden_kpis || [])],
		home_section_order_keys: [...(value?.home_section_order_keys || [])],
		hidden_sidebar_routes: [...(value?.hidden_sidebar_routes || [])],
		hidden_tab_keys: [...(value?.hidden_tab_keys || [])],
		sidebar_order_routes: [...(value?.sidebar_order_routes || [])],
		tab_order_keys: [...(value?.tab_order_keys || [])],
		kpi_order_keys: [...(value?.kpi_order_keys || [])],
		sidebar_labels: { ...(value?.sidebar_labels || {}) },
		tab_labels: { ...(value?.tab_labels || {}) },
		kpi_labels: { ...(value?.kpi_labels || {}) },
	}
}

function mergeOrderedList(base = [], override = []) {
	return normalizeList([...(override || []), ...(base || [])])
}

function mergePreferences(base, override) {
	return {
		home_hidden_sections: normalizeList([
			...(base?.home_hidden_sections || []),
			...(override?.home_hidden_sections || []),
		]),
		home_hidden_kpis: normalizeList([
			...(base?.home_hidden_kpis || []),
			...(override?.home_hidden_kpis || []),
		]),
		home_section_order_keys: mergeOrderedList(
			base?.home_section_order_keys,
			override?.home_section_order_keys
		),
		hidden_sidebar_routes: normalizeList([
			...(base?.hidden_sidebar_routes || []),
			...(override?.hidden_sidebar_routes || []),
		]),
		hidden_tab_keys: normalizeList([...(base?.hidden_tab_keys || []), ...(override?.hidden_tab_keys || [])]),
		sidebar_order_routes: mergeOrderedList(base?.sidebar_order_routes, override?.sidebar_order_routes),
		tab_order_keys: mergeOrderedList(base?.tab_order_keys, override?.tab_order_keys),
		kpi_order_keys: mergeOrderedList(base?.kpi_order_keys, override?.kpi_order_keys),
		sidebar_labels: {
			...(base?.sidebar_labels || {}),
			...(override?.sidebar_labels || {}),
		},
		tab_labels: {
			...(base?.tab_labels || {}),
			...(override?.tab_labels || {}),
		},
		kpi_labels: {
			...(base?.kpi_labels || {}),
			...(override?.kpi_labels || {}),
		},
	}
}

export const employeeDeskPersonalization = createResource({
	url: "hrms.api.get_employee_desk_personalization",
	auto: false,
	cache: "hrms:employee_desk_personalization",
	transform(data) {
		return {
			can_customize: Boolean(data?.can_customize),
			preferences: normalizePreferences(data?.preferences || PERSONALIZATION_DEFAULTS),
		}
	},
})

export const employeeDeskGlobalPersonalization = createResource({
	url: "hrms.api.get_employee_desk_global_personalization",
	auto: false,
	cache: "hrms:employee_desk_global_personalization",
	transform(data) {
		return {
			can_customize_global: Boolean(data?.can_customize_global),
			preferences: normalizePreferences(data?.preferences || PERSONALIZATION_DEFAULTS),
		}
	},
})

export const canCustomizeEmployeeDeskGlobal = computed(() =>
	Boolean(employeeDeskGlobalPersonalization.data?.can_customize_global)
)

export const canCustomizeEmployeeDesk = computed(
	() => Boolean(employeeDeskPersonalization.data?.can_customize) || canCustomizeEmployeeDeskGlobal.value
)

const personalPreferences = computed(
	() => employeeDeskPersonalization.data?.preferences || clonePreferences(PERSONALIZATION_DEFAULTS)
)

const globalPreferences = computed(
	() => employeeDeskGlobalPersonalization.data?.preferences || clonePreferences(PERSONALIZATION_DEFAULTS)
)

export const employeeDeskPreferences = computed(() => {
	return mergePreferences(globalPreferences.value, personalPreferences.value)
})

const saveEmployeeDeskPersonalizationResource = createResource({
	url: "hrms.api.save_employee_desk_personalization",
	auto: false,
})

const saveEmployeeDeskGlobalPersonalizationResource = createResource({
	url: "hrms.api.save_employee_desk_global_personalization",
	auto: false,
})

export async function saveEmployeeDeskPersonalization(preferences) {
	const normalized = normalizePreferences(preferences)
	await saveEmployeeDeskPersonalizationResource.submit({
		preferences: JSON.stringify(normalized),
	})

	const payload = {
		can_customize: Boolean(employeeDeskPersonalization.data?.can_customize),
		preferences: clonePreferences(normalized),
	}
	employeeDeskPersonalization.data = payload
	return payload
}

export async function saveEmployeeDeskGlobalPersonalization(preferences) {
	const normalized = normalizePreferences(preferences)
	await saveEmployeeDeskGlobalPersonalizationResource.submit({
		preferences: JSON.stringify(normalized),
	})

	const payload = {
		can_customize_global: Boolean(employeeDeskGlobalPersonalization.data?.can_customize_global),
		preferences: clonePreferences(normalized),
	}
	employeeDeskGlobalPersonalization.data = payload
	return payload
}

export function saveActiveEmployeeDeskPersonalization(preferences) {
	if (canCustomizeEmployeeDeskGlobal.value) {
		return saveEmployeeDeskGlobalPersonalization(preferences)
	}
	return saveEmployeeDeskPersonalization(preferences)
}

export function resetEmployeeDeskPersonalizationLocal() {
	employeeDeskPersonalization.data = {
		can_customize: Boolean(employeeDeskPersonalization.data?.can_customize),
		preferences: clonePreferences(PERSONALIZATION_DEFAULTS),
	}
	return employeeDeskPersonalization.data
}

export function refreshEmployeeDeskPersonalization() {
	if (!employeeResource.data?.name) return
	employeeDeskPersonalization.reload()
	employeeDeskGlobalPersonalization.reload()
}
