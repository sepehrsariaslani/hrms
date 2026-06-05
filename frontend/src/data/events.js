import { computed, watch } from "vue"
import { createResource } from "frappe-ui"

import dayjs from "@/utils/dayjs"
import { userResource } from "@/data/user"

const EVENT_FIELDS = [
	"name",
	"subject",
	"starts_on",
	"ends_on",
	"all_day",
	"event_type",
	"description",
	"location",
	"owner",
	"creation",
	"modified",
]

function normalizeEvent(row = {}) {
	const startsOn = row.starts_on || row.creation || ""
	const endsOn = row.ends_on || startsOn

	return {
		name: row.name || "",
		subject: row.subject || "",
		starts_on: startsOn,
		ends_on: endsOn,
		all_day: Boolean(row.all_day),
		event_type: row.event_type || "Private",
		description: row.description || "",
		location: row.location || "",
		owner: row.owner || "",
		creation: row.creation || "",
		modified: row.modified || "",
	}
}

function isUpcoming(event) {
	const boundary = event.ends_on || event.starts_on
	if (!boundary) return false
	return !dayjs(boundary).isBefore(dayjs().startOf("day"))
}

export const myEventsResource = createResource({
	url: "frappe.client.get_list",
	auto: false,
	cache: "hrms:my_events",
	makeParams() {
		return {
			doctype: "Event",
			fields: EVENT_FIELDS,
			filters: [
				["Event", "owner", "=", userResource.data?.name],
				["Event", "docstatus", "!=", 2],
			],
			order_by: "starts_on asc",
			limit_page_length: 100,
		}
	},
	transform(data) {
		if (!Array.isArray(data)) return []
		return data.map((row) => normalizeEvent(row))
	},
})

watch(
	() => userResource.data?.name,
	(userId) => {
		if (!userId) return
		myEventsResource.reload()
	},
	{ immediate: true }
)

export const myEvents = computed(() => myEventsResource.data || [])

export const upcomingEvents = computed(() =>
	myEvents.value.filter((event) => isUpcoming(event))
)

export const todayEventsCount = computed(() => {
	const todayStart = dayjs().startOf("day")
	const todayEnd = dayjs().endOf("day")
	return upcomingEvents.value.filter((event) => {
		if (!event.starts_on) return false
		const start = dayjs(event.starts_on)
		return !start.isBefore(todayStart) && !start.isAfter(todayEnd)
	}).length
})

export const thisWeekEventsCount = computed(() => {
	const weekStart = dayjs().startOf("week")
	const weekEnd = dayjs().endOf("week")
	return upcomingEvents.value.filter((event) => {
		if (!event.starts_on) return false
		const start = dayjs(event.starts_on)
		return !start.isBefore(weekStart) && !start.isAfter(weekEnd)
	}).length
})
