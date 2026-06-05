<template>
	<BaseLayout :pageTitle="__('Organization Newsletters')">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-4">
				<div v-if="isManager" class="grid grid-cols-1 sm:grid-cols-2 gap-2">
					<router-link :to="{ name: 'NewsletterFormView' }" v-slot="{ navigate }">
						<Button @click="navigate" variant="solid" class="py-5 text-base w-full">
							{{ __('Create New Announcement') }}
						</Button>
					</router-link>
					<Button variant="outline" class="py-5 text-base w-full" @click="reloadDashboard">
						{{ __('Refresh') }}
					</Button>
				</div>

				<div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
					<div
						v-for="card in kpiCards"
						:key="card.label"
						class="rounded-lg border bg-white p-3 hr-accent-border"
					>
						<div class="text-xs text-gray-500">{{ __(card.label) }}</div>
						<div class="text-2xl font-semibold text-gray-900">
							{{ toPersianDigits(card.value) }}
						</div>
					</div>
				</div>

				<div class="w-full">
					<div class="text-lg text-gray-800 font-bold">{{ __('Latest Newsletters') }}</div>
					<div
						v-if="employeeNewsletters.length"
						class="flex flex-col bg-white rounded mt-4 overflow-hidden"
					>
						<router-link
							v-for="newsletter in employeeNewsletters"
							:key="newsletter.name"
							:to="{ name: 'NewsletterDetailView', params: { id: newsletter.name } }"
							class="p-3.5 border-b last:border-b-0"
						>
							<div class="flex items-start justify-between gap-3">
								<div class="min-w-0">
									<div class="text-sm font-semibold text-gray-900 truncate">
										{{ newsletter.title }}
									</div>
									<div class="text-xs text-gray-600 mt-1 line-clamp-2">
										{{ newsletter.summary || __("No summary") }}
									</div>
									<div class="text-[11px] text-gray-500 mt-1">
										{{ publishDateLabel(newsletter) }}
									</div>
								</div>
								<div class="flex flex-col items-end gap-1">
									<Badge
										:label="__(newsletter.is_read ? 'Read' : 'Unread')"
										variant="outline"
										:theme="newsletter.is_read ? 'green' : 'orange'"
										size="sm"
									/>
									<Badge
										v-if="isManager"
										:label="__(newsletter.status)"
										variant="outline"
										:theme="statusTheme(newsletter.status)"
										size="sm"
									/>
								</div>
							</div>
						</router-link>
					</div>
					<EmptyState v-else :message="__('No newsletters available')" />
				</div>

				<div v-if="isManager" class="w-full">
					<div class="text-lg text-gray-800 font-bold">{{ __('HR Manager Board') }}</div>
					<div
						v-if="managedNewsletters.length"
						class="flex flex-col bg-white rounded mt-4 overflow-hidden"
					>
						<div
							v-for="newsletter in managedNewsletters"
							:key="newsletter.name"
							class="p-3.5 border-b last:border-b-0"
						>
							<div class="flex items-center justify-between gap-3">
								<div class="min-w-0">
									<div class="text-sm font-semibold text-gray-900 truncate">
										{{ newsletter.title }}
									</div>
									<div class="text-[11px] text-gray-500 mt-1">
										{{ publishDateLabel(newsletter) }}
									</div>
								</div>
								<Badge
									:label="__(newsletter.status)"
									variant="outline"
									:theme="statusTheme(newsletter.status)"
									size="sm"
								/>
							</div>
							<div class="grid grid-cols-2 gap-2 mt-3">
								<router-link
									:to="{ name: 'NewsletterEditView', params: { id: newsletter.name } }"
									v-slot="{ navigate }"
								>
									<Button @click="navigate" variant="outline" class="w-full">
										{{ __('Edit') }}
									</Button>
								</router-link>
								<router-link
									:to="{ name: 'NewsletterReportView', params: { id: newsletter.name } }"
									v-slot="{ navigate }"
								>
									<Button @click="navigate" variant="solid" class="w-full">
										{{ __('View Report') }}
									</Button>
								</router-link>
							</div>
						</div>
					</div>
					<EmptyState v-else :message="__('No announcements created yet')" />
				</div>

				<ErrorMessage :message="errorMessage" />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref } from "vue"
import { Badge, createResource, ErrorMessage } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import {
	extractErrorMessage,
	isNewsletterManager,
	normalizeNewsletter,
} from "@/data/newsletters"
import { formatJalaliDateShort, toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")
const user = inject("$user")

const errorMessage = ref("")
const employeeNewsletters = ref([])
const managedNewsletters = ref([])
const stats = ref({
	total_sent: 0,
	published: 0,
	scheduled: 0,
	read_count: 0,
	unread_count: 0,
})

const isManager = computed(() => isNewsletterManager(user.data))

const dashboardResource = createResource({
	url: "hrms.api.newsletter.get_newsletter_dashboard_context",
	auto: true,
	cache: "hrms:newsletter_dashboard",
	onSuccess(data) {
		errorMessage.value = ""
		employeeNewsletters.value = (data?.employee_newsletters || [])
			.map((row) => normalizeNewsletter(row))
			.slice(0, 8)
		managedNewsletters.value = (data?.managed_newsletters || [])
			.map((row) => normalizeNewsletter(row))
			.slice(0, 8)

		stats.value = {
			total_sent: Number(data?.stats?.total_sent || data?.stats?.recipient_count || 0),
			published: Number(data?.stats?.published || 0),
			scheduled: Number(data?.stats?.scheduled || 0),
			read_count: Number(data?.stats?.read_count || 0),
			unread_count: Number(data?.stats?.unread_count || 0),
		}
	},
	onError(error) {
		errorMessage.value = extractErrorMessage(error, __("Failed to load newsletters."))
	},
})

const kpiCards = computed(() => {
	if (!isManager.value) {
		return [
			{ label: "Unread Newsletters", value: stats.value.unread_count },
			{ label: "Read Newsletters", value: stats.value.read_count },
			{ label: "Scheduled Newsletters", value: stats.value.scheduled },
			{ label: "Published Newsletters", value: stats.value.published },
		]
	}

	return [
		{ label: "Total Recipients", value: stats.value.total_sent },
		{ label: "Read Newsletters", value: stats.value.read_count },
		{ label: "Unread Newsletters", value: stats.value.unread_count },
		{ label: "Published Newsletters", value: stats.value.published },
	]
})

function reloadDashboard() {
	dashboardResource.reload()
}

function publishDateLabel(newsletter) {
	const dateValue =
		newsletter.published_on || newsletter.scheduled_publish_at || newsletter.creation || ""
	if (!dateValue) return __("No publish date")
	return `${__("Publish Date")}: ${formatJalaliDateShort(dateValue)}`
}

function statusTheme(status) {
	if (status === "Published") return "green"
	if (status === "Scheduled") return "blue"
	if (status === "Cancelled") return "red"
	return "orange"
}
</script>
