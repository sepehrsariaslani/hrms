<template>
	<BaseLayout :pageTitle="__('تقویم حضور و غیاب')">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-7">
				<HrPlannerCalendar title="تقویم حضور و غیاب" :showShiftItems="true" />
				<div v-if="isShiftAllocator" class="grid grid-cols-1 gap-2 sm:grid-cols-2">
					<router-link :to="{ name: 'ShiftAllocatorSchedulerView' }" v-slot="{ navigate }">
						<Button @click="navigate" variant="solid" class="w-full py-5 text-base">
							{{ __("تقویم شیفت هفتگی تیم") }}
						</Button>
					</router-link>
					<router-link :to="{ name: 'TeamWeeklyShiftBoardView' }" v-slot="{ navigate }">
						<Button @click="navigate" variant="outline" class="w-full py-5 text-base">
							{{ __("تابلوی هفتگی تیم") }}
						</Button>
					</router-link>
				</div>
				<div>
					<div class="text-lg text-gray-800 font-bold">{{ __("Recent Attendance Requests") }}</div>
					<RequestList
						:component="markRaw(AttendanceRequestItem)"
						:items="myAttendanceRequests?.data?.slice(0, 5)"
						:addListButton="true"
						listButtonRoute="AttendanceRequestListView"
					/>
				</div>
				<div v-if="hasShiftPlanningAccess && !isShiftAllocator" class="w-full">
					<router-link :to="{ name: 'ShiftRequestFormView' }" v-slot="{ navigate }">
						<Button @click="navigate" variant="solid" class="w-full py-5 text-base">
							{{ __("Request a Shift") }}
						</Button>
					</router-link>
				</div>
				<div v-if="hasShiftPlanningAccess && !isShiftAllocator">
					<div class="text-lg text-gray-800 font-bold">{{ __("Recent Shift Requests") }}</div>
					<RequestList
						:component="markRaw(ShiftRequestItem)"
						:items="myShiftRequests?.data?.slice(0, 5)"
						:addListButton="true"
						listButtonRoute="ShiftRequestListView"
					/>
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, markRaw } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import AttendanceRequestItem from "@/components/AttendanceRequestItem.vue"
import ShiftRequestItem from "@/components/ShiftRequestItem.vue"
import RequestList from "@/components/RequestList.vue"
import HrPlannerCalendar from "@/components/HrPlannerCalendar.vue"

import {
	myAttendanceRequests,
	myShiftRequests,
} from "@/data/attendance"

const employee = inject("$employee")

const isShiftAllocator = computed(() => Boolean(employee.data?.is_shift_allocator))
const hasShiftPlanningAccess = computed(() =>
	Boolean(employee.data?.variable_shift || employee.data?.has_rotational_shift || employee.data?.needs_shift_registration)
)

</script>
