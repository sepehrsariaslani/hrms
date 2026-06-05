<template>
	<div class="flex flex-col w-full gap-5" v-if="calendarEvents.data">
		<div class="text-lg text-gray-800 font-bold">{{ __(props.title) }}</div>

		<div class="flex flex-col gap-6 bg-white py-6 px-3.5 rounded-lg border-none">
			<div class="flex flex-row justify-between items-center px-4">
				<Button icon="chevron-left" variant="ghost" @click="shiftMonth(-1)" />
				<div class="flex items-center gap-2">
					<button
						type="button"
						class="rounded-lg border border-gray-200 px-2.5 py-1 text-xs font-semibold text-gray-600 hover:bg-gray-50"
						@click="goToToday"
					>
						{{ __("Today") }}
					</button>
					<button
						type="button"
						class="text-base text-gray-800 font-bold text-center min-w-[140px] rounded px-1"
						:class="viewMode === 'month' ? 'hover:bg-gray-100' : 'cursor-default'"
						@click="openYearFromMonth"
					>
						{{ periodLabel }}
					</button>
				</div>
				<Button icon="chevron-right" variant="ghost" @click="shiftMonth(1)" />
			</div>

			<div class="mx-2 grid grid-cols-2 gap-2">
				<button
					v-for="mode in viewModes"
					:key="mode.value"
					type="button"
					class="rounded-lg border px-2 py-1.5 text-xs font-semibold transition"
					:class="
						viewMode === mode.value
							? 'border-emerald-500 bg-emerald-50 text-emerald-700'
							: 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
					"
					@click="setViewMode(mode.value)"
				>
					{{ mode.label }}
				</button>
			</div>

			<div class="mx-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2">
				<div class="text-[11px] font-semibold text-gray-700">
					راهنمای رنگ‌ها
				</div>
				<div class="mt-2 flex flex-wrap gap-2">
					<span
						v-for="item in calendarLegendItems"
						:key="item.key"
						class="inline-flex items-center gap-1 rounded-full border border-gray-200 bg-white px-2 py-0.5 text-[11px] text-gray-700"
					>
						<span class="h-2.5 w-2.5 rounded-full" :class="item.dotClass" />
						{{ item.label }}
					</span>
				</div>
			</div>

			<div v-if="viewMode === 'month'" class="grid grid-cols-7 gap-px rounded-lg border border-gray-200 overflow-hidden bg-gray-200/70">
				<div
					v-for="day in DAYS"
					:key="day"
					class="flex h-9 items-center justify-center bg-gray-50 text-gray-600 text-xs font-semibold"
				>
					{{ day }}
				</div>

				<button
					v-for="day in monthGridDays"
					:key="day.key"
					type="button"
					class="month-grid-cell border-b border-l border-gray-200 p-2 text-right transition-colors"
					:class="getMonthCellClass(day)"
					@click="selectDate(day)"
				>
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-1">
							<span
								v-if="getDayIndicatorCount(day.gregorianDate)"
								class="inline-flex min-w-[1.3rem] items-center justify-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold"
								:class="getDayIndicatorSummaryText(day.gregorianDate).badgeClass"
							>
								{{ toPersianDigits(String(getDayIndicatorCount(day.gregorianDate))) }}
							</span>
							<span v-if="getMealEmoji(day.gregorianDate)" class="text-sm leading-none">
								{{ getMealEmoji(day.gregorianDate) }}
							</span>
						</div>
						<span class="h-7 w-7 flex items-center justify-center rounded-full text-xs font-semibold" :class="getMonthDayClass(day)">
							{{ toPersianDigits(String(day.jalaliDay)) }}
						</span>
					</div>

						<div class="mt-2 space-y-1">
							<div
								v-if="getDayShiftSlotSummary(day.gregorianDate)"
								class="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-semibold"
								:class="getDayShiftSlotSummary(day.gregorianDate).badgeClass"
							>
								{{ getDayShiftSlotSummary(day.gregorianDate).label }}
							</div>
							<div
								v-if="getDayAttendanceLabel(day.gregorianDate)"
								class="inline-flex w-full items-center gap-1 rounded px-1.5 py-1 text-[10px] font-medium"
								:class="getDayAttendanceBadgeClass(day.gregorianDate)"
							>
							<span class="h-1.5 w-1.5 rounded-full" :class="getDayAttendanceDotClass(day.gregorianDate)" />
							<span class="hidden truncate sm:inline">{{ getDayAttendanceLabel(day.gregorianDate) }}</span>
							<span class="truncate sm:hidden">{{ getDayAttendanceCompactLabel(day.gregorianDate) }}</span>
						</div>
						<div
							v-if="getDayMissionLabel(day.gregorianDate)"
							class="hidden w-full items-center gap-1 rounded bg-violet-100 px-1.5 py-1 text-[10px] font-medium text-violet-700 sm:inline-flex"
						>
							<span class="h-1.5 w-1.5 rounded-full bg-violet-500" />
							<span class="truncate">{{ getDayMissionLabel(day.gregorianDate) }}</span>
						</div>
					</div>
				</button>
			</div>

			<div v-else-if="viewMode === 'week'" class="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-7">
				<button
					v-for="day in weekDays"
					:key="day.key"
					type="button"
					class="rounded-xl border p-2.5 text-right transition"
					:class="getWeekCellClass(day)"
					@click="selectDate(day)"
				>
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-1">
							<span class="text-[10px] text-gray-500">{{ day.weekdayShort }}</span>
							<span v-if="getMealEmoji(day.gregorianDate)" class="text-sm leading-none">
								{{ getMealEmoji(day.gregorianDate) }}
							</span>
						</div>
						<span class="h-6 min-w-6 px-1 inline-flex items-center justify-center rounded-full text-xs font-semibold" :class="getWeekDayNumberClass(day)">
							{{ toPersianDigits(String(day.jalaliDay)) }}
						</span>
					</div>
						<div class="mt-2 space-y-1">
							<div
								v-if="getDayShiftSlotSummary(day.gregorianDate)"
								class="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-semibold"
								:class="getDayShiftSlotSummary(day.gregorianDate).badgeClass"
							>
								{{ getDayShiftSlotSummary(day.gregorianDate).label }}
							</div>
						<div
							v-if="getDayAttendanceLabel(day.gregorianDate)"
							class="inline-flex w-full items-center gap-1 rounded px-1.5 py-1 text-[10px] font-medium"
							:class="getDayAttendanceBadgeClass(day.gregorianDate)"
						>
							<span class="h-1.5 w-1.5 rounded-full" :class="getDayAttendanceDotClass(day.gregorianDate)" />
							<span class="truncate">{{ getDayAttendanceLabel(day.gregorianDate) }}</span>
						</div>
						<div
							v-if="getDayMissionLabel(day.gregorianDate)"
							class="inline-flex w-full items-center gap-1 rounded bg-violet-100 px-1.5 py-1 text-[10px] font-medium text-violet-700"
						>
							<span class="h-1.5 w-1.5 rounded-full bg-violet-500" />
							<span class="truncate">{{ getDayMissionLabel(day.gregorianDate) }}</span>
						</div>
						<div
							v-for="badge in getDayRequestBadges(day.gregorianDate)"
							:key="`week-request-${day.gregorianDate}-${badge.key}`"
							class="inline-flex w-full items-center gap-1 rounded px-1.5 py-1 text-[10px] font-medium"
							:class="badge.className"
						>
							<span class="h-1.5 w-1.5 rounded-full" :class="badge.dotClass" />
							<span class="truncate">{{ badge.label }}</span>
						</div>
					</div>
				</button>
			</div>

			<div v-else class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
				<button
					v-for="month in yearMonths"
					:key="`year-${month.month}`"
					type="button"
					class="rounded-lg border border-gray-200 bg-white px-3 py-3 text-right transition hover:bg-gray-50"
					:class="month.month === activeJalaliMonth.month ? 'ring-2 ring-emerald-500 border-emerald-400' : ''"
					@click="openMonthFromYear(month.month)"
				>
					<div class="text-sm font-semibold text-gray-800">{{ month.label }}</div>
					<div class="text-[11px] text-gray-500 mt-1">{{ toPersianDigits(String(month.year)) }}</div>
				</button>
			</div>

			<hr />

			<div v-if="viewMode === 'month'" class="grid grid-cols-2 gap-2 mx-2 sm:grid-cols-4">
				<div
					v-for="status in summaryStatuses"
					:key="status"
					class="rounded-lg border border-gray-200 bg-gray-50 px-2 py-1.5"
				>
					<div class="flex flex-row gap-1 items-center">
						<span class="rounded full h-3 w-3" :class="colorMap[status]" />
						<span class="text-gray-600 text-xs font-medium leading-5"> {{ __(status) }} </span>
					</div>
					<span class="text-gray-800 text-sm font-semibold leading-5 mr-4">
						{{ summary[status] || 0 }}
					</span>
				</div>
			</div>

			<hr />
			<div class="mx-2 flex items-center justify-between gap-3">
				<div class="text-sm font-semibold text-gray-800">
					{{ `برنامه منابع انسانی ${selectedDateLabel}` }}
				</div>
				<div v-if="getSelectedDateCheckinRange() !== '-'" class="text-[11px] rounded bg-gray-100 px-2 py-1 text-gray-600">
					{{ getSelectedDateCheckinRange() }}
				</div>
			</div>

			<div
				v-if="getSelectedDateShiftRequestOptions().length"
				class="mx-2 rounded-lg border border-indigo-100 bg-indigo-50/60 px-2.5 py-2"
			>
				<div class="text-[11px] font-semibold text-indigo-800">
					شیفت‌های تایید شده این روز
				</div>
				<div class="mt-1.5 flex flex-wrap gap-2">
					<router-link
						v-for="slot in getSelectedDateShiftRequestOptions()"
						:key="`selected-shift-change-${slot.code}`"
						:to="buildShiftRequestRouteForSlot(slot)"
						class="inline-flex items-center rounded border border-indigo-200 bg-white px-2 py-1 text-[11px] font-medium text-indigo-700 hover:bg-indigo-100"
					>
						{{ `درخواست تغییر شیفت ${slot.label}` }}
					</router-link>
				</div>
			</div>

			<div v-if="dayAgendaLoading" class="mx-2 text-xs text-gray-500">
				در حال بارگذاری...
			</div>
			<div
				v-else-if="dayAgendaSections.length"
				class="mx-2 flex flex-col gap-2.5"
			>
				<div
					v-for="section in dayAgendaSections"
					:key="`agenda-section-${section.key}`"
					class="rounded-xl border px-2.5 py-2"
					:class="section.containerClass"
				>
					<div class="flex items-center justify-between gap-2">
						<div class="inline-flex items-center gap-1.5 text-xs font-semibold" :class="section.titleClass">
							<span class="h-2 w-2 rounded-full" :class="section.dotClass" />
							{{ section.title }}
						</div>
						<span class="rounded-full px-2 py-0.5 text-[10px] font-semibold" :class="section.countClass">
							{{ toPersianDigits(String(section.items.length)) }}
						</span>
					</div>
					<div class="mt-2 space-y-1.5">
						<template v-for="item in section.items" :key="item.key">
							<router-link
								v-if="item.route"
								:to="item.route"
								class="block rounded-lg border px-2.5 py-2 transition hover:bg-white/70"
								:class="section.itemClass"
							>
								<div class="flex items-center justify-between gap-2">
									<div class="truncate text-xs font-semibold text-gray-800">{{ item.title }}</div>
									<span
										v-if="item.badgeLabel"
										class="rounded-full bg-white px-2 py-0.5 text-[10px] font-medium text-gray-700"
									>
										{{ item.badgeLabel }}
									</span>
								</div>
								<div class="mt-0.5 text-[11px] text-gray-600">{{ item.subtitle }}</div>
								<div v-if="item.meta" class="mt-0.5 text-[11px] text-gray-500">{{ item.meta }}</div>
							</router-link>
							<button
								v-else-if="item.action === 'open_shift_detail'"
								type="button"
								class="w-full rounded-lg border px-2.5 py-2 text-right transition hover:bg-white/80"
								:class="section.itemClass"
								@click="openShiftDetail(item.rawShift)"
							>
								<div class="flex items-center justify-between gap-2">
									<div class="truncate text-xs font-semibold text-gray-800">{{ item.title }}</div>
									<span
										v-if="item.badgeLabel"
										class="rounded-full bg-white px-2 py-0.5 text-[10px] font-medium text-gray-700"
									>
										{{ item.badgeLabel }}
									</span>
								</div>
								<div class="mt-0.5 text-[11px] text-gray-600">{{ item.subtitle }}</div>
								<div v-if="item.meta" class="mt-0.5 text-[11px] text-gray-500">{{ item.meta }}</div>
							</button>
							<div
								v-else
								class="rounded-lg border px-2.5 py-2"
								:class="section.itemClass"
							>
								<div class="flex items-center justify-between gap-2">
									<div class="truncate text-xs font-semibold text-gray-800">{{ item.title }}</div>
									<span
										v-if="item.badgeLabel"
										class="rounded-full bg-white px-2 py-0.5 text-[10px] font-medium text-gray-700"
									>
										{{ item.badgeLabel }}
									</span>
								</div>
								<div class="mt-0.5 text-[11px] text-gray-600">{{ item.subtitle }}</div>
								<div v-if="item.meta" class="mt-0.5 text-[11px] text-gray-500">{{ item.meta }}</div>
							</div>
						</template>
					</div>
				</div>
			</div>

			<div v-else class="mx-2 text-xs text-gray-500">
				برای این روز آیتمی ثبت نشده است.
			</div>

			<hr />
			<div class="mx-2 rounded-xl border border-gray-200 bg-white p-3">
				<div class="flex items-center justify-between gap-2">
					<div class="text-sm font-semibold text-gray-800">غذای {{ selectedDateLabel }}</div>
					<span
						v-if="selectedDayMealRow"
						class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold"
						:class="getMealStatusClass(selectedDayMealRow.reservation_status)"
					>
						{{ __(selectedDayMealRow.reservation_status || "Not Required") }}
					</span>
				</div>
				<div v-if="mealPlan" class="mt-2 rounded-lg bg-gray-50 px-2.5 py-2">
					<div class="flex items-center justify-between gap-2">
						<span class="text-[11px] font-medium text-gray-600">تحویل غذا در این هفته</span>
						<span class="text-xs font-semibold text-gray-800">
							{{ toPersianDigits(String(deliveredMealsThisWeek)) }} روز
						</span>
					</div>
					<div v-if="mealWeekLabel" class="mt-1 text-[10px] text-gray-500">
						{{ mealWeekLabel }}
					</div>
				</div>

				<div v-if="mealContextResource.loading" class="mt-2 text-xs text-gray-500">در حال بارگذاری برنامه غذا...</div>
				<div v-else-if="mealErrorMessage" class="mt-2 text-xs text-red-600">{{ mealErrorMessage }}</div>
				<div v-else-if="!mealPlan" class="mt-2 text-xs text-gray-500">
					برای هفته‌ی این روز برنامه غذایی منتشر نشده است.
				</div>
				<div v-else-if="isSelectedMealAfterCutoff" class="mt-2 text-xs text-amber-700">
					مهلت رزرو غذای این روز گذشته است.
				</div>
				<div v-else-if="!selectedDayMealRow" class="mt-2 text-xs text-gray-500">
					برای این روز غذایی تعریف نشده است.
				</div>
				<div v-else class="mt-2 space-y-2">
					<div class="text-xs text-gray-700 font-semibold">{{ selectedDayMealRow.menu_title || "بدون عنوان" }}</div>
					<div v-if="selectedDayMealRow.menu_description" class="text-xs text-gray-500">
						{{ selectedDayMealRow.menu_description }}
					</div>

					<div class="grid grid-cols-2 gap-2">
						<button
							type="button"
							class="rounded-lg border px-2 py-2 text-xs font-semibold transition"
							:class="
								selectedDayMealRow.reservation_status === 'Reserved'
									? 'border-emerald-500 bg-emerald-50 text-emerald-700'
									: 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
							"
							:disabled="!canEditMealSelection || mealSaving"
							@click="setSelectedDayMealReservation('Reserved')"
						>
							{{ __("می‌خوام") }}
						</button>
						<button
							type="button"
							class="rounded-lg border px-2 py-2 text-xs font-semibold transition"
							:class="
								selectedDayMealRow.reservation_status === 'Not Required'
									? 'border-rose-500 bg-rose-50 text-rose-700'
									: 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
							"
							:disabled="!canEditMealSelection || mealSaving"
							@click="setSelectedDayMealReservation('Not Required')"
						>
							{{ __("نمی‌خوام") }}
						</button>
					</div>

					<div v-if="selectedDayMealRow.reservation_status === 'Delivered'" class="text-[10px] text-amber-600">
						غذا تحویل شده و دیگر قابل تغییر نیست.
					</div>
					<div v-else-if="selectedDayMealRow.is_locked" class="text-[10px] text-amber-600">
						{{ __("Meal already delivered and cannot be edited.") }}
					</div>
				</div>
			</div>

			<Teleport to="body">
				<div class="calendar-fab-wrap">
					<Transition name="calendar-fab-pop">
						<div
							v-if="showActionMenu"
							class="calendar-fab-menu rounded-xl border border-gray-200 bg-white p-2 shadow-2xl"
						>
							<button
								v-for="action in quickActions"
								:key="action.key"
								type="button"
								class="calendar-fab-menu-item"
								@click="openQuickAction(action)"
							>
								{{ action.label }}
							</button>
						</div>
					</Transition>

					<button
						type="button"
						class="calendar-fab-button"
						:class="{ 'calendar-fab-button-open': showActionMenu }"
						@click="showActionMenu = !showActionMenu"
					>
						+
					</button>
				</div>
			</Teleport>
		</div>
	</div>

	<Dialog v-model="showAttendanceRequestDialog">
		<template #body-title>
			<h2 class="text-base font-bold text-gray-900">ثبت سریع درخواست حضور</h2>
		</template>
		<template #body-content>
			<div class="space-y-3 text-right">
				<div class="text-xs text-gray-600">
					تاریخ انتخاب‌شده: {{ selectedDateLabel }}
				</div>

				<div class="grid grid-cols-2 gap-2">
					<button
						type="button"
						class="rounded-lg border px-2 py-2 text-xs font-semibold transition"
						:class="
							quickAttendanceLogType === 'IN'
								? 'border-emerald-500 bg-emerald-50 text-emerald-700'
								: 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
						"
						@click="quickAttendanceLogType = 'IN'"
					>
						ورود
					</button>
					<button
						type="button"
						class="rounded-lg border px-2 py-2 text-xs font-semibold transition"
						:class="
							quickAttendanceLogType === 'OUT'
								? 'border-rose-500 bg-rose-50 text-rose-700'
								: 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
						"
						@click="quickAttendanceLogType = 'OUT'"
					>
						خروج
					</button>
				</div>

				<div>
					<label class="mb-1 block text-xs font-medium text-gray-700">ساعت</label>
					<input
						v-model="quickAttendanceTime"
						type="time"
						class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
					/>
				</div>

				<div>
					<label class="mb-1 block text-xs font-medium text-gray-700">توضیح (اختیاری)</label>
					<textarea
						v-model="quickAttendanceExplanation"
						rows="2"
						class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
						placeholder="مثلا: فراموشی ثبت تردد"
					/>
				</div>

				<div v-if="quickAttendanceError" class="text-xs text-red-600">
					{{ quickAttendanceError }}
				</div>
			</div>
		</template>
		<template #actions>
			<div class="flex flex-row gap-2">
				<Button variant="outline" class="w-full py-5" @click="showAttendanceRequestDialog = false">
					انصراف
				</Button>
				<Button
					variant="solid"
					class="w-full py-5"
					:loading="quickAttendanceRequestResource.loading"
					@click="submitQuickAttendanceRequest"
				>
					ثبت درخواست
				</Button>
			</div>
		</template>
	</Dialog>

	<ion-modal
		class="shift-detail-sheet"
		:is-open="isShiftDetailSheetOpen"
		@didDismiss="closeShiftDetail"
		:initial-breakpoint="0.82"
		:breakpoints="[0, 0.82, 0.96]"
		:handle="true"
	>
		<div class="h-full overflow-y-auto p-4 text-right">
			<div class="flex items-center justify-between gap-2">
				<div class="text-sm font-semibold text-gray-900">جزئیات شیفت</div>
				<span class="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-700">
					فقط نمایش
				</span>
			</div>

			<div v-if="selectedShiftDetail" class="mt-3 space-y-2">
				<div class="rounded-lg border border-gray-200 bg-gray-50 px-2.5 py-2">
					<div class="text-[11px] text-gray-500">عنوان شیفت</div>
					<div class="mt-0.5 text-sm font-semibold text-gray-800">
						{{ selectedShiftDetail.shift_type || "شیفت کاری" }}
					</div>
				</div>

				<div class="grid grid-cols-2 gap-2">
					<div class="rounded-lg border border-gray-200 bg-white px-2.5 py-2">
						<div class="text-[11px] text-gray-500">نوبت</div>
						<div class="mt-0.5 text-sm font-semibold text-gray-800">
							{{ getShiftSlotBadge(inferShiftSlotCode(selectedShiftDetail)).label }}
						</div>
					</div>
					<div class="rounded-lg border border-gray-200 bg-white px-2.5 py-2">
						<div class="text-[11px] text-gray-500">تاریخ</div>
						<div class="mt-0.5 text-sm font-semibold text-gray-800">
							{{ formatJalaliDate(localSelectedDate) }}
						</div>
					</div>
				</div>

				<div class="rounded-lg border border-indigo-100 bg-indigo-50/50 px-2.5 py-2">
					<div class="text-[11px] text-indigo-700">ساعت کاری</div>
					<div class="mt-0.5 text-sm font-semibold text-indigo-900">
						{{ formatShiftTiming(selectedShiftDetail) }}
					</div>
				</div>

				<div class="rounded-lg border border-emerald-100 bg-emerald-50/60 px-2.5 py-2">
					<div class="text-[11px] text-emerald-700">وضعیت</div>
					<div class="mt-0.5 text-sm font-semibold text-emerald-900">
						این شیفت برای شما ثبت شده و قابل ویرایش نیست.
					</div>
				</div>

				<router-link
					v-if="canRequestShiftChangeFromSheet && getShiftChangeRouteFromDetail(selectedShiftDetail)"
					:to="getShiftChangeRouteFromDetail(selectedShiftDetail)"
					class="inline-flex w-full items-center justify-center rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 text-xs font-semibold text-sky-700 hover:bg-sky-100"
					@click="closeShiftDetail"
				>
					ثبت درخواست تغییر همین شیفت
				</router-link>
			</div>
		</div>
	</ion-modal>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue"
import { useRouter } from "vue-router"
import { createListResource, createResource, Dialog, toast } from "frappe-ui"
import { IonModal } from "@ionic/vue"
import {
	PERSIAN_MONTHS,
	formatGregorianDate,
	formatJalaliDate,
	formatJalaliTime,
	getJalaliDaysInMonth,
	gregorianToJalali,
	jalaliToGregorian,
	toPersianDigits,
} from "@/utils/jalali"

const props = defineProps({
	selectedDate: {
		type: String,
		default: "",
	},
	title: {
		type: String,
		default: "تقویم حضور و غیاب",
	},
	showShiftItems: {
		type: Boolean,
		default: true,
	},
})

const emit = defineEmits(["dateSelected"])

const router = useRouter()
const employee = inject("$employee")
const user = inject("$user")
const __ = inject("$translate")

const today = new Date()
const todayDateString = formatGregorianDate(today)
const currentJalaliDate = gregorianToJalali(
	today.getFullYear(),
	today.getMonth() + 1,
	today.getDate()
)

const localSelectedDate = ref(props.selectedDate || todayDateString)
const activeJalaliMonth = ref({
	year: currentJalaliDate.year,
	month: currentJalaliDate.month,
})
const showActionMenu = ref(false)
const viewMode = ref("month")
const mealRows = ref([])
const mealErrorMessage = ref("")
const mealSaving = ref(false)
const showAttendanceRequestDialog = ref(false)
const quickAttendanceLogType = ref("IN")
const quickAttendanceTime = ref("")
const quickAttendanceExplanation = ref("")
const quickAttendanceError = ref("")
const isShiftDetailSheetOpen = ref(false)
const selectedShiftDetail = ref(null)

const viewModes = [
	{ value: "month", label: __("Monthly") },
	{ value: "week", label: __("Weekly") },
]

const colorMap = {
	Present: "bg-green-200 dark:bg-emerald-500/35",
	"Work From Home": "bg-green-200 dark:bg-emerald-500/35",
	Absent: "bg-red-200 dark:bg-rose-500/35",
	"On Leave": "bg-blue-200 dark:bg-sky-500/35",
	Holiday: "bg-gray-200 dark:bg-slate-500/35",
}

const summaryStatuses = ["Present", "Absent", "On Leave", "Holiday"]
const calendarLegendItems = [
	{ key: "present", label: "سبز: حضور", dotClass: "bg-green-500" },
	{ key: "absent", label: "قرمز: غیبت", dotClass: "bg-red-500" },
	{ key: "leave", label: "آبی: مرخصی", dotClass: "bg-blue-500" },
	{ key: "holiday", label: "خاکستری: تعطیل", dotClass: "bg-gray-500" },
	{ key: "warning", label: "زرد: هشدار تردد", dotClass: "bg-yellow-500" },
	{ key: "morning-shift", label: "شیفت صبح", dotClass: "bg-sky-500" },
	{ key: "evening-shift", label: "شیفت عصر", dotClass: "bg-rose-500" },
]

const isShiftAllocator = computed(() =>
	Boolean(employee.data?.is_shift_allocator || employee.data?.is_shift_allocator_by_role)
)
const hasShiftPlanningAccess = computed(() =>
	Boolean(employee.data?.variable_shift || employee.data?.has_rotational_shift || employee.data?.needs_shift_registration)
)
const canRequestShiftChangeFromSheet = computed(() => hasShiftPlanningAccess.value && !isShiftAllocator.value)

const quickActions = computed(() => {
	const actions = [
		{ key: "mission", label: "درخواست ماموریت", routeName: "MissionFormView" },
		{ key: "attendance", label: "درخواست حضور", routeName: "AttendanceRequestFormView" },
		{ key: "leave", label: "درخواست مرخصی", routeName: "LeaveApplicationFormView" },
		{ key: "advance", label: "درخواست مساعده", routeName: "EmployeeAdvanceFormView" },
		{ key: "expense_claim", label: "درخواست مطالبه هزینه", routeName: "ExpenseClaimFormView" },
		{ key: "event", label: "ثبت رویداد / یادآور", routeName: "EventFormView" },
	]
	if (hasShiftPlanningAccess.value && !isShiftAllocator.value) {
		actions.splice(3, 0, {
			key: "shift_request",
			label: "درخواست تغییر شیفت",
			routeName: "ShiftRequestFormView",
		})
	}
	return actions
})

const selectedDateLabel = computed(() => formatJalaliDate(localSelectedDate.value, { withWeekday: true }))

const monthTitle = computed(() => {
	return `${PERSIAN_MONTHS[activeJalaliMonth.value.month - 1]} ${toPersianDigits(
		activeJalaliMonth.value.year
	)}`
})

const periodLabel = computed(() => {
	if (viewMode.value === "week") {
		if (!weekDays.value.length) return monthTitle.value
		const start = weekDays.value[0]?.gregorianDate
		const end = weekDays.value[weekDays.value.length - 1]?.gregorianDate
		return `${formatJalaliDate(start)} - ${formatJalaliDate(end)}`
	}
	if (viewMode.value === "year") return `${__("Year")} ${toPersianDigits(activeJalaliMonth.value.year)}`
	return monthTitle.value
})

const monthDays = computed(() => {
	const year = activeJalaliMonth.value.year
	const month = activeJalaliMonth.value.month
	const firstGregorian = jalaliToGregorian(year, month, 1)
	const firstDate = new Date(firstGregorian.year, firstGregorian.month - 1, firstGregorian.day)
	const offset = (firstDate.getDay() + 1) % 7
	const totalDays = getJalaliDaysInMonth(year, month)
	const days = []

	for (let day = 1; day <= totalDays; day++) {
		const gregorianDate = jalaliToGregorian(year, month, day)
		const date = new Date(gregorianDate.year, gregorianDate.month - 1, gregorianDate.day)
		days.push({
			key: `${year}-${month}-${day}`,
			jalaliDay: day,
			gregorianDate: formatGregorianDate(date),
			isToday:
				date.getFullYear() === today.getFullYear()
				&& date.getMonth() === today.getMonth()
				&& date.getDate() === today.getDate(),
		})
	}

	return { offset, days }
})


const monthGridDays = computed(() => {
	const days = monthDays.value.days || []
	if (!days.length) return []

	const grid = []
	const firstCurrentDate = new Date(`${days[0].gregorianDate}T12:00:00`)
	for (let index = monthDays.value.offset; index > 0; index--) {
		const date = new Date(firstCurrentDate)
		date.setDate(firstCurrentDate.getDate() - index)
		grid.push(buildCalendarCell(date, false))
	}

	for (const day of days) {
		grid.push({ ...day, key: `grid-${day.gregorianDate}`, isCurrentMonth: true })
	}

	let tailDate = new Date(`${days[days.length - 1].gregorianDate}T12:00:00`)
	while (grid.length < 42) {
		tailDate = new Date(tailDate)
		tailDate.setDate(tailDate.getDate() + 1)
		grid.push(buildCalendarCell(tailDate, false))
	}

	return grid
})

function buildCalendarCell(date, isCurrentMonth) {
	const gregorianDate = formatGregorianDate(date)
	const jalali = gregorianToJalali(date.getFullYear(), date.getMonth() + 1, date.getDate())
	return {
		key: `grid-${gregorianDate}`,
		jalaliDay: jalali.day,
		gregorianDate,
		isToday: gregorianDate === todayDateString,
		isCurrentMonth,
	}
}


const weekDays = computed(() => {
	const referenceDate = new Date(`${localSelectedDate.value || todayDateString}T12:00:00`)
	const start = new Date(referenceDate)
	const startOffset = (start.getDay() + 1) % 7
	start.setDate(start.getDate() - startOffset)

	return DAYS.map((label, index) => {
		const date = new Date(start)
		date.setDate(start.getDate() + index)
		const gregorianDate = formatGregorianDate(date)
		const jalali = gregorianToJalali(date.getFullYear(), date.getMonth() + 1, date.getDate())
		return {
			key: `week-${gregorianDate}`,
			weekdayShort: label,
			gregorianDate,
			jalaliDay: jalali.day,
			isToday: gregorianDate === todayDateString,
		}
	})
})

const yearMonths = computed(() => {
	return PERSIAN_MONTHS.map((label, index) => ({
		month: index + 1,
		year: activeJalaliMonth.value.year,
		label,
	}))
})

const summary = computed(() => {
	const result = {
		Present: 0,
		Absent: 0,
		"On Leave": 0,
		Holiday: 0,
	}

	for (const day of monthDays.value.days) {
		const date = day.gregorianDate
		const calendarStatus = calendarEvents.data?.[date]
		if (date > todayDateString) continue

		if (calendarStatus === "Holiday") {
			result.Holiday += 1
			continue
		}

		if (isApprovedLeaveDate(date) || calendarStatus === "On Leave") {
			result["On Leave"] += 1
			continue
		}

		if (
			calendarStatus === "Present"
			|| calendarStatus === "Work From Home"
			|| calendarStatus === "Half Day"
		) {
			result.Present += 1
			continue
		}

		const checkinSummary = monthCheckinSummary.value[date]
		if (!checkinSummary || !checkinSummary.total) {
			if (hasScheduledShift(date) && date === todayDateString) {
				result.Present += 1
				continue
			}
			result.Absent += 1
			continue
		}

		const hasIn = (checkinSummary.IN || 0) > 0
		const hasOut = (checkinSummary.OUT || 0) > 0
		if (hasIn || hasOut) {
			result.Present += 1
		} else {
			result.Absent += 1
		}
	}

	return result
})

const monthCheckinSummary = computed(() => {
	const summaryByDate = {}
	for (const checkin of monthCheckins.data || []) {
		const date = String(checkin.time || "").slice(0, 10)
		if (!date) continue
		if (!summaryByDate[date]) {
			summaryByDate[date] = {
				IN: 0,
				OUT: 0,
				total: 0,
				firstIn: "",
				lastOut: "",
			}
		}
		summaryByDate[date][checkin.log_type] = (summaryByDate[date][checkin.log_type] || 0) + 1
		summaryByDate[date].total += 1
		if (checkin.log_type === "IN" && !summaryByDate[date].firstIn) {
			summaryByDate[date].firstIn = checkin.time
		}
		if (checkin.log_type === "OUT") {
			summaryByDate[date].lastOut = checkin.time
		}
	}
	return summaryByDate
})

const missionSummaryByDate = computed(() => {
	const summaryByDate = {}
	const rows = Array.isArray(missionsResource.data) ? missionsResource.data : []

	for (const mission of rows) {
		const dates = getMissionDates(mission)
		if (!dates.length) continue
		const missionMinutes = getMissionDurationMinutes(mission)

		for (const date of dates) {
			if (!summaryByDate[date]) {
				summaryByDate[date] = {
					count: 0,
					totalMinutes: 0,
					hasDailySpan: false,
				}
			}
			summaryByDate[date].count += 1
			if (missionMinutes > 0) {
				summaryByDate[date].totalMinutes += missionMinutes
			} else {
				summaryByDate[date].hasDailySpan = true
			}
		}
	}

	return summaryByDate
})

const normalizedShiftRows = computed(() => {
	if (!props.showShiftItems) return []

	const rows = []
	const seenKeys = new Set()
	const pushShiftRow = (row) => {
		const dedupeKey = [
			row.start_date || "",
			row.end_date || "",
			inferShiftSlotCode(row),
			row.shift_type || "",
			row.start_time || "",
			row.end_time || "",
		].join("::")
		if (seenKeys.has(dedupeKey)) return
		seenKeys.add(dedupeKey)
		rows.push(row)
	}

	for (const shift of shiftsResource.data || []) {
		pushShiftRow({
			name: shift.name,
			shift_type: shift.shift_type,
			start_date: shift.start_date,
			end_date: shift.end_date || shift.start_date,
			start_time: shift.start_time,
			end_time: shift.end_time,
			slot_code: "",
		})
	}

	for (const slot of finalizedShiftSlotsResource.data || []) {
		const workDate = String(slot.work_date || "")
		if (!workDate) continue
		pushShiftRow({
			name: slot.name || `final-${workDate}-${slot.slot_code || ""}`,
			shift_type: slot.shift_type,
			start_date: workDate,
			end_date: workDate,
			start_time: slot.start_time,
			end_time: slot.end_time,
			slot_code: slot.slot_code || "",
		})
	}

	return rows
})

const monthShiftSummary = computed(() => {
	if (!props.showShiftItems) return {}

	const summaryByDate = {}
	const range = getMonthDateRange()
	for (const shift of normalizedShiftRows.value) {
		if (!shift.start_date) continue
		const shiftStart = shift.start_date > range.fromDate ? shift.start_date : range.fromDate
		const shiftEnd = (shift.end_date || shift.start_date) < range.toDate
			? shift.end_date || shift.start_date
			: range.toDate
		if (shiftStart > shiftEnd) continue

		for (const date of expandDateRange(shiftStart, shiftEnd)) {
			if (!summaryByDate[date]) summaryByDate[date] = []
			summaryByDate[date].push(shift)
		}
	}
	return summaryByDate
})

const selectedDateShifts = computed(() => monthShiftSummary.value[localSelectedDate.value] || [])
const selectedDateCheckins = computed(() => dailyCheckins.data || [])

const selectedDateLeaves = computed(() => {
	const date = localSelectedDate.value
	return (monthLeaveApplications.data || []).filter((leave) => {
		const startDate = String(leave.from_date || "")
		const endDate = String(leave.to_date || leave.from_date || "")
		return startDate && endDate && startDate <= date && endDate >= date
	})
})

const selectedDateMissions = computed(() => {
	const date = localSelectedDate.value
	const rows = Array.isArray(missionsResource.data) ? missionsResource.data : []
	return rows.filter((mission) => isMissionOnDate(mission, date))
})

const dayRequestSummaryByDate = computed(() => {
	const range = getMonthDateRange()
	const summaryByDate = {}
	const ensureDate = (date) => {
		if (!date) return null
		if (!summaryByDate[date]) {
			summaryByDate[date] = {
				attendance: 0,
				shift: 0,
				leave: 0,
				expense: 0,
				advance: 0,
				event: 0,
			}
		}
		return summaryByDate[date]
	}
	const pushRange = (fromDate, toDate, key) => {
		if (!(fromDate && toDate)) return
		const start = fromDate > range.fromDate ? fromDate : range.fromDate
		const end = toDate < range.toDate ? toDate : range.toDate
		if (start > end) return
		for (const date of expandDateRange(start, end)) {
			const daySummary = ensureDate(date)
			if (!daySummary) continue
			daySummary[key] += 1
		}
	}

	for (const row of monthAttendanceRequests.data || []) {
		pushRange(String(row.from_date || "").slice(0, 10), String(row.to_date || row.from_date || "").slice(0, 10), "attendance")
	}
	for (const row of monthShiftRequests.data || []) {
		pushRange(String(row.from_date || "").slice(0, 10), String(row.to_date || row.from_date || "").slice(0, 10), "shift")
	}
	for (const row of monthLeaveApplications.data || []) {
		pushRange(String(row.from_date || "").slice(0, 10), String(row.to_date || row.from_date || "").slice(0, 10), "leave")
	}
	for (const row of monthExpenseClaims.data || []) {
		const postingDate = String(row.posting_date || "").slice(0, 10)
		const daySummary = ensureDate(postingDate)
		if (!daySummary) continue
		daySummary.expense += 1
	}
	for (const row of monthAdvances.data || []) {
		const postingDate = String(row.posting_date || "").slice(0, 10)
		const daySummary = ensureDate(postingDate)
		if (!daySummary) continue
		daySummary.advance += 1
	}
	for (const row of monthEvents.data || []) {
		pushRange(
			String(row.starts_on || "").slice(0, 10),
			String(row.ends_on || row.starts_on || "").slice(0, 10),
			"event"
		)
	}

	return summaryByDate
})

const mealPlan = computed(() => mealContextResource.data?.plan || null)

const mealRowByDate = computed(() => {
	const map = {}
	for (const row of mealRows.value) {
		if (!row?.meal_date) continue
		map[row.meal_date] = row
	}
	return map
})

const mealStatusByDate = computed(() => {
	const map = {}
	for (const row of mealRows.value) {
		if (!row?.meal_date) continue
		if (row.after_cutoff) continue
		map[row.meal_date] = row.reservation_status || "Not Required"
	}
	return map
})

const deliveredMealsThisWeek = computed(() =>
	mealRows.value.filter((row) => row.reservation_status === "Delivered").length
)

const mealWeekLabel = computed(() => {
	const start = mealContextResource.data?.week_start_date
	const end = mealContextResource.data?.week_end_date
	if (!(start && end)) return ""
	return `${formatJalaliDate(start)} - ${formatJalaliDate(end)}`
})

const selectedDayMealRow = computed(() => {
	const date = localSelectedDate.value
	return mealRows.value.find((row) => row.meal_date === date) || null
})

const isSelectedMealAfterCutoff = computed(() => Boolean(selectedDayMealRow.value?.after_cutoff))

const canEditMealSelection = computed(() => {
	const row = selectedDayMealRow.value
	if (!row) return false
	if (!mealPlan.value?.name) return false
	if (!mealContextResource.data?.can_edit_reservations) return false
	if (row.reservation_status === "Delivered") return false
	if (row.is_locked || row.after_cutoff) return false
	return true
})

const leaveDateStates = computed(() => {
	const states = {}
	const range = getMonthDateRange()
	for (const leave of monthLeaveApplications.data || []) {
		const startDate = leave.from_date > range.fromDate ? leave.from_date : range.fromDate
		const endDate = leave.to_date < range.toDate ? leave.to_date : range.toDate
		if (!startDate || !endDate || startDate > endDate) continue

		const leaveState = getLeaveState(leave)
		if (!leaveState) continue

		for (const date of expandDateRange(startDate, endDate)) {
			if (!states[date] || leaveState === "approved") {
				states[date] = leaveState
			}
		}
	}
	return states
})


const dayIndicatorsByDate = computed(() => {
	const map = {}
	for (const day of monthGridDays.value) {
		map[day.gregorianDate] = buildDayIndicators(day.gregorianDate)
	}
	return map
})

const agendaSectionStyles = {
	shift: {
		containerClass: "border-sky-200 bg-sky-50/40",
		titleClass: "text-sky-800",
		dotClass: "bg-sky-500",
		countClass: "bg-sky-100 text-sky-700",
		itemClass: "border-sky-100 bg-white",
	},
	mission: {
		containerClass: "border-violet-200 bg-violet-50/40",
		titleClass: "text-violet-800",
		dotClass: "bg-violet-500",
		countClass: "bg-violet-100 text-violet-700",
		itemClass: "border-violet-100 bg-white",
	},
	checkin: {
		containerClass: "border-emerald-200 bg-emerald-50/40",
		titleClass: "text-emerald-800",
		dotClass: "bg-emerald-500",
		countClass: "bg-emerald-100 text-emerald-700",
		itemClass: "border-emerald-100 bg-white",
	},
	attendance_request: {
		containerClass: "border-yellow-200 bg-yellow-50/40",
		titleClass: "text-yellow-800",
		dotClass: "bg-yellow-500",
		countClass: "bg-yellow-100 text-yellow-700",
		itemClass: "border-yellow-100 bg-white",
	},
	shift_request: {
		containerClass: "border-rose-200 bg-rose-50/40",
		titleClass: "text-rose-800",
		dotClass: "bg-rose-500",
		countClass: "bg-rose-100 text-rose-700",
		itemClass: "border-rose-100 bg-white",
	},
	leave: {
		containerClass: "border-blue-200 bg-blue-50/40",
		titleClass: "text-blue-800",
		dotClass: "bg-blue-500",
		countClass: "bg-blue-100 text-blue-700",
		itemClass: "border-blue-100 bg-white",
	},
	event: {
		containerClass: "border-gray-200 bg-gray-50/70",
		titleClass: "text-gray-700",
		dotClass: "bg-gray-500",
		countClass: "bg-white text-gray-700",
		itemClass: "border-gray-200 bg-white",
	},
	expense: {
		containerClass: "border-amber-200 bg-amber-50/40",
		titleClass: "text-amber-800",
		dotClass: "bg-amber-500",
		countClass: "bg-amber-100 text-amber-700",
		itemClass: "border-amber-100 bg-white",
	},
	advance: {
		containerClass: "border-teal-200 bg-teal-50/40",
		titleClass: "text-teal-800",
		dotClass: "bg-teal-500",
		countClass: "bg-teal-100 text-teal-700",
		itemClass: "border-teal-100 bg-white",
	},
}

function getMissionAgendaTiming(row) {
	const hourlyDate = String(row?.hourly_date || "").slice(0, 10)
	const startDate = String(row?.start_date || "").slice(0, 10)
	const endDate = String(row?.end_date || row?.start_date || "").slice(0, 10)
	const fromTime = String(row?.hourly_from_time || "").slice(0, 5)
	const toTime = String(row?.hourly_to_time || "").slice(0, 5)

	if (hourlyDate) {
		const timeRange = fromTime && toTime ? ` • ${toPersianDigits(fromTime)} - ${toPersianDigits(toTime)}` : ""
		return `ماموریت ساعتی • ${formatJalaliDate(hourlyDate)}${timeRange}`
	}

	if (startDate && endDate && startDate !== endDate) {
		return `ماموریت روزانه • ${formatJalaliDate(startDate)} تا ${formatJalaliDate(endDate)}`
	}
	if (startDate) {
		return `ماموریت روزانه • ${formatJalaliDate(startDate)}`
	}
	return "ماموریت"
}

function getMissionAgendaDetails(row) {
	const details = []
	if (row?.destination) details.push(`مقصد: ${row.destination}`)
	if (row?.purpose) details.push(`هدف: ${row.purpose}`)
	if (row?.notes) details.push(`توضیح: ${row.notes}`)
	return details.join(" • ")
}

function buildAgendaSection(key, title, items) {
	if (!items.length) return null
	return {
		key,
		title,
		items,
		...(agendaSectionStyles[key] || agendaSectionStyles.event),
	}
}

const dayAgendaSections = computed(() => {
	const sections = []

		if (props.showShiftItems) {
			const shiftItems = selectedDateShifts.value.map((shift, index) => {
				const slot = getShiftSlotBadge(inferShiftSlotCode(shift))
				return {
					key: `shift-${shift.name || index}`,
					title: shift.shift_type || `شیفت ${slot.label}`,
					subtitle: formatShiftDateRange(shift),
					meta: `ساعت ${formatShiftTiming(shift)}`,
					badgeLabel: slot.label,
					action: "open_shift_detail",
					rawShift: shift,
					route: null,
				}
			})
		const shiftSection = buildAgendaSection("shift", "شیفت‌های این روز", shiftItems)
		if (shiftSection) sections.push(shiftSection)
	}

	const missionItems = selectedDateMissions.value.map((row) => {
		const missionId = row.id || row.name
		return {
			key: `mission-${missionId}`,
			title: row.title || row.destination || missionId || "ماموریت",
			subtitle: getMissionAgendaTiming(row),
			meta: getMissionAgendaDetails(row) || `وضعیت: ${row.status || "-"}`,
			route: { name: "MissionDetailView", params: { id: missionId } },
		}
	})
	const missionSection = buildAgendaSection("mission", "ماموریت‌ها", missionItems)
	if (missionSection) sections.push(missionSection)

	const checkinItems = selectedDateCheckins.value.map((checkin) => ({
		key: `checkin-${checkin.name}`,
		title: `ثبت ${__(checkin.log_type || "")}`,
		subtitle: `زمان ثبت: ${getCheckinTime(checkin.time)}`,
		meta: "",
		route: { name: "EmployeeCheckinListView" },
	}))
	const checkinSection = buildAgendaSection("checkin", "ترددها", checkinItems)
	if (checkinSection) sections.push(checkinSection)

	const attendanceRequestItems = (dailyAttendanceRequests.data || []).map((row) => ({
		key: `attendance-${row.name}`,
		title: `درخواست حضور ${row.name}`,
		subtitle: `وضعیت: ${row.status || row.workflow_state || "-"}`,
		meta: "",
		route: { name: "AttendanceRequestDetailView", params: { id: row.name } },
	}))
	const attendanceRequestSection = buildAgendaSection(
		"attendance_request",
		"درخواست‌های حضور",
		attendanceRequestItems
	)
	if (attendanceRequestSection) sections.push(attendanceRequestSection)

	const shiftRequestItems = (dailyShiftRequests.data || []).map((row) => ({
		key: `shift-request-${row.name}`,
		title: `درخواست تغییر شیفت ${row.name}`,
		subtitle: `وضعیت: ${row.status || row.workflow_state || "-"}`,
		meta: `${formatJalaliDate(row.from_date)}${row.to_date && row.to_date !== row.from_date ? ` تا ${formatJalaliDate(row.to_date)}` : ""}`,
		route: { name: "ShiftRequestDetailView", params: { id: row.name } },
	}))
	const shiftRequestSection = buildAgendaSection("shift_request", "درخواست‌های تغییر شیفت", shiftRequestItems)
	if (shiftRequestSection) sections.push(shiftRequestSection)

	const leaveItems = selectedDateLeaves.value.map((row) => ({
		key: `leave-${row.name}`,
		title: `درخواست مرخصی ${row.leave_type || row.name}`,
		subtitle: `وضعیت: ${row.status || row.workflow_state || "-"}`,
		meta: "",
		route: { name: "LeaveApplicationDetailView", params: { id: row.name } },
	}))
	const leaveSection = buildAgendaSection("leave", "مرخصی‌ها", leaveItems)
	if (leaveSection) sections.push(leaveSection)

	const eventItems = (dailyEvents.data || []).map((row) => ({
		key: `event-${row.name}`,
		title: row.subject || row.name || "رویداد",
		subtitle: formatEventTiming(row),
		meta: row.event_type ? `نوع: ${row.event_type}` : "",
		route: { name: "EventDetailView", params: { id: row.name } },
	}))
	const eventSection = buildAgendaSection("event", "رویدادها و یادآورها", eventItems)
	if (eventSection) sections.push(eventSection)

	const expenseItems = (dailyExpenseClaims.data || []).map((row) => ({
		key: `claim-${row.name}`,
		title: `مطالبه هزینه ${row.name}`,
		subtitle: `${row.status || row.approval_status || "-"} • ${formatAmount(row.total_claimed_amount, row.currency)}`,
		meta: "",
		route: { name: "ExpenseClaimDetailView", params: { id: row.name } },
	}))
	const expenseSection = buildAgendaSection("expense", "هزینه‌ها", expenseItems)
	if (expenseSection) sections.push(expenseSection)

	const advanceItems = (dailyAdvances.data || []).map((row) => ({
		key: `advance-${row.name}`,
		title: `درخواست مساعده ${row.name}`,
		subtitle: `${row.status || "-"} • ${formatAmount(row.advance_amount, row.currency)}`,
		meta: row.purpose ? `هدف: ${row.purpose}` : "",
		route: { name: "EmployeeAdvanceDetailView", params: { id: row.name } },
	}))
	const advanceSection = buildAgendaSection("advance", "مساعده‌ها", advanceItems)
	if (advanceSection) sections.push(advanceSection)

	return sections
})

const dayAgendaLoading = computed(() => {
	return Boolean(
		dailyCheckins.list.loading
		|| dailyAttendanceRequests.list.loading
		|| dailyShiftRequests.list.loading
		|| dailyExpenseClaims.list.loading
		|| dailyAdvances.list.loading
		|| dailyEvents.list.loading
		|| missionsResource.loading
	)
})

function openQuickAction(action) {
	if (action.key === "attendance") {
		openQuickAttendanceRequestDialog()
		return
	}
	if (action.key === "shift_request") {
		showActionMenu.value = false
		router.push({
			name: action.routeName,
			query: {
				from_date: localSelectedDate.value,
				to_date: localSelectedDate.value,
			},
		})
		return
	}

	showActionMenu.value = false
	router.push({
		name: action.routeName,
		query: { date: localSelectedDate.value },
	})
}

function openShiftDetail(shift) {
	if (!shift) return
	selectedShiftDetail.value = shift
	isShiftDetailSheetOpen.value = true
}

function closeShiftDetail() {
	isShiftDetailSheetOpen.value = false
	selectedShiftDetail.value = null
}

function getShiftChangeRouteFromDetail(shift) {
	if (!shift || !canRequestShiftChangeFromSheet.value) return null

	const slotCode = inferShiftSlotCode(shift)
	const date = localSelectedDate.value || String(shift.start_date || "")
	if (!date) return null

	return {
		name: "ShiftRequestFormView",
		query: {
			from_date: date,
			to_date: date,
			slot_code: slotCode,
			shift_type: String(shift.shift_type || ""),
		},
	}
}

function getCurrentTimeValue() {
	const now = new Date()
	const hour = String(now.getHours()).padStart(2, "0")
	const minute = String(now.getMinutes()).padStart(2, "0")
	return `${hour}:${minute}`
}

function openQuickAttendanceRequestDialog() {
	showActionMenu.value = false
	quickAttendanceError.value = ""
	quickAttendanceLogType.value = "IN"
	quickAttendanceTime.value = getCurrentTimeValue()
	quickAttendanceExplanation.value = ""
	showAttendanceRequestDialog.value = true
}

function submitQuickAttendanceRequest() {
	if (!employee.data?.name) {
		quickAttendanceError.value = "اطلاعات کارمند یافت نشد."
		return
	}

	const selectedDate = localSelectedDate.value || todayDateString
	const selectedTime = String(quickAttendanceTime.value || "").trim() || getCurrentTimeValue()
	const logType = quickAttendanceLogType.value === "OUT" ? "OUT" : "IN"
	const logTypeLabel = logType === "OUT" ? "خروج" : "ورود"

	quickAttendanceError.value = ""
	quickAttendanceRequestResource.submit(
		{
			doc: {
				doctype: "Attendance Request",
				employee: employee.data.name,
				company: employee.data.company,
				from_date: selectedDate,
				to_date: selectedDate,
				request_mode: "Checkin Request",
				requested_log_type: logType,
				requested_time: selectedTime,
				review_status: "Pending",
				reason: "On Duty",
				half_day: 0,
				include_holidays: 0,
				explanation:
					String(quickAttendanceExplanation.value || "").trim()
					|| `درخواست ثبت ${logTypeLabel} در ساعت ${selectedTime}`,
			},
		},
		{
			onSuccess() {
				showAttendanceRequestDialog.value = false
				loadDailyAttendanceRequests(selectedDate)
				toast({
					title: __("Success"),
					text: __("Attendance request created successfully."),
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			},
			onError(error) {
				quickAttendanceError.value = extractErrorMessage(
					error,
					"ثبت درخواست حضور ناموفق بود."
				)
			},
		}
	)
}

function setViewMode(mode) {
	viewMode.value = mode
	showActionMenu.value = false
}

function normalizeMealRows(rows) {
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

function loadMealContext(date) {
	if (!date) return
	mealErrorMessage.value = ""
	mealContextResource.fetch(
		{ week_start_date: date },
		{
			onSuccess(data) {
				mealRows.value = normalizeMealRows(data?.reservations || [])
			},
			onError(error) {
				mealRows.value = []
				mealErrorMessage.value = extractErrorMessage(error, "بارگذاری برنامه غذا ناموفق بود.")
			},
		}
	)
}

function setSelectedDayMealReservation(status) {
	const row = selectedDayMealRow.value
	if (!row || !canEditMealSelection.value || !mealPlan.value?.name || mealSaving.value) return

	mealSaving.value = true
	mealErrorMessage.value = ""
	const payload = mealRows.value.map((entry) => ({
		meal_date: entry.meal_date,
		reservation_status: entry.meal_date === row.meal_date ? status : entry.reservation_status,
		reservation_note: entry.reservation_note || "",
	}))

	saveMealReservationResource.submit(
		{
			plan_name: mealPlan.value.name,
			reservations: JSON.stringify(payload),
		},
		{
			onSuccess(data) {
				mealRows.value = normalizeMealRows(data?.reservations || [])
				loadMealContext(localSelectedDate.value)
				toast({
					title: __("Success"),
					text: __("Meal reservations saved successfully."),
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
				mealSaving.value = false
			},
			onError(error) {
				mealErrorMessage.value = extractErrorMessage(error, __("Failed to save meal reservations."))
				mealSaving.value = false
			},
		}
	)
}

function getMealStatusClass(status) {
	if (status === "Reserved") return "bg-emerald-100 text-emerald-700"
	if (status === "Delivered") return "bg-indigo-100 text-indigo-700"
	return "bg-gray-100 text-gray-600"
}

function getMealEmoji(date) {
	const row = mealRowByDate.value[date]
	if (!row || row.after_cutoff) return ""
	const status = mealStatusByDate.value[date]
	if (status === "Reserved" || status === "Delivered") return "🍱"
	if (status === "Not Required") return "🍽️"
	return ""
}

function extractErrorMessage(error, fallbackMessage) {
	if (Array.isArray(error?.messages) && error.messages.length) return error.messages[0]
	if (typeof error?.message === "string" && error.message.trim()) return error.message
	return fallbackMessage
}

function openYearFromMonth() {
	if (viewMode.value !== "month") return
	viewMode.value = "year"
	showActionMenu.value = false
}

function goToToday() {
	localSelectedDate.value = todayDateString
	syncActiveMonthWithDate(todayDateString)
	showActionMenu.value = false
}

function openMonthFromYear(month) {
	activeJalaliMonth.value = { year: activeJalaliMonth.value.year, month }
	viewMode.value = "month"
	showActionMenu.value = false
}

function syncActiveMonthWithDate(dateString) {
	if (!dateString) return
	const date = new Date(`${dateString}T12:00:00`)
	const jalali = gregorianToJalali(date.getFullYear(), date.getMonth() + 1, date.getDate())
	activeJalaliMonth.value = { year: jalali.year, month: jalali.month }
}

function shiftMonth(delta) {
	if (viewMode.value === "month") {
		let month = activeJalaliMonth.value.month + delta
		let year = activeJalaliMonth.value.year
		if (month < 1) {
			month = 12
			year -= 1
		} else if (month > 12) {
			month = 1
			year += 1
		}
		activeJalaliMonth.value = { year, month }
	} else if (viewMode.value === "year") {
		activeJalaliMonth.value = {
			year: activeJalaliMonth.value.year + delta,
			month: activeJalaliMonth.value.month,
		}
	} else {
		const dayStep = 7
		const date = new Date(`${localSelectedDate.value || todayDateString}T12:00:00`)
		date.setDate(date.getDate() + delta * dayStep)
		const nextDate = formatGregorianDate(date)
		localSelectedDate.value = nextDate
		syncActiveMonthWithDate(nextDate)
	}
	showActionMenu.value = false
}

function selectDate(day) {
	localSelectedDate.value = day.gregorianDate
	syncActiveMonthWithDate(day.gregorianDate)
	showActionMenu.value = false
}

function getMonthCellClass(day) {
	if (!day.isCurrentMonth) return "bg-gray-50 text-gray-400 dark:bg-slate-900/40 dark:text-slate-500"
	const state = getDayAttendanceState(day.gregorianDate)
	const stateClassMap = {
		present: "bg-green-50 dark:bg-emerald-900/35",
		leave: "bg-blue-50 dark:bg-sky-900/35",
		absent: "bg-red-50 dark:bg-rose-900/35",
		warning: "bg-yellow-50 dark:bg-amber-900/35",
		holiday: "bg-gray-50 dark:bg-slate-800/60",
	}
	const base = stateClassMap[state] || "bg-white dark:bg-slate-900/70"
	const selected = localSelectedDate.value === day.gregorianDate
	if (selected) return `${base} ring-2 ring-gray-900/20 dark:ring-slate-100/40`
	if (day.isToday) return `${base} ring-1 ring-amber-300 dark:ring-amber-400/70`
	return `${base} hover:bg-slate-50 dark:hover:bg-slate-800/80`
}

function getMonthDayClass(day) {
	if (localSelectedDate.value === day.gregorianDate) return "bg-gray-900 text-white shadow-sm dark:bg-slate-100 dark:text-slate-900"
	if (day.isToday) return "bg-amber-500 text-white"
	if (!day.isCurrentMonth) return "text-gray-400 dark:text-slate-500"
	const state = getDayAttendanceState(day.gregorianDate)
	if (state === "present") return "text-green-700 dark:text-emerald-300"
	if (state === "warning") return "text-yellow-700 dark:text-amber-300"
	if (state === "leave") return "text-blue-700 dark:text-sky-300"
	if (state === "absent") return "text-red-700 dark:text-rose-300"
	return "text-gray-900 dark:text-slate-100"
}

function getWeekCellClass(day) {
	const state = getDayAttendanceState(day.gregorianDate)
	const classByState = {
		present: "border-green-200 bg-green-50 dark:border-emerald-600/50 dark:bg-emerald-900/30",
		warning: "border-yellow-200 bg-yellow-50 dark:border-amber-600/50 dark:bg-amber-900/30",
		leave: "border-blue-200 bg-blue-50 dark:border-sky-600/50 dark:bg-sky-900/30",
		absent: "border-red-200 bg-red-50 dark:border-rose-600/50 dark:bg-rose-900/30",
		holiday: "border-gray-200 bg-gray-50 dark:border-slate-700 dark:bg-slate-800/60",
	}
	const base = classByState[state] || "border-gray-200 bg-white hover:bg-gray-50 dark:border-slate-700 dark:bg-slate-900/70 dark:hover:bg-slate-800/80"
	if (localSelectedDate.value === day.gregorianDate) return `${base} ring-2 ring-gray-900/20 dark:ring-slate-100/40`
	if (day.isToday) return `${base} ring-1 ring-amber-300 dark:ring-amber-400/70`
	return base
}

function getWeekDayNumberClass(day) {
	if (localSelectedDate.value === day.gregorianDate) return "bg-gray-900 text-white dark:bg-slate-100 dark:text-slate-900"
	if (day.isToday) return "bg-amber-500 text-white"
	const state = getDayAttendanceState(day.gregorianDate)
	if (state === "present") return "text-green-700 bg-white/80 dark:text-emerald-200 dark:bg-slate-900/70"
	if (state === "warning") return "text-yellow-700 bg-white/80 dark:text-amber-200 dark:bg-slate-900/70"
	if (state === "leave") return "text-blue-700 bg-white/80 dark:text-sky-200 dark:bg-slate-900/70"
	if (state === "absent") return "text-red-700 bg-white/80 dark:text-rose-200 dark:bg-slate-900/70"
	return "text-gray-800 bg-white/80 dark:text-slate-200 dark:bg-slate-900/70"
}

function buildDayIndicators(date) {
	const indicators = []
	const seen = new Set()
	const addIndicator = (key, label, badgeClass, dotClass) => {
		if (seen.has(key)) return
		seen.add(key)
		indicators.push({ key, label, badgeClass, dotClass })
	}

	const status = calendarEvents.data?.[date]
	const leaveState = leaveDateStates.value[date]

	if (props.showShiftItems && hasScheduledShift(date)) {
		addIndicator(
			"shift",
			"شیفت",
			"bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-200",
			"bg-sky-500"
		)
	}

	if (leaveState === "approved" || status === "On Leave") {
		addIndicator("leave", "مرخصی", "bg-blue-100 text-blue-700 dark:bg-sky-900/40 dark:text-sky-200", "bg-blue-500")
	} else if (leaveState === "pending") {
		addIndicator("leave-pending", "مرخصی در انتظار", "bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-200", "bg-sky-500")
	}

	if (status === "Holiday") {
		addIndicator("holiday", "تعطیل", "bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200", "bg-gray-500")
	}

	if (hasMissionOnDate(date)) {
		addIndicator("mission", "ماموریت", "bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-200", "bg-violet-500")
	}

	if (hasSingleLogType(date)) {
		addIndicator("single-log", "هشدار تردد", "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-200", "bg-rose-500")
	}

	if (status === "Absent") {
		addIndicator("absent", "غیبت", "bg-red-100 text-red-700 dark:bg-rose-900/40 dark:text-rose-200", "bg-red-500")
	} else if (status === "Present" || status === "Work From Home" || status === "Half Day") {
		addIndicator("present", "حضور", "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200", "bg-emerald-500")
	}

	return indicators
}

function getDayIndicators(date) {
	if (!date) return []
	return dayIndicatorsByDate.value[date] || buildDayIndicators(date)
}

function getDayIndicatorCount(date) {
	return getDayIndicators(date).length
}

function getDayIndicatorSummaryText(date) {
	const first = getDayIndicators(date)[0]
	if (!first) return { badgeClass: "bg-gray-100 text-gray-600 dark:bg-slate-800 dark:text-slate-300" }
	return { badgeClass: first.badgeClass }
}

function hasScheduledShift(date) {
	if (!props.showShiftItems) return false
	return Boolean(monthShiftSummary.value[date]?.length)
}

function hasMissionOnDate(date) {
	return Boolean(getDayMissionSummary(date)?.count)
}

function hasSingleLogType(date) {
	const summaryByDate = monthCheckinSummary.value[date]
	if (!summaryByDate) return false
	const hasIn = (summaryByDate.IN || 0) > 0
	const hasOut = (summaryByDate.OUT || 0) > 0
	return hasIn !== hasOut
}

function getCheckinTime(timestamp) {
	return formatJalaliTime(timestamp, { withSeconds: true })
}

function formatShiftTiming(shift) {
	const start = String(shift.start_time || "").slice(0, 5)
	const end = String(shift.end_time || "").slice(0, 5)
	if (!(start && end)) return "-"
	return `${toPersianDigits(start)} - ${toPersianDigits(end)}`
}

function formatShiftDateRange(shift) {
	const startDate = String(shift.start_date || "")
	const endDate = String(shift.end_date || shift.start_date || "")
	if (!(startDate && endDate)) return "-"
	if (startDate === endDate) return formatJalaliDate(startDate)
	return `${formatJalaliDate(startDate)} تا ${formatJalaliDate(endDate)}`
}

function parseShiftTimeToMinutes(value) {
	const normalized = String(value || "").slice(0, 5)
	const [hourText = "", minuteText = ""] = normalized.split(":")
	const hour = Number(hourText)
	const minute = Number(minuteText)
	if (!Number.isFinite(hour) || !Number.isFinite(minute)) return null
	return hour * 60 + minute
}

function inferShiftSlotCode(shift) {
	const explicitSlot = String(shift?.slot_code || "").toLowerCase()
	if (explicitSlot === "morning") return "Morning"
	if (explicitSlot === "evening") return "Evening"

	const shiftName = String(shift?.shift_type || "").toLowerCase()
	if (shiftName.includes("morning") || shiftName.includes("صبح")) return "Morning"
	if (shiftName.includes("evening") || shiftName.includes("عصر")) return "Evening"

	const startMinutes = parseShiftTimeToMinutes(shift?.start_time)
	if (startMinutes === null) return "Shift"
	return startMinutes < 15 * 60 ? "Morning" : "Evening"
}

function getShiftSlotBadge(slotCode) {
	if (slotCode === "Morning") {
		return {
			code: "Morning",
			label: "صبح",
			badgeClass: "bg-sky-100 text-sky-700",
		}
	}
	if (slotCode === "Evening") {
		return {
			code: "Evening",
			label: "عصر",
			badgeClass: "bg-rose-100 text-rose-700",
		}
	}
	return {
		code: slotCode || "Shift",
		label: "شیفت",
		badgeClass: "bg-slate-100 text-slate-700",
	}
}

function getDayShiftSlotCodes(date) {
	const shifts = monthShiftSummary.value[date] || []
	if (!shifts.length) return []

	const uniqueSlots = new Set()
	for (const shift of shifts) {
		uniqueSlots.add(inferShiftSlotCode(shift))
	}

	return [...uniqueSlots]
		.map((slotCode) => getShiftSlotBadge(slotCode))
		.sort((left, right) => {
			const order = { Morning: 1, Evening: 2, Shift: 3 }
			return (order[left.code] || 99) - (order[right.code] || 99)
		})
		.map((slot) => slot.code)
}

function getDayShiftSlotSummary(date) {
	const slotCodes = getDayShiftSlotCodes(date)
	if (!slotCodes.length) return null

	const hasMorning = slotCodes.includes("Morning")
	const hasEvening = slotCodes.includes("Evening")
	if (hasMorning && hasEvening) {
		return {
			label: "شیفت: صبح+عصر",
			badgeClass: "bg-violet-100 text-violet-700",
		}
	}
	if (hasMorning) {
		return {
			label: "شیفت: صبح",
			badgeClass: "bg-sky-100 text-sky-700",
		}
	}
	if (hasEvening) {
		return {
			label: "شیفت: عصر",
			badgeClass: "bg-rose-100 text-rose-700",
		}
	}
	return {
		label: "شیفت",
		badgeClass: "bg-slate-100 text-slate-700",
	}
}

function getShiftTypeForDateAndSlot(date, slotCode) {
	const rows = monthShiftSummary.value[date] || []
	const match = rows.find((row) => inferShiftSlotCode(row) === slotCode)
	return String(match?.shift_type || "")
}

function getSelectedDateShiftRequestOptions() {
	const date = localSelectedDate.value
	if (!date) return []
	const slotCodes = getDayShiftSlotCodes(date)
	return slotCodes.map((slotCode) => ({
		code: slotCode,
		label: slotCode === "Morning" ? "صبح" : slotCode === "Evening" ? "عصر" : "شیفت",
		shiftType: getShiftTypeForDateAndSlot(date, slotCode),
	}))
}

function buildShiftRequestRouteForSlot(slotOption) {
	const date = localSelectedDate.value
	return {
		name: "ShiftRequestFormView",
		query: {
			from_date: date,
			to_date: date,
			slot_code: slotOption.code,
			shift_type: slotOption.shiftType || "",
		},
	}
}

function formatEventTiming(eventRow) {
	if (Number(eventRow?.all_day) === 1 || eventRow?.all_day === true) {
		return "تمام‌روز"
	}
	const start = String(eventRow?.starts_on || "").slice(11, 16)
	const end = String(eventRow?.ends_on || "").slice(11, 16)
	if (!(start && end)) return "-"
	return `${toPersianDigits(start)} - ${toPersianDigits(end)}`
}

function getWorkingHours(checkinSummary) {
	const firstIn = checkinSummary.firstIn
	const lastOut = checkinSummary.lastOut
	if (!(firstIn && lastOut)) return 0
	const firstDate = new Date(String(firstIn).replace(" ", "T"))
	const lastDate = new Date(String(lastOut).replace(" ", "T"))
	const durationHours = (lastDate.getTime() - firstDate.getTime()) / (1000 * 60 * 60)
	return durationHours > 0 ? durationHours : 0
}

function formatWorkedHoursLabel(hours) {
	if (!hours || hours <= 0) return "۰ ساعت"
	const rounded = Math.round(hours * 10) / 10
	const [wholeText, fractionText] = String(rounded).split(".")
	if (fractionText && Number(fractionText) > 0) {
		const minutes = Math.round((Number(fractionText) / 10) * 60)
		if (minutes > 0) {
			return `${toPersianDigits(String(Number(wholeText || 0)))} ساعت و ${toPersianDigits(String(minutes))} دقیقه`
		}
	}
	return `${toPersianDigits(String(Number(wholeText || 0)))} ساعت`
}

function getDayAttendanceMeta(date) {
	if (!date) return null
	const leaveState = leaveDateStates.value[date]
	const status = calendarEvents.data?.[date]
	const checkinSummary = monthCheckinSummary.value[date]

	if (leaveState === "approved" || status === "On Leave") {
		return { state: "leave", label: "مرخصی" }
	}

	if (status === "Holiday") {
		return { state: "holiday", label: "تعطیل" }
	}

	if (status === "Half Day" || status === "Present" || status === "Work From Home") {
		return { state: "present", label: "حضور" }
	}

	if (!checkinSummary || !checkinSummary.total) {
		if (hasScheduledShift(date) && date >= todayDateString) {
			return { state: "present", label: "شیفت تاییدشده" }
		}
		if (status === "Absent" && date <= todayDateString) {
			return { state: "absent", label: "غیبت" }
		}
		return null
	}

	const inCount = checkinSummary.IN || 0
	const outCount = checkinSummary.OUT || 0
	const hasIn = inCount > 0
	const hasOut = outCount > 0

	if (hasIn && hasOut && inCount === outCount) {
		return {
			state: "present",
			label: `${formatWorkedHoursLabel(getWorkingHours(checkinSummary))} حضور`,
		}
	}

	return {
		state: "warning",
		label: `هشدار تردد: ورود ${toPersianDigits(String(inCount))} | خروج ${toPersianDigits(String(outCount))}`,
	}
}

function getDayAttendanceState(date) {
	return getDayAttendanceMeta(date)?.state || ""
}

function getDayAttendanceLabel(date) {
	return getDayAttendanceMeta(date)?.label || ""
}

function getDayAttendanceCompactLabel(date) {
	const meta = getDayAttendanceMeta(date)
	if (!meta) return ""
	if (meta.state === "present") {
		return String(meta.label).replace(" حضور", "")
	}
	if (meta.state === "warning") {
		return "هشدار"
	}
	return meta.label
}

function getDayAttendanceBadgeClass(date) {
	const state = getDayAttendanceState(date)
	if (state === "present") return "bg-green-100 text-green-700 dark:bg-emerald-900/40 dark:text-emerald-200"
	if (state === "warning") return "bg-yellow-100 text-yellow-700 dark:bg-amber-900/40 dark:text-amber-200"
	if (state === "leave") return "bg-blue-100 text-blue-700 dark:bg-sky-900/40 dark:text-sky-200"
	if (state === "absent") return "bg-red-100 text-red-700 dark:bg-rose-900/40 dark:text-rose-200"
	if (state === "holiday") return "bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200"
	return "bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200"
}

function getDayAttendanceDotClass(date) {
	const state = getDayAttendanceState(date)
	if (state === "present") return "bg-green-500"
	if (state === "warning") return "bg-yellow-500"
	if (state === "leave") return "bg-blue-500"
	if (state === "absent") return "bg-red-500"
	if (state === "holiday") return "bg-gray-500"
	return "bg-gray-500"
}

function getSelectedDateCheckinRange() {
	const summaryByDate = monthCheckinSummary.value[localSelectedDate.value]
	if (!summaryByDate || !summaryByDate.total) return "-"
	const entryTime = summaryByDate.firstIn
		? toPersianDigits(String(summaryByDate.firstIn).slice(11, 16))
		: "--:--"
	const exitTime = summaryByDate.lastOut
		? toPersianDigits(String(summaryByDate.lastOut).slice(11, 16))
		: "--:--"
	return `ورود ${entryTime} | خروج ${exitTime}`
}

function getMissionDates(mission) {
	const hourlyDate = String(mission?.hourly_date || "").slice(0, 10)
	if (hourlyDate) return [hourlyDate]
	const startDate = String(mission?.start_date || "").slice(0, 10)
	const endDate = String(mission?.end_date || mission?.start_date || "").slice(0, 10)
	if (!startDate) return []
	if (!endDate || startDate > endDate) return [startDate]
	return expandDateRange(startDate, endDate)
}

function getMissionDurationMinutes(mission) {
	const fromText = String(mission?.hourly_from_time || "").slice(0, 5)
	const toText = String(mission?.hourly_to_time || "").slice(0, 5)
	const [fromHour, fromMinute] = fromText.split(":").map(Number)
	const [toHour, toMinute] = toText.split(":").map(Number)

	if (
		!Number.isFinite(fromHour)
		|| !Number.isFinite(fromMinute)
		|| !Number.isFinite(toHour)
		|| !Number.isFinite(toMinute)
	) {
		return 0
	}

	let minutes = (toHour * 60 + toMinute) - (fromHour * 60 + fromMinute)
	if (minutes < 0) minutes += 24 * 60
	return minutes > 0 ? minutes : 0
}

function buildMissionSummaryFromRows(rows) {
	if (!rows.length) return null
	let totalMinutes = 0
	let hasDailySpan = false

	for (const mission of rows) {
		const missionMinutes = getMissionDurationMinutes(mission)
		if (missionMinutes > 0) {
			totalMinutes += missionMinutes
		} else {
			hasDailySpan = true
		}
	}

	return { count: rows.length, totalMinutes, hasDailySpan }
}

function getDayMissionSummary(date) {
	if (!date) return null
	if (missionSummaryByDate.value[date]) return missionSummaryByDate.value[date]
	const rows = (Array.isArray(missionsResource.data) ? missionsResource.data : []).filter((mission) =>
		isMissionOnDate(mission, date)
	)
	return buildMissionSummaryFromRows(rows)
}

function formatMissionDuration(minutes) {
	const safeMinutes = Math.max(0, Number(minutes) || 0)
	const hours = Math.floor(safeMinutes / 60)
	const remainder = safeMinutes % 60
	if (hours && remainder) {
		return `${toPersianDigits(String(hours))} ساعت و ${toPersianDigits(String(remainder))} دقیقه`
	}
	if (hours) return `${toPersianDigits(String(hours))} ساعت`
	return `${toPersianDigits(String(remainder))} دقیقه`
}

function getDayMissionLabel(date) {
	const summaryByDate = getDayMissionSummary(date)
	if (!summaryByDate) return ""
	if (summaryByDate.totalMinutes > 0) {
		return `ماموریت ${formatMissionDuration(summaryByDate.totalMinutes)}`
	}
	if (summaryByDate.count > 1) {
		return `${toPersianDigits(String(summaryByDate.count))} ماموریت`
	}
	return "ماموریت روزانه"
}

function getDayRequestBadges(date) {
	const summary = dayRequestSummaryByDate.value[date]
	if (!summary) return []

	const badgeCandidates = [
		{
			key: "shift",
			count: summary.shift,
			label: (count) => `شیفت ${toPersianDigits(String(count))}`,
			className: "bg-rose-100 text-rose-700",
			dotClass: "bg-rose-500",
		},
		{
			key: "attendance",
			count: summary.attendance,
			label: (count) => `حضور ${toPersianDigits(String(count))}`,
			className: "bg-yellow-100 text-yellow-700",
			dotClass: "bg-yellow-500",
		},
		{
			key: "leave",
			count: summary.leave,
			label: (count) => `مرخصی ${toPersianDigits(String(count))}`,
			className: "bg-blue-100 text-blue-700",
			dotClass: "bg-blue-500",
		},
		{
			key: "advance",
			count: summary.advance,
			label: (count) => `مساعده ${toPersianDigits(String(count))}`,
			className: "bg-teal-100 text-teal-700",
			dotClass: "bg-teal-500",
		},
		{
			key: "expense",
			count: summary.expense,
			label: (count) => `هزینه ${toPersianDigits(String(count))}`,
			className: "bg-amber-100 text-amber-700",
			dotClass: "bg-amber-500",
		},
		{
			key: "event",
			count: summary.event,
			label: (count) => `رویداد ${toPersianDigits(String(count))}`,
			className: "bg-gray-100 text-gray-700",
			dotClass: "bg-gray-500",
		},
	]

	const badges = badgeCandidates
		.filter((entry) => entry.count > 0)
		.map((entry) => ({
			key: entry.key,
			label: entry.label(entry.count),
			className: entry.className,
			dotClass: entry.dotClass,
			count: entry.count,
		}))
		.sort((left, right) => right.count - left.count)

	if (badges.length <= 2) return badges

	const visible = badges.slice(0, 2)
	const extraCount = badges.slice(2).reduce((total, badge) => total + badge.count, 0)
	visible.push({
		key: "more",
		label: `+${toPersianDigits(String(extraCount))} درخواست دیگر`,
		className: "bg-slate-100 text-slate-700",
		dotClass: "bg-slate-500",
		count: extraCount,
	})
	return visible
}

function parseDocstatus(value) {
	if (value === null || value === undefined || value === "") return 0
	return Number(value)
}

function getLeaveState(leave) {
	const status = String(leave.status || leave.workflow_state || "").trim().toLowerCase()
	const docstatus = parseDocstatus(leave.docstatus)
	if (status === "approved" || docstatus === 1) return "approved"
	if (["rejected", "cancelled"].includes(status) || docstatus === 2) return null
	return "pending"
}

function isApprovedLeaveDate(date) {
	return leaveDateStates.value[date] === "approved"
}

function expandDateRange(fromDate, toDate) {
	const dates = []
	let currentDate = fromDate
	while (currentDate <= toDate) {
		dates.push(currentDate)
		const dateObj = new Date(`${currentDate}T12:00:00`)
		dateObj.setDate(dateObj.getDate() + 1)
		currentDate = formatGregorianDate(dateObj)
	}
	return dates
}

function isMissionOnDate(mission, date) {
	const hourlyDate = String(mission?.hourly_date || "").slice(0, 10)
	if (hourlyDate) return hourlyDate === date
	const startDate = String(mission?.start_date || "").slice(0, 10)
	const endDate = String(mission?.end_date || mission?.start_date || "").slice(0, 10)
	if (!(startDate && endDate)) return false
	return startDate <= date && endDate >= date
}

function formatAmount(value, currency) {
	const amount = Number(value || 0)
	const amountText = toPersianDigits(new Intl.NumberFormat("en-US").format(Math.round(amount)))
	return `${amountText} ${currency || ""}`.trim()
}

const DAYS = ["ش", "ی", "د", "س", "چ", "پ", "ج"]

const dailyCheckins = createListResource({
	doctype: "Employee Checkin",
	fields: ["name", "log_type", "time"],
	filters: {},
	orderBy: "time asc",
	auto: false,
})

const monthCheckins = createListResource({
	doctype: "Employee Checkin",
	fields: ["name", "log_type", "time"],
	filters: {},
	orderBy: "time asc",
	auto: false,
})

const monthLeaveApplications = createListResource({
	doctype: "Leave Application",
	fields: ["name", "leave_type", "from_date", "to_date", "status", "workflow_state", "docstatus"],
	filters: {},
	orderBy: "from_date asc",
	auto: false,
})

const dailyAttendanceRequests = createListResource({
	doctype: "Attendance Request",
	fields: [
		"name",
		"status",
		"workflow_state",
		"from_date",
		"to_date",
		"request_mode",
		"requested_log_type",
		"requested_time",
	],
	filters: {},
	orderBy: "modified desc",
	auto: false,
})

const dailyShiftRequests = createListResource({
	doctype: "Shift Request",
	fields: ["name", "status", "workflow_state", "from_date", "to_date", "shift_type"],
	filters: {},
	orderBy: "modified desc",
	auto: false,
})

const dailyExpenseClaims = createListResource({
	doctype: "Expense Claim",
	fields: ["name", "status", "approval_status", "posting_date", "total_claimed_amount", "currency"],
	filters: {},
	orderBy: "modified desc",
	auto: false,
})

const monthAttendanceRequests = createListResource({
	doctype: "Attendance Request",
	fields: ["name", "from_date", "to_date", "docstatus"],
	filters: {},
	orderBy: "modified desc",
	auto: false,
})

const monthShiftRequests = createListResource({
	doctype: "Shift Request",
	fields: ["name", "from_date", "to_date", "docstatus"],
	filters: {},
	orderBy: "modified desc",
	auto: false,
})

const monthExpenseClaims = createListResource({
	doctype: "Expense Claim",
	fields: ["name", "posting_date", "docstatus"],
	filters: {},
	orderBy: "posting_date desc",
	auto: false,
})

const monthAdvances = createListResource({
	doctype: "Employee Advance",
	fields: ["name", "posting_date", "docstatus"],
	filters: {},
	orderBy: "posting_date desc",
	auto: false,
})

const monthEvents = createListResource({
	doctype: "Event",
	fields: ["name", "starts_on", "ends_on", "docstatus"],
	filters: {},
	orderBy: "starts_on desc",
	auto: false,
})

const dailyAdvances = createListResource({
	doctype: "Employee Advance",
	fields: ["name", "status", "posting_date", "advance_amount", "currency", "purpose"],
	filters: {},
	orderBy: "modified desc",
	auto: false,
})

const dailyEvents = createListResource({
	doctype: "Event",
	fields: ["name", "subject", "starts_on", "ends_on", "all_day", "event_type"],
	filters: {},
	orderBy: "starts_on asc",
	auto: false,
})

const shiftsResource = createResource({
	url: "hrms.api.get_shifts",
	auto: false,
})

const finalizedShiftSlotsResource = createResource({
	url: "hrms.api.get_employee_finalized_shift_slots",
	auto: false,
})

const missionsResource = createResource({
	url: "hrms.api.travel.get_travel_requests",
	auto: false,
})

const mealContextResource = createResource({
	url: "hrms.api.meal.get_meal_plan_context",
	auto: false,
})

const saveMealReservationResource = createResource({
	url: "hrms.api.meal.save_my_meal_reservations",
	auto: false,
})

const quickAttendanceRequestResource = createResource({
	url: "frappe.client.insert",
	auto: false,
})

const calendarEvents = createResource({
	url: "hrms.api.get_attendance_calendar_events",
	auto: true,
	cache: "hrms:attendance_calendar_events",
	makeParams() {
		const range = getMonthDateRange()
		return {
			employee: employee.data.name,
			from_date: range.fromDate,
			to_date: range.toDate,
		}
	},
})

function getMonthDateRange() {
	const visibleDays = monthGridDays.value || []
	if (visibleDays.length) {
		return {
			fromDate: visibleDays[0].gregorianDate,
			toDate: visibleDays[visibleDays.length - 1].gregorianDate,
		}
	}

	const year = activeJalaliMonth.value.year
	const month = activeJalaliMonth.value.month
	const firstGregorian = jalaliToGregorian(year, month, 1)
	const lastGregorian = jalaliToGregorian(year, month, getJalaliDaysInMonth(year, month))
	return {
		fromDate: formatGregorianDate(
			new Date(firstGregorian.year, firstGregorian.month - 1, firstGregorian.day)
		),
		toDate: formatGregorianDate(
			new Date(lastGregorian.year, lastGregorian.month - 1, lastGregorian.day)
		),
	}
}

function loadDailyCheckins(date) {
	if (!employee.data?.name) return
	dailyCheckins.filters.employee = employee.data.name
	dailyCheckins.filters.time = ["between", [`${date} 00:00:00`, `${date} 23:59:59`]]
	dailyCheckins.reload()
}

function loadMonthCheckins() {
	if (!employee.data?.name) return
	const range = getMonthDateRange()
	monthCheckins.filters.employee = employee.data.name
	monthCheckins.filters.time = ["between", [`${range.fromDate} 00:00:00`, `${range.toDate} 23:59:59`]]
	monthCheckins.reload()
}

function loadMonthLeaveApplications() {
	if (!employee.data?.name) return
	const range = getMonthDateRange()
	monthLeaveApplications.filters.employee = employee.data.name
	monthLeaveApplications.filters.from_date = ["<=", range.toDate]
	monthLeaveApplications.filters.to_date = [">=", range.fromDate]
	monthLeaveApplications.filters.docstatus = ["!=", 2]
	monthLeaveApplications.reload()
}

async function loadShifts() {
	if (!props.showShiftItems || !employee.data?.name) return
	await shiftsResource.fetch({
		employee: employee.data.name,
	})
}

async function loadFinalizedShiftSlots() {
	if (!props.showShiftItems || !employee.data?.name) return
	const range = getMonthDateRange()
	await finalizedShiftSlotsResource.fetch({
		employee: employee.data.name,
		from_date: range.fromDate,
		to_date: range.toDate,
	})
}

async function loadMissions() {
	await missionsResource.fetch({
		limit: 200,
		for_approval: 0,
	})
}

function loadDailyAttendanceRequests(date) {
	if (!employee.data?.name) return
	dailyAttendanceRequests.filters.employee = employee.data.name
	dailyAttendanceRequests.filters.from_date = ["<=", date]
	dailyAttendanceRequests.filters.to_date = [">=", date]
	dailyAttendanceRequests.filters.docstatus = ["!=", 2]
	dailyAttendanceRequests.reload()
}

function loadDailyShiftRequests(date) {
	if (!employee.data?.name) return
	dailyShiftRequests.filters.employee = employee.data.name
	dailyShiftRequests.filters.from_date = ["<=", date]
	dailyShiftRequests.filters.to_date = [">=", date]
	dailyShiftRequests.filters.docstatus = ["!=", 2]
	dailyShiftRequests.reload()
}

function loadDailyExpenseClaims(date) {
	if (!employee.data?.name) return
	dailyExpenseClaims.filters.employee = employee.data.name
	dailyExpenseClaims.filters.posting_date = date
	dailyExpenseClaims.filters.docstatus = ["!=", 2]
	dailyExpenseClaims.reload()
}

function loadDailyAdvances(date) {
	if (!employee.data?.name) return
	dailyAdvances.filters.employee = employee.data.name
	dailyAdvances.filters.posting_date = date
	dailyAdvances.filters.docstatus = ["!=", 2]
	dailyAdvances.reload()
}

function loadDailyEvents(date) {
	if (!user.data?.name) return
	dailyEvents.filters.owner = user.data.name
	dailyEvents.filters.starts_on = ["<=", `${date} 23:59:59`]
	dailyEvents.filters.ends_on = [">=", `${date} 00:00:00`]
	dailyEvents.filters.docstatus = ["!=", 2]
	dailyEvents.reload()
}

function loadMonthAttendanceRequests() {
	if (!employee.data?.name) return
	const range = getMonthDateRange()
	monthAttendanceRequests.filters.employee = employee.data.name
	monthAttendanceRequests.filters.from_date = ["<=", range.toDate]
	monthAttendanceRequests.filters.to_date = [">=", range.fromDate]
	monthAttendanceRequests.filters.docstatus = ["!=", 2]
	monthAttendanceRequests.reload()
}

function loadMonthShiftRequests() {
	if (!employee.data?.name) return
	const range = getMonthDateRange()
	monthShiftRequests.filters.employee = employee.data.name
	monthShiftRequests.filters.from_date = ["<=", range.toDate]
	monthShiftRequests.filters.to_date = [">=", range.fromDate]
	monthShiftRequests.filters.docstatus = ["!=", 2]
	monthShiftRequests.reload()
}

function loadMonthExpenseClaims() {
	if (!employee.data?.name) return
	const range = getMonthDateRange()
	monthExpenseClaims.filters.employee = employee.data.name
	monthExpenseClaims.filters.posting_date = ["between", [range.fromDate, range.toDate]]
	monthExpenseClaims.filters.docstatus = ["!=", 2]
	monthExpenseClaims.reload()
}

function loadMonthAdvances() {
	if (!employee.data?.name) return
	const range = getMonthDateRange()
	monthAdvances.filters.employee = employee.data.name
	monthAdvances.filters.posting_date = ["between", [range.fromDate, range.toDate]]
	monthAdvances.filters.docstatus = ["!=", 2]
	monthAdvances.reload()
}

function loadMonthEvents() {
	if (!user.data?.name) return
	const range = getMonthDateRange()
	monthEvents.filters.owner = user.data.name
	monthEvents.filters.starts_on = ["<=", `${range.toDate} 23:59:59`]
	monthEvents.filters.ends_on = [">=", `${range.fromDate} 00:00:00`]
	monthEvents.filters.docstatus = ["!=", 2]
	monthEvents.reload()
}

function loadMonthRequestSnapshots() {
	loadMonthAttendanceRequests()
	loadMonthShiftRequests()
	loadMonthExpenseClaims()
	loadMonthAdvances()
	loadMonthEvents()
}

function loadDailyAgenda(date) {
	loadDailyCheckins(date)
	loadDailyAttendanceRequests(date)
	loadDailyShiftRequests(date)
	loadDailyExpenseClaims(date)
	loadDailyAdvances(date)
	loadDailyEvents(date)
}

watch(
	() => `${activeJalaliMonth.value.year}-${activeJalaliMonth.value.month}`,
	() => {
		calendarEvents.fetch()
		loadMonthCheckins()
		loadMonthLeaveApplications()
		loadMonthRequestSnapshots()
		if (props.showShiftItems) {
			loadShifts()
			loadFinalizedShiftSlots()
		}
		loadMissions()
	},
	{ immediate: true }
)

watch(
	() => [employee.data?.name, user.data?.name],
	([employeeName, userName]) => {
		if (!(employeeName && userName)) return
		calendarEvents.fetch()
		loadMonthCheckins()
		loadMonthLeaveApplications()
		loadMonthRequestSnapshots()
		loadShifts()
		loadFinalizedShiftSlots()
		loadMissions()
		loadDailyAgenda(localSelectedDate.value)
		loadMealContext(localSelectedDate.value)
	},
	{ immediate: true }
)

watch(
	() => props.selectedDate,
	(value) => {
		if (!value) return
		localSelectedDate.value = value
	}
)

watch(
	() => localSelectedDate.value,
	(value) => {
		if (!value) return
		closeShiftDetail()
		loadDailyAgenda(value)
		loadMealContext(value)
		emit("dateSelected", value)
	},
	{ immediate: true }
)
</script>

<style scoped>
.month-grid-cell {
	height: clamp(5.8rem, 8vw, 6.6rem);
	overflow: hidden;
}

.shift-detail-sheet {
	--height: min(90vh, 760px);
	--max-height: calc(100vh - env(safe-area-inset-top) - 8px);
	--border-radius: 16px 16px 0 0;
}

.calendar-fab-wrap {
	position: fixed;
	left: max(1rem, env(safe-area-inset-left));
	bottom: max(5rem, env(safe-area-inset-bottom));
	z-index: 2147483000;
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	gap: 0.6rem;
	transform: translate3d(0, 0, 0);
	will-change: transform;
}

.calendar-fab-menu {
	min-width: 12rem;
}

.calendar-fab-menu-item {
	display: block;
	width: 100%;
	text-align: right;
	font-size: 0.8rem;
	font-weight: 600;
	padding: 0.5rem 0.6rem;
	border-radius: 0.55rem;
	color: #374151;
}

.calendar-fab-menu-item:hover {
	background: #f3f4f6;
}

.calendar-fab-button {
	width: 3.25rem;
	height: 3.25rem;
	border-radius: 9999px;
	background: linear-gradient(135deg, var(--ion-color-primary, #0f766e) 0%, var(--ion-color-primary-tint, #14b8a6) 100%);
	color: #ffffff;
	font-size: 1.6rem;
	line-height: 1;
	box-shadow: 0 14px 28px -15px rgba(var(--ion-color-primary-rgb, 15, 118, 110), 0.8);
	transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.calendar-fab-button:hover {
	transform: translateY(-1px) scale(1.02);
	box-shadow: 0 18px 30px -16px rgba(var(--ion-color-primary-rgb, 15, 118, 110), 0.85);
}

.calendar-fab-button-open {
	transform: rotate(45deg);
}

.calendar-fab-pop-enter-active,
.calendar-fab-pop-leave-active {
	transition: all 0.2s ease;
}

.calendar-fab-pop-enter-from,
.calendar-fab-pop-leave-to {
	opacity: 0;
	transform: translateY(6px) scale(0.96);
}

@media (max-width: 768px) {
	.month-grid-cell {
		height: 6.2rem;
	}
}
</style>
