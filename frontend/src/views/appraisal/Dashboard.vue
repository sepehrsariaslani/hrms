<template>
	<BaseLayout :pageTitle="__('Performance Appraisal')">
		<template #body>
			<div class="flex flex-col items-center mt-7 mb-7 py-4 px-4 w-full gap-6">
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

				<div class="grid grid-cols-2 gap-3 w-full">
					<div v-for="card in kpiCards" :key="card.label" class="rounded-lg border bg-white p-3 hr-accent-border">
						<div class="text-xs text-gray-500">{{ __(card.label) }}</div>
						<div class="text-2xl font-semibold text-gray-900">{{ card.value }}</div>
					</div>
				</div>

				<div class="w-full">
					<div class="text-lg text-gray-800 font-bold">{{ __("Recent Appraisals") }}</div>
					<div
						v-if="myAppraisals.data?.length"
						class="flex flex-col bg-white rounded mt-4 overflow-hidden"
					>
						<router-link
							v-for="appraisal in myRecentAppraisals"
							:key="appraisal.name"
							:to="{
								name: 'AppraisalDetailView',
								params: { id: appraisal.name },
								query: { mode: 'self' },
							}"
							class="p-3.5 border-b last:border-b-0"
						>
							<AppraisalItem :doc="appraisal" />
						</router-link>
						<router-link
							:to="{ name: 'AppraisalListView' }"
							class="w-full text-center py-4 text-sm text-gray-600"
						>
							{{ __("View List") }}
						</router-link>
					</div>
					<EmptyState v-else :message="__('No appraisals found')" />
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import AppraisalItem from "@/components/AppraisalItem.vue"

import { myAppraisals, teamAppraisals } from "@/data/appraisals"

const __ = inject("$translate")
const user = inject("$user")

const isHrUser = computed(() => {
	const roles = user.data?.roles || []
	return (
		roles.includes("HR Manager") || roles.includes("HR User") || roles.includes("System Manager")
	)
})

const myRecentAppraisals = computed(() => (myAppraisals.data || []).slice(0, 5))
const myCount = computed(() => (myAppraisals.data || []).length)
const myDraftCount = computed(
	() => (myAppraisals.data || []).filter((row) => row.status === "Draft").length
)
const mySubmittedCount = computed(
	() => (myAppraisals.data || []).filter((row) => row.status === "Submitted").length
)
const myAverageFinalScore = computed(() => {
	const scores = (myAppraisals.data || [])
		.map((row) => Number(row.final_score))
		.filter((score) => Number.isFinite(score))

	if (!scores.length) return "-"
	const avg = scores.reduce((sum, current) => sum + current, 0) / scores.length
	return avg.toFixed(2)
})

const pendingCount = computed(() => {
	if (isHrUser.value) {
		return (teamAppraisals.data || []).filter((row) => row.status === "Draft").length
	}
	return (myAppraisals.data || []).filter((row) => row.status === "Draft").length
})

const kpiCards = computed(() => {
	const cards = [
		{ label: "My Appraisals", value: myCount.value },
		{ label: "My Drafts", value: myDraftCount.value },
		{ label: "Submitted Appraisals", value: mySubmittedCount.value },
		{ label: "Average Final Score", value: myAverageFinalScore.value },
	]

	if (isHrUser.value) {
		cards[1] = { label: "Pending Team Reviews", value: pendingCount.value }
	}

	return cards
})
</script>
