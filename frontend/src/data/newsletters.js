import dayjs from "@/utils/dayjs"

export const NEWSLETTER_MANAGER_ROLES = ["HR Manager", "HR User", "System Manager"]

export const NEWSLETTER_AUDIENCE_MODES = [
	"All Employees",
	"By Role",
	"Specific Employees",
]

export function isNewsletterManager(user = {}) {
	const roles = user?.roles || []
	return NEWSLETTER_MANAGER_ROLES.some((role) => roles.includes(role))
}

export function normalizeNewsletter(data = {}) {
	const row = { ...data }
	const scheduledAt =
		row.scheduled_publish_at || row.schedule_at || row.publish_on || ""
	const publishedAt = row.published_on || row.publish_date || ""
	const expiresOn = row.expires_on || row.expiry_date || ""
	const status = row.status || inferStatus({ scheduledAt, publishedAt, docstatus: row.docstatus })

	const targetRoles = normalizeStringArray(row.target_roles)
	const targetEmployees = normalizeStringArray(row.target_employees)
	const excludedEmployees = normalizeStringArray(
		row.excluded_employees || row.excluded_target_employees
	)
	const polls = Array.isArray(row.polls) ? row.polls : []

	const recipientCount = Number(row.recipient_count || row.total_recipients || 0)
	const readCount = Number(row.read_count || row.total_reads || 0)
	const unreadCount = Math.max(recipientCount - readCount, 0)
	const readRate = recipientCount
		? Number(((readCount / recipientCount) * 100).toFixed(1))
		: 0

	return {
		...row,
		status,
		scheduled_publish_at: scheduledAt,
		published_on: publishedAt,
		expires_on: expiresOn,
		target_roles: targetRoles,
		target_employees: targetEmployees,
		excluded_employees: excludedEmployees,
		polls,
		audience_mode: row.audience_mode || inferAudienceMode(targetRoles, targetEmployees),
		cover_image: row.cover_image || row.image || "",
		cover_caption: row.cover_caption || "",
		title: row.title || row.subject || "",
		summary: row.summary || row.description || "",
		content: row.content || "",
		is_read: Boolean(row.is_read),
		recipient_count: recipientCount,
		read_count: readCount,
		unread_count: unreadCount,
		read_rate: readRate,
	}
}

export function normalizeRecipient(data = {}) {
	return {
		...data,
		employee: data.employee || data.employee_id || "",
		employee_name: data.employee_name || data.full_name || data.employee || "",
		designation: data.designation || data.role || "",
		is_read: Boolean(data.is_read),
		read_on: data.read_on || data.read_at || "",
	}
}

export function normalizeRoleStats(data = []) {
	return (data || []).map((row) => ({
		role: row.role || row.designation || "",
		recipient_count: Number(row.recipient_count || row.total_recipients || 0),
		read_count: Number(row.read_count || row.total_reads || 0),
		read_rate: Number(row.read_rate || 0),
	}))
}

export function normalizeStringArray(value) {
	if (Array.isArray(value)) {
		return value.filter(Boolean).map((item) => String(item).trim()).filter(Boolean)
	}

	if (typeof value !== "string") return []
	const trimmed = value.trim()
	if (!trimmed) return []

	try {
		const parsed = JSON.parse(trimmed)
		if (Array.isArray(parsed)) return normalizeStringArray(parsed)
	} catch (_error) {
		// value is plain text and will be split
	}

	return trimmed
		.split(",")
		.map((item) => item.trim())
		.filter(Boolean)
}

export function toDateTimeInput(value) {
	if (!value) return ""
	const parsed = dayjs(value)
	if (!parsed.isValid()) return ""
	return parsed.format("YYYY-MM-DDTHH:mm")
}

export function toServerDateTime(value) {
	if (!value) return ""
	const parsed = dayjs(value)
	if (!parsed.isValid()) return ""
	return parsed.format("YYYY-MM-DD HH:mm:ss")
}

export function extractErrorMessage(error, fallbackMessage) {
	if (Array.isArray(error?.messages) && error.messages.length) return error.messages[0]
	if (typeof error?.message === "string" && error.message.trim()) return error.message
	return fallbackMessage
}

function inferStatus({ scheduledAt, publishedAt, docstatus }) {
	if (Number(docstatus) === 2) return "Cancelled"
	if (publishedAt) return "Published"
	if (scheduledAt && dayjs(scheduledAt).isAfter(dayjs())) return "Scheduled"
	return "Draft"
}

function inferAudienceMode(targetRoles = [], targetEmployees = []) {
	if (targetEmployees.length) return "Specific Employees"
	if (targetRoles.length) return "By Role"
	return "All Employees"
}
