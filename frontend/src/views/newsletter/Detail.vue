<template>
	<BaseLayout :pageTitle="__('Newsletter Detail')">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-4">
				<div v-if="!newsletter" class="bg-white rounded p-4 text-sm text-gray-600">
					{{ __("Loading newsletter...") }}
				</div>

				<template v-else>
					<div class="bg-white rounded p-4">
						<div class="flex flex-wrap items-center gap-2">
							<Badge
								:label="__(newsletter.status)"
								variant="outline"
								:theme="statusTheme(newsletter.status)"
								size="sm"
							/>
							<Badge
								:label="__(newsletter.is_read ? 'Read' : 'Unread')"
								variant="outline"
								:theme="newsletter.is_read ? 'green' : 'orange'"
								size="sm"
							/>
						</div>
						<h1 class="text-xl font-bold text-gray-900 mt-3">
							{{ newsletter.title }}
						</h1>
						<div v-if="newsletter.summary" class="text-sm text-gray-600 mt-2">
							{{ newsletter.summary }}
						</div>
						<div class="text-xs text-gray-500 mt-3">
							{{ __("Publish Date") }}: {{ publishDateLabel }}
						</div>
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3">
							<div
								v-for="item in publishInfoItems"
								:key="item.label"
								class="rounded border border-gray-200 bg-gray-50 px-3 py-2"
							>
								<div class="text-[11px] text-gray-500">{{ item.label }}</div>
								<div class="text-xs text-gray-800 mt-0.5">{{ item.value }}</div>
							</div>
						</div>
					</div>

					<div v-if="newsletter.cover_image" class="bg-white rounded p-4">
						<img
							:src="newsletter.cover_image"
							alt="newsletter-cover"
							class="w-full max-h-80 object-cover rounded"
						/>
						<div v-if="newsletter.cover_caption" class="text-xs text-gray-600 mt-2">
							{{ newsletter.cover_caption }}
						</div>
					</div>

					<div class="bg-white rounded p-4">
						<div class="newsletter-content prose prose-sm max-w-none">
							<template v-for="block in contentBlocks" :key="block.key">
								<div v-if="block.type === 'html'" v-html="block.html || '<p></p>'"></div>

								<div
									v-else-if="block.type === 'poll' && block.poll"
									class="not-prose my-4 rounded border border-gray-200 bg-gray-50 p-3"
								>
									<div class="text-sm font-semibold text-gray-900">{{ block.poll.question }}</div>
									<div class="text-[11px] text-gray-500 mt-1">
										{{
											block.poll.allow_multiple
												? __("Multiple choice poll")
												: __("Single choice poll")
										}}
									</div>

									<div class="grid grid-cols-1 gap-2 mt-3">
										<label
											v-for="option in block.poll.options || []"
											:key="`${block.poll.name}-${option.option_text}`"
											class="inline-flex items-center justify-between gap-3 rounded border border-gray-200 bg-white px-2.5 py-2"
										>
											<div class="inline-flex items-center gap-2 text-sm text-gray-800">
												<input
													:type="block.poll.allow_multiple ? 'checkbox' : 'radio'"
													:name="`poll-${block.poll.name}`"
													:checked="isOptionSelected(block.poll.name, option.option_text)"
													@change="togglePollSelection(block.poll, option.option_text)"
												/>
												{{ option.option_text }}
											</div>
											<div class="text-[11px] text-gray-500">
												{{ __("Votes") }}: {{ toPersianDigits(option.vote_count || 0) }}
											</div>
										</label>
									</div>

									<div class="mt-2 flex justify-between items-center gap-2">
										<div class="text-[11px] text-gray-500">
											{{ __("Total Votes") }}: {{ toPersianDigits(block.poll.total_votes || 0) }}
										</div>
										<Button
											size="sm"
											variant="outline"
											:loading="voteResource.loading && activeVotingPoll === block.poll.name"
											@click="submitPollVote(block.poll)"
										>
											{{ __("Submit Vote") }}
										</Button>
									</div>

									<div
										v-if="shouldShowVoters(block.poll)"
										class="mt-3 border-t border-gray-200 pt-2 grid grid-cols-1 gap-2"
									>
										<div
											v-for="option in block.poll.options || []"
											:key="`${block.poll.name}-${option.option_text}-voters`"
											class="rounded border border-gray-200 bg-white px-2 py-1.5"
										>
											<div class="text-[11px] font-semibold text-gray-700">
												{{ option.option_text }}
											</div>
											<div class="text-[11px] text-gray-600 mt-1">
												{{
													option.voters?.length
														? option.voters.map((row) => row.employee_name || row.employee).join("، ")
														: __("No votes yet")
												}}
											</div>
										</div>
									</div>
								</div>

								<div
									v-else-if="block.type === 'poll'"
									class="not-prose my-4 rounded border border-dashed border-amber-300 bg-amber-50 p-3 text-xs text-amber-700"
								>
									{{ __("Poll component was not found.") }}
								</div>
							</template>
						</div>
					</div>

					<div v-if="unplacedPolls.length" class="bg-white rounded p-4">
						<div class="text-sm font-semibold text-gray-900 mb-2">
							{{ __("Polls") }}
						</div>
						<div class="grid grid-cols-1 gap-3">
							<div
								v-for="poll in unplacedPolls"
								:key="`floating-${poll.name}`"
								class="rounded border border-gray-200 bg-gray-50 p-3"
							>
								<div class="text-sm font-semibold text-gray-900">{{ poll.question }}</div>
								<div class="text-[11px] text-gray-500 mt-1">
									{{ poll.allow_multiple ? __("Multiple choice poll") : __("Single choice poll") }}
								</div>
								<div class="grid grid-cols-1 gap-2 mt-3">
									<label
										v-for="option in poll.options || []"
										:key="`${poll.name}-${option.option_text}-floating`"
										class="inline-flex items-center justify-between gap-3 rounded border border-gray-200 bg-white px-2.5 py-2"
									>
										<div class="inline-flex items-center gap-2 text-sm text-gray-800">
											<input
												:type="poll.allow_multiple ? 'checkbox' : 'radio'"
												:name="`poll-floating-${poll.name}`"
												:checked="isOptionSelected(poll.name, option.option_text)"
												@change="togglePollSelection(poll, option.option_text)"
											/>
											{{ option.option_text }}
										</div>
										<div class="text-[11px] text-gray-500">
											{{ __("Votes") }}: {{ toPersianDigits(option.vote_count || 0) }}
										</div>
									</label>
								</div>
								<div class="mt-2 flex justify-between items-center gap-2">
									<div class="text-[11px] text-gray-500">
										{{ __("Total Votes") }}: {{ toPersianDigits(poll.total_votes || 0) }}
									</div>
									<Button
										size="sm"
										variant="outline"
										:loading="voteResource.loading && activeVotingPoll === poll.name"
										@click="submitPollVote(poll)"
									>
										{{ __("Submit Vote") }}
									</Button>
								</div>
								<div
									v-if="shouldShowVoters(poll)"
									class="mt-3 border-t border-gray-200 pt-2 grid grid-cols-1 gap-2"
								>
									<div
										v-for="option in poll.options || []"
										:key="`${poll.name}-${option.option_text}-voters-floating`"
										class="rounded border border-gray-200 bg-white px-2 py-1.5"
									>
										<div class="text-[11px] font-semibold text-gray-700">
											{{ option.option_text }}
										</div>
										<div class="text-[11px] text-gray-600 mt-1">
											{{
												option.voters?.length
													? option.voters.map((row) => row.employee_name || row.employee).join("، ")
													: __("No votes yet")
											}}
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>

					<div v-if="isManager" class="grid grid-cols-1 sm:grid-cols-2 gap-2">
						<router-link
							:to="{ name: 'NewsletterEditView', params: { id: newsletter.name } }"
							v-slot="{ navigate }"
						>
							<Button @click="navigate" variant="outline" class="py-5 text-base w-full">
								{{ __("Edit Newsletter") }}
							</Button>
						</router-link>
						<router-link
							:to="{ name: 'NewsletterReportView', params: { id: newsletter.name } }"
							v-slot="{ navigate }"
						>
							<Button @click="navigate" variant="solid" class="py-5 text-base w-full">
								{{ __("View Report") }}
							</Button>
						</router-link>
					</div>
				</template>

				<ErrorMessage :message="errorMessage" />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref } from "vue"
import { Badge, createResource, ErrorMessage, toast } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import {
	extractErrorMessage,
	isNewsletterManager,
	normalizeNewsletter,
} from "@/data/newsletters"
import { formatJalaliDateShort, formatJalaliDateTime, toPersianDigits } from "@/utils/jalali"

const __ = inject("$translate")
const user = inject("$user")

const props = defineProps({
	id: {
		type: String,
		required: true,
	},
})

const newsletter = ref(null)
const errorMessage = ref("")
const pollSelections = ref({})
const activeVotingPoll = ref("")

const isManager = computed(() => isNewsletterManager(user.data))
const publishDateLabel = computed(() => {
	const dateValue =
		newsletter.value?.published_on ||
		newsletter.value?.scheduled_publish_at ||
		newsletter.value?.creation
	if (!dateValue) return "-"
	return formatJalaliDateShort(dateValue)
})
const publishInfoItems = computed(() => {
	if (!newsletter.value) return []

	const publisherName =
		newsletter.value.published_by_name ||
		newsletter.value.owner ||
		"-"

	return [
		{
			label: __("Publisher"),
			value: publisherName,
		},
		{
			label: __("Audience Scope"),
			value: __(newsletter.value.audience_mode || "All Employees"),
		},
		{
			label: __("Scheduled"),
			value: newsletter.value.scheduled_publish_at
				? formatJalaliDateTime(newsletter.value.scheduled_publish_at)
				: "-",
		},
		{
			label: __("Expires On"),
			value: newsletter.value.expires_on ? formatJalaliDateTime(newsletter.value.expires_on) : "-",
		},
	]
})
const pollByName = computed(() => {
	const rows = newsletter.value?.polls || []
	return Object.fromEntries(rows.map((row) => [row.name, row]))
})
const contentBlocks = computed(() => {
	const content = String(newsletter.value?.content || "")
	if (!content.trim()) return [{ type: "html", key: "html-0", html: "<p></p>" }]

	const tokenRegex = /\[\[POLL:([^\]]+)\]\]/g
	const blocks = []
	let cursor = 0
	let matchIndex = 0

	while (true) {
		const match = tokenRegex.exec(content)
		if (!match) break

		const beforeHtml = content.slice(cursor, match.index)
		if (beforeHtml) {
			blocks.push({
				type: "html",
				key: `html-${matchIndex}`,
				html: beforeHtml,
			})
		}

		const pollName = String(match[1] || "").trim()
		blocks.push({
			type: "poll",
			key: `poll-${pollName}-${matchIndex}`,
			poll: pollByName.value[pollName] || null,
		})

		cursor = match.index + match[0].length
		matchIndex += 1
	}

	const tail = content.slice(cursor)
	if (tail || !blocks.length) {
		blocks.push({
			type: "html",
			key: `html-tail-${matchIndex}`,
			html: tail || "<p></p>",
		})
	}

	return blocks
})
const embeddedPollNames = computed(() => {
	return new Set(
		contentBlocks.value
			.filter((block) => block.type === "poll" && block.poll?.name)
			.map((block) => block.poll.name)
	)
})
const unplacedPolls = computed(() => {
	const allPolls = newsletter.value?.polls || []
	return allPolls.filter((poll) => !embeddedPollNames.value.has(poll.name))
})

const detailResource = createResource({
	url: "hrms.api.newsletter.get_newsletter_detail",
	auto: false,
})

const markReadResource = createResource({
	url: "hrms.api.newsletter.mark_newsletter_read",
	auto: false,
})
const voteResource = createResource({
	url: "hrms.api.newsletter.submit_poll_vote",
	auto: false,
})

loadNewsletter()

function loadNewsletter() {
	detailResource.fetch(
		{
			newsletter_name: props.id,
		},
		{
			onSuccess(data) {
				errorMessage.value = ""
				newsletter.value = normalizeNewsletter(data?.newsletter || data)
				initializePollSelections()
				markAsRead()
			},
			onError(error) {
				errorMessage.value = extractErrorMessage(error, __("Failed to load newsletter details."))
			},
		}
	)
}

function markAsRead() {
	if (!newsletter.value?.name) return
	markReadResource.submit(
		{
			newsletter_name: newsletter.value.name,
		},
		{
			onSuccess() {
				if (newsletter.value) newsletter.value.is_read = true
			},
		}
	)
}

function statusTheme(status) {
	if (status === "Published") return "green"
	if (status === "Scheduled") return "blue"
	if (status === "Cancelled") return "red"
	return "orange"
}

function initializePollSelections() {
	const rows = newsletter.value?.polls || []
	pollSelections.value = Object.fromEntries(
		rows.map((poll) => [poll.name, [...(poll.my_votes || [])]])
	)
}

function isOptionSelected(pollName, optionText) {
	return (pollSelections.value[pollName] || []).includes(optionText)
}

function togglePollSelection(poll, optionText) {
	if (!poll?.name || !optionText) return

	const selected = new Set(pollSelections.value[poll.name] || [])
	if (poll.allow_multiple) {
		if (selected.has(optionText)) selected.delete(optionText)
		else selected.add(optionText)
	} else {
		selected.clear()
		selected.add(optionText)
	}
	pollSelections.value[poll.name] = Array.from(selected)
}

function shouldShowVoters(poll) {
	if (isManager.value) return true
	if (poll?.is_private) return false
	return Boolean(poll?.show_voters)
}

function submitPollVote(poll) {
	const selected = pollSelections.value[poll?.name] || []
	if (!poll?.name || !selected.length) {
		errorMessage.value = __("Please select at least one poll option.")
		return
	}

	activeVotingPoll.value = poll.name
	voteResource.submit(
		{
			newsletter_name: newsletter.value?.name,
			poll_name: poll.name,
			selected_options: JSON.stringify(selected),
		},
		{
			onSuccess(data) {
				errorMessage.value = ""
				upsertPoll(data?.poll)
				toast({
					title: __("Success"),
					text: __("Vote submitted successfully."),
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			},
			onError(error) {
				errorMessage.value = extractErrorMessage(error, __("Failed to submit vote."))
			},
			onFinally() {
				activeVotingPoll.value = ""
			},
		}
	)
}

function upsertPoll(poll) {
	if (!newsletter.value || !poll?.name) return
	const rows = newsletter.value.polls || []
	const nextRows = rows.filter((row) => row.name !== poll.name)
	nextRows.push(poll)
	newsletter.value.polls = nextRows
	pollSelections.value[poll.name] = [...(poll.my_votes || [])]
}
</script>
