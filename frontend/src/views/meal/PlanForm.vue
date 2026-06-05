<template>
	<BaseLayout :pageTitle="__('Weekly Meal Plan')">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-4">
				<div v-if="!canManage" class="bg-white rounded p-4 text-sm text-gray-600">
					{{ __('You are not allowed to manage meal plans.') }}
				</div>

				<template v-else>
					<div class="bg-white rounded p-4 grid grid-cols-1 gap-3">
						<div>
							<label class="block text-xs text-gray-600 mb-1">{{ __('Company') }}</label>
							<input
								:value="form.company"
								type="text"
								readonly
								class="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm w-full"
							/>
						</div>

						<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
							<div>
								<label class="block text-xs text-gray-600 mb-1">{{ __('Week Start Date') }}</label>
								<JalaliDatePicker
									v-model="form.week_start_date"
									:disabled="Boolean(props.id)"
									@change="handleWeekChange"
								/>
							</div>
							<div>
								<label class="block text-xs text-gray-600 mb-1">{{ __('Daily Cutoff Time') }}</label>
								<input
									v-model="form.cutoff_time"
									type="time"
									class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
								/>
							</div>
						</div>

						<div class="grid grid-cols-1 sm:grid-cols-3 gap-2 items-end">
							<div class="sm:col-span-2">
								<label class="block text-xs text-gray-600 mb-1">{{ __('Copy From Previous Week') }}</label>
								<select
									v-model="selectedPreviousPlan"
									class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
								>
									<option value="">{{ __('Select Previous Week Plan') }}</option>
									<option v-for="plan in previousPlans" :key="plan.name" :value="plan.name">
										{{ formatJalaliDateShort(plan.week_start_date) }} - {{ plan.name }}
									</option>
								</select>
							</div>
							<Button
								variant="outline"
								:loading="copyResource.loading"
								:disabled="!selectedPreviousPlan"
								@click="copyFromPreviousWeek"
							>
								{{ __('Copy Week Plan') }}
							</Button>
						</div>

						<div>
							<label class="block text-xs text-gray-600 mb-1">{{ __('Notes') }}</label>
							<textarea
								v-model="form.notes"
								rows="2"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
							/>
						</div>
					</div>

					<div class="bg-white rounded p-4 grid grid-cols-1 sm:grid-cols-3 gap-2 items-end">
						<div class="sm:col-span-2">
							<label class="block text-xs text-gray-600 mb-1">{{ __('Add Food To Catalog') }}</label>
							<select
								v-model="selectedCatalogItem"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
							>
								<option value="">{{ __('Select Food Item') }}</option>
								<option v-for="item in itemOptions" :key="item.name" :value="item.name">
									{{ item.item_name || item.name }}
								</option>
							</select>
						</div>
						<Button
							variant="solid"
							:loading="catalogUpsertResource.loading"
							:disabled="!selectedCatalogItem"
							@click="addCatalogItem"
						>
							{{ __('Add Food') }}
						</Button>
						<div class="sm:col-span-3 text-xs text-gray-600" v-if="!mealCatalog.length">
							{{ __('No active food catalog items found. Add foods from Item list.') }}
						</div>
						<div class="sm:col-span-3 flex flex-wrap gap-2" v-else>
							<span
								v-for="row in mealCatalog"
								:key="row.name"
								class="px-2 py-1 rounded bg-gray-100 text-xs text-gray-700"
							>
								{{ row.item_name || row.item }}
							</span>
						</div>
					</div>

					<div class="bg-white rounded border border-gray-200 divide-y">
						<div
							v-for="(item, index) in form.meal_items"
							:key="`${item.meal_date}-${index}`"
							class="p-3 grid grid-cols-1 gap-2"
						>
							<div class="flex items-center justify-between gap-2">
								<div class="text-sm font-medium text-gray-900">
									{{ item.meal_day_label }} - {{ formatJalaliDateShort(item.meal_date) }}
								</div>
								<label class="inline-flex items-center gap-2 text-xs text-gray-700">
									<input v-model="item.is_available" type="checkbox" />
									{{ __('Available') }}
								</label>
							</div>
							<select
								v-model="item.meal_item"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
								:disabled="!mealCatalog.length"
								@change="onMealItemChange(item)"
							>
								<option value="">{{ __('Select Food Item') }}</option>
								<option
									v-for="food in mealCatalog"
									:key="food.name"
									:value="food.item"
								>
									{{ food.item_name || food.item }}
								</option>
							</select>
							<div class="text-xs text-gray-600">
								{{ __('Selected Food') }}: {{ item.menu_title || '-' }}
							</div>
							<input
								v-model="item.menu_description"
								type="text"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
								:placeholder="__('Menu Description')"
							/>
						</div>
					</div>

					<ErrorMessage :message="errorMessage" />

					<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
						<Button
							variant="outline"
							class="py-5 text-base w-full"
							:loading="saveResource.loading"
							@click="savePlan(false)"
						>
							{{ __('Save Draft Meal Plan') }}
						</Button>
						<Button
							variant="solid"
							class="py-5 text-base w-full"
							:loading="publishResource.loading"
							@click="savePlan(true)"
						>
							{{ __('Publish Meal Plan') }}
						</Button>
					</div>
				</template>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref } from "vue"
import { createResource, ErrorMessage, toast } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import JalaliDatePicker from "@/components/JalaliDatePicker.vue"
import dayjs from "@/utils/dayjs"
import { formatJalaliDateShort } from "@/utils/jalali"

const __ = inject("$translate")

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

const form = ref({
	name: "",
	company: "",
	week_start_date: "",
	cutoff_time: "10:00",
	notes: "",
	meal_items: [],
})

const errorMessage = ref("")
const selectedPreviousPlan = ref("")
const selectedCatalogItem = ref("")
const mealCatalog = ref([])
const previousPlans = ref([])
const itemOptions = ref([])

const canManage = computed(() => Boolean(contextResource.data?.is_meal_coordinator))

const contextResource = createResource({
	url: "hrms.api.meal.get_meal_plan_context",
	auto: true,
	onSuccess(data) {
		errorMessage.value = ""
		setContextData(data)
		if (props.id) {
			loadPlanByName(props.id)
			return
		}

		if (data?.plan && data?.is_meal_coordinator) {
			applyPlan(data.plan)
			return
		}

		initializeNewForm(data)
	},
	onError(error) {
		errorMessage.value = extractErrorMessage(error, __("Failed to load meal plan context."))
	},
})

const saveResource = createResource({
	url: "hrms.api.meal.upsert_meal_weekly_plan",
	auto: false,
})

const publishResource = createResource({
	url: "hrms.api.meal.publish_meal_weekly_plan",
	auto: false,
})

const copyResource = createResource({
	url: "hrms.api.meal.copy_meal_plan_from_previous_week",
	auto: false,
})

const loadPlanResource = createResource({
	url: "frappe.client.get",
	auto: false,
})

const catalogResource = createResource({
	url: "hrms.api.meal.get_meal_catalog",
	auto: false,
	onSuccess(data) {
		mealCatalog.value = data || []
	},
})

const itemOptionResource = createResource({
	url: "hrms.api.meal.get_employee_meal_item_options",
	auto: false,
	onSuccess(data) {
		itemOptions.value = data || []
	},
})

const previousPlanResource = createResource({
	url: "frappe.client.get_list",
	auto: false,
	onSuccess(data) {
		previousPlans.value = data || []
	},
})

const catalogUpsertResource = createResource({
	url: "hrms.api.meal.upsert_meal_catalog_item",
	auto: false,
})

function setContextData(data) {
	mealCatalog.value = data?.meal_catalog || []
	previousPlans.value = data?.previous_week_plans || []
	loadItemOptions()
}

function initializeNewForm(context) {
	const weekStart = context?.week_start_date || dayjs().format("YYYY-MM-DD")
	form.value = {
		name: "",
		company: context?.company || context?.employee?.company || "",
		week_start_date: weekStart,
		cutoff_time: normalizeTimeInput(context?.default_cutoff_time || "10:00:00"),
		notes: "",
		meal_items: buildWeekItems(weekStart),
	}
	refreshSupportLists()
}

function applyPlan(planData) {
	const rows = (planData?.meal_items || []).map((row) => ({
		meal_date: row.meal_date,
		meal_day_label: row.meal_day_label || getWeekdayLabel(row.meal_date),
		meal_type: row.meal_type || "Lunch",
		meal_item: row.meal_item || "",
		menu_title: row.menu_title || "",
		is_available: Boolean(Number(row.is_available ?? 1)),
		menu_description: row.menu_description || "",
	}))

	form.value = {
		name: planData.name || "",
		company: planData.company || "",
		week_start_date: planData.week_start_date || dayjs().format("YYYY-MM-DD"),
		cutoff_time: normalizeTimeInput(planData.cutoff_time || "10:00:00"),
		notes: planData.notes || "",
		meal_items: rows.length ? rows : buildWeekItems(planData.week_start_date),
	}
	refreshSupportLists()
}

function loadPlanByName(planName) {
	loadPlanResource.fetch(
		{
			doctype: "Meal Weekly Plan",
			name: planName,
		},
		{
			onSuccess(data) {
				applyPlan(data)
			},
			onError(error) {
				errorMessage.value = extractErrorMessage(error, __("Failed to load meal plan."))
			},
		}
	)
}

function refreshSupportLists() {
	if (!form.value.company) return
	loadMealCatalog()
	loadItemOptions()
	loadPreviousPlans()
}

function loadMealCatalog() {
	catalogResource.fetch({ company: form.value.company })
}

function loadItemOptions() {
	if (!form.value.company) return
	itemOptionResource.fetch({ company: form.value.company })
}

function loadPreviousPlans() {
	if (!(form.value.company && form.value.week_start_date)) return
	previousPlanResource.fetch({
		doctype: "Meal Weekly Plan",
		fields: ["name", "week_start_date", "week_end_date", "published_on"],
		filters: {
			company: form.value.company,
			status: "Published",
			week_start_date: ["<", form.value.week_start_date],
			docstatus: ["!=", 2],
		},
		order_by: "week_start_date desc",
		limit_page_length: 12,
	})
}

function handleWeekChange() {
	const weekStart = form.value.week_start_date
	if (!weekStart) return
	const existingMap = Object.fromEntries(
		(form.value.meal_items || []).map((row) => [row.meal_date, row])
	)
	form.value.meal_items = buildWeekItems(weekStart, existingMap)
	loadPreviousPlans()
}

function buildWeekItems(weekStart, existingMap = {}) {
	const base = dayjs(weekStart)
	return Array.from({ length: 7 }).map((_, index) => {
		const date = base.add(index, "day").format("YYYY-MM-DD")
		const existing = existingMap[date] || {}
		return {
			meal_date: date,
			meal_day_label: getWeekdayLabel(date),
			meal_type: "Lunch",
			meal_item: existing.meal_item || "",
			menu_title: existing.menu_title || "",
			is_available:
				existing.is_available !== undefined ? Boolean(existing.is_available) : true,
			menu_description: existing.menu_description || "",
		}
	})
}

function getWeekdayLabel(date) {
	const map = ["یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه"]
	return map[dayjs(date).day()] || ""
}

function onMealItemChange(row) {
	const option = [...mealCatalog.value, ...itemOptions.value].find((food) => food.item === row.meal_item || food.name === row.meal_item)
	if (option) {
		row.menu_title = option.item_name || option.item || option.name
	} else {
		row.menu_title = row.meal_item || ""
	}
}

function copyFromPreviousWeek() {
	if (!selectedPreviousPlan.value) return
	copyResource.submit(
		{
			source_plan_name: selectedPreviousPlan.value,
			target_week_start_date: form.value.week_start_date,
			company: form.value.company,
		},
		{
			onSuccess(data) {
				applyCopiedWeek(data?.meal_items || [])
				toast({
					title: __("Success"),
					text: __("Previous week copied successfully."),
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			},
			onError(error) {
				errorMessage.value = extractErrorMessage(error, __("Failed to copy previous week."))
			},
		}
	)
}

function applyCopiedWeek(rows) {
	const map = {}
	for (const row of rows) {
		if (!row?.meal_date) continue
		map[row.meal_date] = {
			meal_date: row.meal_date,
			meal_day_label: getWeekdayLabel(row.meal_date),
			meal_type: row.meal_type || "Lunch",
			meal_item: row.meal_item || "",
			menu_title: row.menu_title || "",
			is_available: Boolean(Number(row.is_available ?? 1)),
			menu_description: row.menu_description || "",
		}
	}
	form.value.meal_items = buildWeekItems(form.value.week_start_date, map)
}

function addCatalogItem() {
	if (!selectedCatalogItem.value) return
	catalogUpsertResource.submit(
		{
			item_code: selectedCatalogItem.value,
			company: form.value.company,
			is_active: 1,
		},
		{
			onSuccess() {
				selectedCatalogItem.value = ""
				loadMealCatalog()
				toast({
					title: __("Success"),
					text: __("Food added to catalog."),
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			},
			onError(error) {
				errorMessage.value = extractErrorMessage(error, __("Failed to add food to catalog."))
			},
		}
	)
}

function savePlan(shouldPublish) {
	if (!canManage.value) return
	errorMessage.value = ""

	const payload = {
		name: form.value.name || undefined,
		company: form.value.company,
		week_start_date: form.value.week_start_date,
		cutoff_time: normalizeTimeOutput(form.value.cutoff_time),
		notes: form.value.notes || "",
		meal_items: (form.value.meal_items || []).map((row) => ({
			meal_date: row.meal_date,
			meal_type: "Lunch",
			meal_item: row.meal_item || "",
			menu_title: row.menu_title || "",
			is_available: row.is_available ? 1 : 0,
			menu_description: row.menu_description || "",
		})),
	}

	saveResource.submit(
		{
			payload: JSON.stringify(payload),
		},
		{
			onSuccess(data) {
				applyPlan(data)
				if (!shouldPublish) {
					toast({
						title: __("Success"),
						text: __("Meal plan draft saved."),
						icon: "check-circle",
						position: "bottom-center",
						iconClasses: "text-green-500",
					})
					return
				}
				publishPlan(data?.name)
			},
			onError(error) {
				errorMessage.value = extractErrorMessage(error, __("Failed to save meal plan."))
			},
		}
	)
}

function publishPlan(planName) {
	if (!planName) return
	publishResource.submit(
		{
			plan_name: planName,
		},
		{
			onSuccess(data) {
				applyPlan(data)
				contextResource.reload()
				toast({
					title: __("Success"),
					text: __("Meal plan published successfully."),
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			},
			onError(error) {
				errorMessage.value = extractErrorMessage(error, __("Failed to publish meal plan."))
			},
		}
	)
}

function normalizeTimeInput(value) {
	return String(value || "10:00:00").slice(0, 5)
}

function normalizeTimeOutput(value) {
	const text = String(value || "10:00").trim()
	return text.length === 5 ? `${text}:00` : text
}

function extractErrorMessage(error, fallbackMessage) {
	if (Array.isArray(error?.messages) && error.messages.length) return error.messages[0]
	if (typeof error?.message === "string" && error.message.trim()) return error.message
	return fallbackMessage
}
</script>
