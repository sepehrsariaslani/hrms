<template>
	<BaseLayout :pageTitle="__('Leaves & Holidays')">
		<template #body>
			<div class="flex flex-col items-center mt-7 mb-7 py-4" data-tour="leave-dashboard-root">
				<LeaveBalance data-tour="leave-balance" />

				<div class="flex flex-col gap-7 mt-5 px-4 w-full">
					<div data-tour="leave-request-action">
						<router-link
							:to="{ name: 'LeaveApplicationFormView' }"
							v-slot="{ navigate }"
						>
							<Button
								@click="navigate"
								variant="solid"
								class="py-5 text-base w-full"
							>
								{{ __("Request a Leave") }}
							</Button>
						</router-link>
					</div>
					<div data-tour="leave-recent-list">
						<div class="text-lg text-gray-800 font-bold">{{ __('Recent Leaves') }} </div>
						<RequestList
							:component="markRaw(LeaveRequestItem)"
							:items="myLeaves.data"
							:addListButton="true"
							listButtonRoute="LeaveApplicationListView"
						/>
					</div>
					<Holidays data-tour="leave-holidays" />
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { markRaw } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import LeaveBalance from "@/components/LeaveBalance.vue"
import RequestList from "@/components/RequestList.vue"
import LeaveRequestItem from "@/components/LeaveRequestItem.vue"
import Holidays from "@/components/Holidays.vue"

import { myLeaves } from "@/data/leaves"
</script>
