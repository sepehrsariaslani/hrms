<template>
	<BaseLayout :pageTitle="__('Newsletter Report')">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-4">
				<div v-if="!canManage" class="bg-white rounded p-4 text-sm text-gray-600">
					{{ __("You are not allowed to view newsletter reports.") }}
				</div>

				<template v-else>
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
						<router-link
							:to="{ name: 'NewsletterEditView', params: { id: props.id } }"
							v-slot="{ navigate }"
						>
							<Button @click="navigate" variant="outline" class="py-5 text-base w-full">
								{{ __("Edit Newsletter") }}
							</Button>
						</router-link>
						<router-link :to="{ name: 'NewslettersDashboard' }" v-slot="{ navigate }">
							<Button @click="navigate" variant="solid" class="py-5 text-base w-full">
								{{ __("Back to Newsletters") }}
							</Button>
						</router-link>
					</div>

					<div v-if="newsletter" class="bg-white rounded p-4">
						<div class="text-base font-semibold text-gray-900">{{ newsletter.title }}</div>
						<div class="text-xs text-gray-500 mt-1">
							{{ __("Status") }}: {{ __(newsletter.status) }}
						</div>
					</div>

					<div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
						<div
							v-for="card in kpiCards"
							:key="card.label"
							class="rounded-lg border bg-white p-3"
						>
							<div class="text-xs text-gray-500">{{ __(card.label) }}</div>
							<div class="text-2xl font-semibold text-gray-900">
								{{ toPersianDigits(card.value) }}
							</div>
						</div>
					</div>

					<div v-if="roleStats.length" class="bg-white rounded p-4">
						<div class="text-sm font-semibold text-gray-900 mb-2">{{ __("Role Breakdown") }}</div>
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
							<div
								v-for="row in roleStats"
								:key="row.role"
								class="rounded border border-gray-200 p-3"
							>
								<div class="text-sm font-semibold text-gray-800">{{ __(row.role) }}</div>
								<div class="text-xs text-gray-600 mt-1">
									{{ __("Recipients") }}: {{ toPersianDigits(row.recipient_count) }}
								</div>
								<div class="text-xs text-gray-600">
									{{ __("Read") }}: {{ toPersianDigits(row.read_count) }}
								</div>
								<div class="text-xs text-gray-600">
									{{ __("Read Rate") }}: {{ toPersianDigits(row.read_rate) }}%
								</div>
							</div>
						</div>
					</div>

					<div class="bg-white rounded p-4">
						<div class="text-sm font-semibold text-gray-900 mb-3">
							{{ __("Employee Read Status") }}
						</div>

						<div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
							<input
								v-model="searchTerm"
								type="text"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
								:placeholder="__('Search employee')"
							/>
							<select
								v-model="statusFilter"
								class="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm w-full"
							>
								<option value="all">{{ __("All Statuses") }}</option>
								<option value="read">{{ __("Read") }}</option>
								<option value="unread">{{ __("Unread") }}</option>
							</select>
						</div>

						<div class="divide-y border border-gray-200 rounded">
							<div
								v-for="recipient in filteredRecipients"
								:key="recipient.employee"
								class="p-3 flex items-center justify-between gap-3"
							>
								<div class="min-w-0">
									<div class="text-sm font-medium text-gray-900 truncate">
										{{ recipient.employee_name }}
									</div>
									<div class="text-xs text-gray-500 mt-1 truncate">
										{{ recipient.designation ? __(recipient.designation) : "-" }}
									</div>
									<div class="text-[11px] text-gray-500 mt-1">
										{{
											recipient.read_on
												? `${__('Read On')}: ${formatJalaliDateTime(recipient.read_on)}`
												: __("Not read yet")
										}}
									</div>
								</div>
								<Badge
									:label="__(recipient.is_read ? 'Read' : 'Unread')"
									variant="outline"
									:theme="recipient.is_read ? 'green' : 'orange'"
									size="sm"
								/>
							</div>
							<div v-if="!filteredRecipients.length" class="p-4 text-sm text-gray-500 text-center">
								{{ __("No recipients found") }}
							</div>
						</div>
					</div>
				</template>

				<ErrorMessage :message="errorMessage" />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue"
import { Badge, createResource, ErrorMessage } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import {
	extractErrorMessage,
	isNewsletterManager,
	normalizeNewsletter,
	normalizeRecipient,
	normalizeRoleStats,
} from "@/data/newsletters"
import { formatJalaliDateTime, toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")
const user = inject("$user")

const props = defineProps({
	id: {
		type: String,
		required: true,
	},
})

const newsletter = ref(null)
const reportStats = ref({
	recipient_count: 0,
	read_count: 0,
	unread_count: 0,
	read_rate: 0,
})
const recipients = ref([])
const roleStats = ref([])
const searchTerm = ref("")
const statusFilter = ref("all")
const errorMessage = ref("")

const canManage = computed(() => isNewsletterManager(user.data))
const kpiCards = computed(() => [
	{ label: "Recipients", value: reportStats.value.recipient_count },
	{ label: "Read", value: reportStats.value.read_count },
	{ label: "Unread", value: reportStats.value.unread_count },
	{ label: "Read Rate", value: `${reportStats.value.read_rate}%` },
])

const filteredRecipients = computed(() => {
	const query = searchTerm.value.trim().toLowerCase()
	return recipients.value.filter((row) => {
		if (statusFilter.value === "read" && !row.is_read) return false
		if (statusFilter.value === "unread" && row.is_read) return false
		if (!query) return true

		return (
			String(row.employee_name || "").toLowerCase().includes(query) ||
			String(row.employee || "").toLowerCase().includes(query) ||
			String(row.designation || "").toLowerCase().includes(query)
		)
	})
})

const reportResource = createResource({
	url: "hrms.api.newsletter.get_newsletter_report",
	auto: false,
})

watch(
	canManage,
	(allowed) => {
		if (allowed) loadReport()
	},
	{ immediate: true }
)

function loadReport() {
	reportResource.fetch(
		{
			newsletter_name: props.id,
		},
		{
			onSuccess(data) {
				errorMessage.value = ""
				newsletter.value = normalizeNewsletter(data?.newsletter || {})
				reportStats.value = {
					recipient_count: Number(data?.stats?.recipient_count || data?.stats?.total_recipients || 0),
					read_count: Number(data?.stats?.read_count || data?.stats?.total_reads || 0),
					unread_count: Number(data?.stats?.unread_count || 0),
					read_rate: Number(data?.stats?.read_rate || 0),
				}
				recipients.value = (data?.recipients || []).map((row) => normalizeRecipient(row))
				roleStats.value = normalizeRoleStats(data?.by_role || data?.role_breakdown || [])
			},
			onError(error) {
				errorMessage.value = extractErrorMessage(error, __("Failed to load newsletter report."))
			},
		}
	)
}
</script>
