<template>
	<BaseLayout :pageTitle="__('Feedback & Suggestions')">
		<template #body>
			<div
				class="flex flex-col items-center mt-7 mb-7 py-4 px-4 w-full gap-7"
				data-tour="complaint-dashboard-root"
			>
				<div class="w-full" data-tour="complaint-submit-action">
					<router-link
						:to="{ name: 'EmployeeGrievanceFormView' }"
						v-slot="{ navigate }"
						class="w-full"
					>
						<Button
							@click="navigate"
							variant="solid"
							class="py-5 text-base w-full"
						>
								{{ __("Submit Feedback") }}
						</Button>
					</router-link>
				</div>

				<div class="w-full" data-tour="complaint-recent-list">
					<div class="text-lg text-gray-800 font-bold" data-tour="complaint-recent-title">
						{{ __("Recent Feedback") }}
					</div>
					<RequestList
						:component="markRaw(ComplaintItem)"
						:items="myComplaints.data"
						:addListButton="true"
						listButtonRoute="EmployeeGrievanceListView"
					/>
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { markRaw } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import RequestList from "@/components/RequestList.vue"
import ComplaintItem from "@/components/ComplaintItem.vue"

import { myComplaints } from "@/data/complaints"
</script>
