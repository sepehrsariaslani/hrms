<template>
	<BaseLayout :pageTitle="pageTitle">
		<template #body>
			<div class="flex flex-col items-center mt-7 mb-7 p-4 w-full max-w-7xl mx-auto gap-4">
				<div class="w-full rounded-xl border border-slate-200 bg-white p-3 md:p-4">
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-2">
							<Button variant="ghost" class="!px-1" @click="router.back()">
								<FeatherIcon name="chevron-left" class="h-5 w-5" />
							</Button>
							<h2 class="text-xl font-semibold text-gray-900">
								{{ props.id ? __("Appraisal Detail") : __("Create Appraisal") }}
							</h2>
						</div>
						<Badge
							v-if="props.id && detailResource.data"
							:label="__(detailResource.data.status)"
							:theme="statusTheme"
							variant="outline"
						/>
					</div>
				</div>

				<div v-if="isLoading" class="mt-6">
					<LoadingIndicator class="w-8 h-8 text-gray-700" />
				</div>

				<div v-else-if="!props.id" class="w-full bg-white rounded-lg border p-4 space-y-4">
					<FormField
						fieldtype="Link"
						fieldname="employee"
						:label="__('Employee')"
						options="Employee"
						:reqd="1"
						v-model="createForm.employee"
					/>
					<FormField
						fieldtype="Link"
						fieldname="appraisal_cycle"
						:label="__('Appraisal Cycle')"
						options="Appraisal Cycle"
						:readOnly="1"
						v-model="createForm.appraisal_cycle"
					/>
					<FormField
						fieldtype="Link"
						fieldname="appraisal_template"
						:label="__('Appraisal Template')"
						options="Appraisal Template"
						:readOnly="1"
						v-model="createForm.appraisal_template"
					/>
					<div class="text-xs text-gray-500">
						{{
							__(
								"Appraisal cycle and template are selected automatically based on employee role and company."
							)
						}}
					</div>
					<Button
						class="w-full py-5"
						:loading="createAppraisal.loading || appraisalDefaults.loading"
						@click="handleCreateAppraisal"
					>
						{{ __("Create Appraisal") }}
					</Button>
				</div>

				<div v-else-if="detailResource.data" class="w-full space-y-4">
					<div class="bg-white rounded-lg border p-4">
						<div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
							<div>
								<span class="text-gray-500">{{ __("Employee") }}:</span>
								<span class="text-gray-900">{{ detailResource.data.employee_name }}</span>
							</div>
							<div>
								<span class="text-gray-500">{{ __("Designation") }}:</span>
								<span class="text-gray-900">{{ detailResource.data.designation || "-" }}</span>
							</div>
							<div>
								<span class="text-gray-500">{{ __("Appraisal Cycle") }}:</span>
								<span class="text-gray-900">{{ detailResource.data.appraisal_cycle }}</span>
							</div>
							<div>
								<span class="text-gray-500">{{ __("Appraisal Template") }}:</span>
								<span class="text-gray-900">{{
									detailResource.data.appraisal_template || "-"
								}}</span>
							</div>
							<div>
								<span class="text-gray-500">{{ __("Final Score") }}:</span>
								<span class="text-gray-900">{{
									formatScore(detailResource.data.final_score)
								}}</span>
							</div>
							<div>
								<span class="text-gray-500">{{ __("Self Score") }}:</span>
								<span class="text-gray-900">{{
									formatScore(detailResource.data.self_score)
								}}</span>
							</div>
							<div>
								<span class="text-gray-500">{{ __("Review Mode") }}:</span>
								<span class="text-gray-900">{{ __(reviewModeLabel) }}</span>
							</div>
						</div>
					</div>

					<div v-if="showSelfSection" class="bg-white rounded-lg border p-4 space-y-3">
						<div class="text-base font-semibold text-gray-900">{{ __(selfSectionTitle) }}</div>
						<div class="overflow-auto">
							<table class="w-full text-sm">
								<thead>
									<tr class="text-gray-500 border-b">
										<th class="text-right py-2">{{ __("Criteria") }}</th>
										<th class="text-right py-2">{{ __("Weightage (%)") }}</th>
										<th class="text-right py-2">{{ __("Rating (1-5)") }}</th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="row in selfRatings" :key="row.name" class="border-b last:border-b-0">
										<td class="py-2">{{ row.criteria }}</td>
										<td class="py-2">{{ row.per_weightage }}</td>
										<td class="py-2 w-36">
											<select
												v-model.number="row.ui_rating"
												class="w-full rounded-md border border-gray-200 px-2 py-1"
												:disabled="!canSelfEdit || reviewMode === 'team'"
											>
												<option v-for="score in [0, 1, 2, 3, 4, 5]" :key="score" :value="score">
													{{ score }}
												</option>
											</select>
										</td>
									</tr>
								</tbody>
							</table>
						</div>
						<FormField
							fieldtype="Text"
							fieldname="reflections"
							:label="__('Reflections')"
							v-model="selfReflections"
							:readOnly="!canSelfEdit || reviewMode === 'team'"
						/>
						<Button
							v-if="showSelfSaveButton"
							class="w-full py-5"
							:loading="saveSelfAppraisal.loading"
							@click="handleSaveSelfAppraisal"
						>
							{{ __("Save Self Appraisal") }}
						</Button>
					</div>

					<div
						class="bg-white rounded-lg border p-4 space-y-3"
						v-if="detailResource.data.appraisal_kra?.length"
					>
						<div class="text-base font-semibold text-gray-900">{{ __("KRA Summary") }}</div>
						<div class="overflow-auto">
							<table class="w-full text-sm">
								<thead>
									<tr class="text-gray-500 border-b">
										<th class="text-right py-2">{{ __("KRA") }}</th>
										<th class="text-right py-2">{{ __("Weightage (%)") }}</th>
										<th class="text-right py-2">{{ __("Goal Completion (%)") }}</th>
										<th class="text-right py-2">{{ __("Goal Score") }}</th>
									</tr>
								</thead>
								<tbody>
									<tr
										v-for="row in detailResource.data.appraisal_kra"
										:key="row.name"
										class="border-b last:border-b-0"
									>
										<td class="py-2">{{ row.kra }}</td>
										<td class="py-2">{{ row.per_weightage }}</td>
										<td class="py-2">{{ row.goal_completion }}</td>
										<td class="py-2">{{ formatScore(row.goal_score) }}</td>
									</tr>
								</tbody>
							</table>
						</div>
					</div>

					<div class="bg-white rounded-lg border p-4 space-y-3" v-if="showTeamSection">
						<div class="text-base font-semibold text-gray-900">{{ __("Team Review") }}</div>
						<div
							v-if="detailResource.data.rate_goals_manually && managerGoals.length"
							class="overflow-auto"
						>
							<table class="w-full text-sm">
								<thead>
									<tr class="text-gray-500 border-b">
										<th class="text-right py-2">{{ __("Goal") }}</th>
										<th class="text-right py-2">{{ __("Weightage (%)") }}</th>
										<th class="text-right py-2">{{ __("Score (0-5)") }}</th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="row in managerGoals" :key="row.name" class="border-b last:border-b-0">
										<td class="py-2">{{ row.kra }}</td>
										<td class="py-2">{{ row.per_weightage }}</td>
										<td class="py-2 w-36">
											<input
												type="number"
												v-model.number="row.score"
												min="0"
												max="5"
												step="0.1"
												class="w-full rounded-md border border-gray-200 px-2 py-1"
											/>
										</td>
									</tr>
								</tbody>
							</table>
						</div>
						<FormField
							fieldtype="Text"
							fieldname="remarks"
							:label="__('Remarks')"
							v-model="managerRemarks"
						/>
						<div class="grid grid-cols-1 md:grid-cols-2 gap-2">
							<Button
								class="py-5"
								:loading="saveTeamAppraisal.loading"
								@click="handleSaveTeamAppraisal"
							>
								{{ __("Save Team Review") }}
							</Button>
							<Button
								variant="outline"
								class="py-5"
								:loading="submitAppraisal.loading"
								@click="handleSubmitAppraisal"
							>
								{{ __("Submit Appraisal") }}
							</Button>
						</div>
					</div>

					<div class="bg-white rounded-lg border p-4 space-y-3" v-if="showTeamSection">
						<div class="text-base font-semibold text-gray-900">{{ __("Add Feedback") }}</div>
						<FormField
							fieldtype="Text"
							fieldname="feedback"
							:label="__('Feedback')"
							v-model="feedbackText"
						/>
						<div class="overflow-auto">
							<table class="w-full text-sm">
								<thead>
									<tr class="text-gray-500 border-b">
										<th class="text-right py-2">{{ __("Criteria") }}</th>
										<th class="text-right py-2">{{ __("Rating (1-5)") }}</th>
									</tr>
								</thead>
								<tbody>
									<tr
										v-for="row in feedbackRatings"
										:key="row.criteria"
										class="border-b last:border-b-0"
									>
										<td class="py-2">{{ row.criteria }}</td>
										<td class="py-2 w-36">
											<select
												v-model.number="row.ui_rating"
												class="w-full rounded-md border border-gray-200 px-2 py-1"
											>
												<option v-for="score in [0, 1, 2, 3, 4, 5]" :key="score" :value="score">
													{{ score }}
												</option>
											</select>
										</td>
									</tr>
								</tbody>
							</table>
						</div>
						<Button class="w-full py-5" :loading="saveFeedback.loading" @click="handleAddFeedback">
							{{ __("Submit Feedback") }}
						</Button>
					</div>
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, ref, inject, watch } from "vue"
import { useRouter } from "vue-router"
import { createResource, FeatherIcon, Badge, toast, LoadingIndicator } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import FormField from "@/components/FormField.vue"

const router = useRouter()
const __ = inject("$translate")

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})
const pageTitle = computed(() =>
	props.id ? __("Appraisal Detail") : __("Create Appraisal")
)

const createForm = ref({
	employee: "",
	appraisal_cycle: "",
	appraisal_template: "",
})

const selfRatings = ref([])
const selfReflections = ref("")
const managerGoals = ref([])
const managerRemarks = ref("")
const feedbackText = ref("")
const feedbackRatings = ref([])

const detailResource = createResource({
	url: "hrms.api.get_appraisal_detail",
	params: {
		name: props.id,
	},
	auto: Boolean(props.id),
	onSuccess(data) {
		hydrateState(data)
	},
})

const appraisalDefaults = createResource({
	url: "hrms.api.get_appraisal_defaults",
	auto: false,
	onSuccess(data) {
		createForm.value.appraisal_cycle = data?.appraisal_cycle || ""
		createForm.value.appraisal_template = data?.appraisal_template || ""
	},
	onError(error) {
		createForm.value.appraisal_cycle = ""
		createForm.value.appraisal_template = ""
		toast({
			title: __("Error"),
			text: __(error?.messages?.[0] || error?.message || "Failed to detect appraisal defaults."),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
	},
})

const createAppraisal = createResource({
	url: "hrms.api.create_appraisal",
	onSuccess(data) {
		toast({
			title: __("Success"),
			text: __("Appraisal created successfully."),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
		router.replace({ name: "AppraisalDetailView", params: { id: data.name } })
	},
})

const saveSelfAppraisal = createResource({
	url: "hrms.api.upsert_self_appraisal",
	onSuccess() {
		toast({
			title: __("Success"),
			text: __("Self appraisal saved successfully."),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
		detailResource.reload()
	},
})

const saveTeamAppraisal = createResource({
	url: "hrms.api.upsert_team_appraisal",
	onSuccess() {
		toast({
			title: __("Success"),
			text: __("Team review saved successfully."),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
		detailResource.reload()
	},
})

const submitAppraisal = createResource({
	url: "hrms.api.submit_appraisal",
	onSuccess() {
		toast({
			title: __("Success"),
			text: __("Appraisal submitted successfully."),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
		detailResource.reload()
	},
})

const saveFeedback = createResource({
	url: "hrms.api.add_appraisal_feedback",
	onSuccess() {
		toast({
			title: __("Success"),
			text: __("Feedback submitted successfully."),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
		feedbackText.value = ""
		feedbackRatings.value = feedbackRatings.value.map((row) => ({ ...row, ui_rating: 0 }))
		detailResource.reload()
	},
})

const isLoading = computed(() => props.id && detailResource.loading)

const isSelfOwner = computed(() => Boolean(detailResource.data?.permissions?.is_self_owner))
const canSelfEdit = computed(() => Boolean(detailResource.data?.permissions?.can_self_edit))
const canTeamEdit = computed(() => Boolean(detailResource.data?.permissions?.can_team_edit))
const reviewMode = computed(() => {
	if (!props.id) return "team"
	return isSelfOwner.value ? "self" : "team"
})
const reviewModeLabel = computed(() =>
	reviewMode.value === "team" ? "Team Review Mode" : "Self Review Mode"
)
const showSelfSection = computed(
	() => Boolean(detailResource.data) && reviewMode.value === "self"
)
const showTeamSection = computed(
	() => Boolean(detailResource.data) && reviewMode.value === "team" && canTeamEdit.value
)
const showSelfSaveButton = computed(
	() => Boolean(detailResource.data) && reviewMode.value === "self" && canSelfEdit.value
)
const selfSectionTitle = computed(() =>
	reviewMode.value === "team" ? "Employee Self Appraisal" : "Self Appraisal"
)

const statusTheme = computed(() => {
	const status = detailResource.data?.status
	if (status === "Submitted") return "green"
	if (status === "Cancelled") return "red"
	return "orange"
})

function formatScore(value) {
	if (value === null || value === undefined || value === "") return "-"
	const parsed = Number(value)
	return Number.isFinite(parsed) ? parsed.toFixed(2) : "-"
}

function toStars(rating) {
	const value = Number(rating)
	if (!Number.isFinite(value)) return 0
	if (value > 1) return Math.max(0, Math.min(5, Math.round(value)))
	return Math.max(0, Math.min(5, Math.round(value * 5)))
}

function normalizeRating(stars) {
	const value = Number(stars)
	if (!Number.isFinite(value)) return 0
	const clamped = Math.max(0, Math.min(5, value))
	return clamped / 5
}

function hydrateState(data) {
	selfRatings.value = (data.self_ratings || []).map((row) => ({
		...row,
		ui_rating: toStars(row.rating),
	}))
	selfReflections.value = data.reflections || ""
	managerGoals.value = (data.goals || []).map((row) => ({ ...row }))
	managerRemarks.value = data.remarks || ""
	feedbackRatings.value = (data.self_ratings || []).map((row) => ({
		criteria: row.criteria,
		per_weightage: row.per_weightage,
		ui_rating: 0,
	}))
}

function handleCreateAppraisal() {
	if (!createForm.value.employee) {
		toast({
			title: __("Error"),
			text: __("Employee is required."),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
		return
	}

	createAppraisal.submit({
		employee: createForm.value.employee,
		appraisal_cycle: createForm.value.appraisal_cycle || null,
		appraisal_template: createForm.value.appraisal_template || null,
	})
}

function handleSaveSelfAppraisal() {
	const payload = {
		name: props.id,
		reflections: selfReflections.value,
		self_ratings: selfRatings.value.map((row) => ({
			name: row.name,
			criteria: row.criteria,
			rating: normalizeRating(row.ui_rating),
		})),
	}

	saveSelfAppraisal.submit({ payload: JSON.stringify(payload) })
}

function handleSaveTeamAppraisal() {
	const payload = {
		name: props.id,
		remarks: managerRemarks.value,
		goals: managerGoals.value.map((row) => ({
			name: row.name,
			kra: row.kra,
			score: row.score,
		})),
	}

	saveTeamAppraisal.submit({ payload: JSON.stringify(payload) })
}

function handleSubmitAppraisal() {
	submitAppraisal.submit({ name: props.id })
}

function handleAddFeedback() {
	const payload = {
		name: props.id,
		feedback: feedbackText.value,
		feedback_ratings: feedbackRatings.value.map((row) => ({
			criteria: row.criteria,
			per_weightage: row.per_weightage,
			rating: normalizeRating(row.ui_rating),
		})),
	}

	saveFeedback.submit({ payload: JSON.stringify(payload) })
}

watch(
	() => createForm.value.employee,
	(employee) => {
		if (!employee) {
			createForm.value.appraisal_cycle = ""
			createForm.value.appraisal_template = ""
			return
		}

		appraisalDefaults.submit({ employee })
	}
)
</script>
