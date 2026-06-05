<template>
	<BaseLayout :pageTitle="__('Appraisal History')">
		<template #body>
			<div class="flex flex-col items-center mt-7 mb-7 py-4 px-4 w-full gap-4">
				<router-link
					v-if="isHrUser"
					:to="{ name: 'AppraisalFormView' }"
					v-slot="{ navigate }"
					class="w-full"
				>
					<Button @click="navigate" variant="solid" class="py-5 text-base w-full">
						{{ __("Create Appraisal") }}
					</Button>
				</router-link>

				<TabButtons :buttons="tabButtons" v-model="activeTab" class="w-full" />

				<div class="w-full flex gap-2">
					<select
						v-model="selectedStatus"
						class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 w-1/2"
					>
						<option value="">{{ __("All Statuses") }}</option>
						<option value="Draft">{{ __("Draft") }}</option>
						<option value="Submitted">{{ __("Submitted") }}</option>
						<option value="Cancelled">{{ __("Cancelled") }}</option>
					</select>
					<select
						v-model="selectedCycle"
						class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 w-1/2"
					>
						<option value="">{{ __("All Cycles") }}</option>
						<option v-for="cycle in cycleOptions" :key="cycle" :value="cycle">
							{{ cycle }}
						</option>
					</select>
				</div>

				<div class="w-full" v-if="filteredItems.length">
					<div class="flex flex-col bg-white rounded overflow-hidden">
						<router-link
							v-for="appraisal in visibleItems"
							:key="appraisal.name"
							:to="{
								name: 'AppraisalDetailView',
								params: { id: appraisal.name },
								query: { mode: activeTab === 'Team Appraisals' ? 'team' : 'self' },
							}"
							class="p-3.5 border-b last:border-b-0"
						>
							<AppraisalItem :doc="appraisal" :isTeamRequest="activeTab === 'Team Appraisals'" />
						</router-link>
					</div>

					<div v-if="hasMore" class="p-3 flex justify-center">
						<Button variant="outline" @click="loadMore">
							{{ __("Load More +") }}
						</Button>
					</div>
				</div>
				<EmptyState v-else :message="__('No appraisals found')" />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import TabButtons from "@/components/TabButtons.vue"
import AppraisalItem from "@/components/AppraisalItem.vue"

import { myAppraisals, teamAppraisals } from "@/data/appraisals"

const __ = inject("$translate")
const user = inject("$user")

const activeTab = ref("My Appraisals")
const selectedStatus = ref("")
const selectedCycle = ref("")
const visibleCount = ref(10)

const isHrUser = computed(() => {
	const roles = user.data?.roles || []
	return (
		roles.includes("HR Manager") || roles.includes("HR User") || roles.includes("System Manager")
	)
})

const tabButtons = computed(() =>
	isHrUser.value ? ["My Appraisals", "Team Appraisals"] : ["My Appraisals"]
)

const activeItems = computed(() => {
	if (activeTab.value === "Team Appraisals" && isHrUser.value) {
		return teamAppraisals.data || []
	}
	return myAppraisals.data || []
})

const cycleOptions = computed(() => {
	return [...new Set(activeItems.value.map((row) => row.appraisal_cycle).filter(Boolean))]
})

const filteredItems = computed(() => {
	return activeItems.value.filter((item) => {
		if (selectedStatus.value && item.status !== selectedStatus.value) return false
		if (selectedCycle.value && item.appraisal_cycle !== selectedCycle.value) return false
		return true
	})
})

const visibleItems = computed(() => filteredItems.value.slice(0, visibleCount.value))
const hasMore = computed(() => filteredItems.value.length > visibleCount.value)

function loadMore() {
	visibleCount.value += 10
}

watch([activeTab, selectedStatus, selectedCycle], () => {
	visibleCount.value = 10
})
</script>
