<template>
	<BaseLayout :pageTitle="__('Meal Program')">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-4">
				<div v-if="isCoordinator" class="grid grid-cols-1 sm:grid-cols-2 gap-2">
					<router-link :to="{ name: 'MealPlanFormView' }" v-slot="{ navigate }">
						<Button @click="navigate" variant="solid" class="py-5 text-base w-full">
							{{ __('Meal Planning') }}
						</Button>
					</router-link>
					<router-link :to="{ name: 'MealCoordinatorBoardView' }" v-slot="{ navigate }">
						<Button @click="navigate" variant="outline" class="py-5 text-base w-full">
							{{ __('Chef Dashboard') }}
						</Button>
					</router-link>
				</div>

				<div class="rounded p-4 text-sm text-gray-700 hr-accent-soft">
					<div class="font-semibold text-gray-900">{{ weekLabel }}</div>
					<div class="mt-1 text-xs text-gray-600">
						{{ __('Daily Cutoff Time') }}: {{ cutoffTimeLabel }}
					</div>
					<div class="mt-1 text-xs text-gray-600">
						{{ __('Reserved Meals') }}: {{ toPersianDigits(reservedCount) }}
					</div>
				</div>

				<div v-if="!plan" class="bg-white rounded p-4 text-sm text-gray-600">
					{{ __('No meal plan has been published for this week.') }}
				</div>

				<div v-else class="bg-white rounded border border-gray-200 overflow-hidden">
					<div class="grid grid-cols-12 bg-gray-50 border-b border-gray-200 text-xs text-gray-600 font-semibold">
						<div class="col-span-3 p-2">{{ __('Day') }}</div>
						<div class="col-span-4 p-2">{{ __('Food') }}</div>
						<div class="col-span-5 p-2">{{ __('Status') }}</div>
					</div>
					<div
						v-for="row in visibleReservationRows"
						:key="row.meal_date"
						class="grid grid-cols-12 border-b border-gray-100 last:border-b-0"
					>
						<div class="col-span-3 p-2 text-xs text-gray-700">
							<div class="font-semibold text-gray-800">{{ row.meal_day_label }}</div>
							<div>{{ formatJalaliDateShort(row.meal_date) }}</div>
						</div>
						<div class="col-span-4 p-2 text-xs text-gray-800">
							<div class="font-medium">{{ row.menu_title }}</div>
							<div v-if="row.menu_description" class="text-gray-500 mt-1">{{ row.menu_description }}</div>
						</div>
						<div class="col-span-5 p-2">
							<select
								v-model="row.reservation_status"
								class="rounded-md border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-800 w-full"
								:disabled="!canEditRow(row)"
							>
								<option value="Not Required">{{ __('Not Required') }}</option>
								<option value="Reserved">{{ __('Reserved') }}</option>
								<option v-if="row.reservation_status === 'Delivered'" value="Delivered">
									{{ __('Delivered') }}
								</option>
							</select>
							<div v-if="row.is_locked" class="text-[10px] text-amber-600 mt-1">
								{{ __('Meal already delivered and cannot be edited.') }}
							</div>
							<div v-else-if="row.after_cutoff" class="text-[10px] text-amber-600 mt-1">
								{{ __('Cutoff passed for this day.') }}
							</div>
						</div>
					</div>
					<div v-if="!visibleReservationRows.length" class="p-4 text-xs text-amber-700">
						{{ __('Reservation deadline has passed for all meals in this week.') }}
					</div>
				</div>

				<ErrorMessage :message="saveErrorMessage" />

				<Button
					v-if="plan"
					variant="solid"
					class="py-5 text-base w-full"
					:loading="saveResource.loading"
					:disabled="!canEditAny"
					@click="saveReservations"
				>
					{{ __('Save Meal Reservations') }}
				</Button>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref } from "vue"
import { createResource, ErrorMessage, toast } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import { formatJalaliDateShort, toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")
const reservationRows = ref([])
const saveErrorMessage = ref("")

const contextResource = createResource({
	url: "hrms.api.meal.get_meal_plan_context",
	auto: true,
	cache: "hrms:meal_context",
	onSuccess(data) {
		reservationRows.value = normalizeReservationRows(data?.reservations || [])
	},
})

const saveResource = createResource({
	url: "hrms.api.meal.save_my_meal_reservations",
	auto: false,
})

const context = computed(() => contextResource.data || {})
const plan = computed(() => context.value.plan || null)
const isCoordinator = computed(() => Boolean(context.value.is_meal_coordinator))

const weekLabel = computed(() => {
	const start = formatJalaliDateShort(context.value.week_start_date)
	const end = formatJalaliDateShort(context.value.week_end_date)
	return start && end ? `${start} - ${end}` : ""
})

const cutoffTimeLabel = computed(() => {
	const cutoff = String(plan.value?.cutoff_time || context.value.default_cutoff_time || "")
	if (!cutoff) return "-"
	return cutoff.slice(0, 5)
})

const visibleReservationRows = computed(() =>
	reservationRows.value.filter((row) => !row.after_cutoff)
)
const reservedCount = computed(() =>
	visibleReservationRows.value.filter(
		(row) => row.reservation_status === "Reserved" || row.reservation_status === "Delivered"
	).length
)

const canEditAny = computed(() => {
	return visibleReservationRows.value.some((row) => canEditRow(row))
})

function normalizeReservationRows(rows) {
	return (rows || []).map((row) => ({
		meal_date: row.meal_date,
		meal_day_label: row.meal_day_label || "",
		meal_type: row.meal_type || "Lunch",
		meal_item: row.meal_item || "",
		menu_title: row.menu_title || "",
		menu_description: row.menu_description || "",
		reservation_status: row.reservation_status || "Not Required",
		reservation_note: row.reservation_note || "",
		is_locked: Boolean(row.is_locked),
		after_cutoff: Boolean(row.after_cutoff),
	}))
}

function canEditRow(row) {
	if (!context.value.can_edit_reservations) return false
	if (row.is_locked) return false
	if (row.after_cutoff) return false
	return true
}

function saveReservations() {
	if (!plan.value?.name) return
	saveErrorMessage.value = ""
	const payload = visibleReservationRows.value.map((row) => ({
		meal_date: row.meal_date,
		reservation_status: row.reservation_status,
		reservation_note: row.reservation_note || "",
	}))

	saveResource.submit(
		{
			plan_name: plan.value.name,
			reservations: JSON.stringify(payload),
		},
		{
			onSuccess(data) {
				reservationRows.value = normalizeReservationRows(data?.reservations || [])
				contextResource.reload()
				toast({
					title: __("Success"),
					text: __("Meal reservations saved successfully."),
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			},
			onError(error) {
				saveErrorMessage.value = extractErrorMessage(error, __("Failed to save meal reservations."))
			},
		}
	)
}

function extractErrorMessage(error, fallbackMessage) {
	if (Array.isArray(error?.messages) && error.messages.length) return error.messages[0]
	if (typeof error?.message === "string" && error.message.trim()) return error.message
	return fallbackMessage
}
</script>
