import { computed, watch } from "vue"
import { createResource } from "frappe-ui"
import { employeeResource } from "./employee"
import {
	employeeDeskGlobalPersonalization,
	employeeDeskPersonalization,
} from "./personalization"

export const newsletterLayoutContext = createResource({
	url: "hrms.api.newsletter.get_newsletter_dashboard_context",
	auto: false,
	cache: "hrms:layout_newsletter_unread",
	onError(error) {
		// newsletter API may be unavailable on some deployments — fail silently
		newsletterLayoutContext.data = { employee_newsletters: [], managed_newsletters: [], stats: { total_sent: 0, published: 0, scheduled: 0, read_count: 0, unread_count: 0 }, is_newsletter_manager: false }
	},
})

export const imprestLayoutContext = createResource({
	url: "hrms.api.imprest.get_imprest_context",
	auto: false,
	cache: "hrms:layout_imprest_context",
	onError(error) {
		imprestLayoutContext.data = { has_imprest: false }
	},
})

export const employeeDeskVisibility = createResource({
	url: "hrms.api.get_employee_desk_visibility",
	auto: false,
	cache: "hrms:employee_desk_visibility",
	transform(data) {
		return data?.visibility || {}
	},
	onError(error) {
		employeeDeskVisibility.data = { visibility: {} }
	},
})

export const layoutUnreadNewsletterCount = computed(() => {
	const rows = newsletterLayoutContext.data?.employee_newsletters || []
	return rows.filter(
		(row) => !row?.is_read && ["Published", "Scheduled"].includes(row?.status)
	).length
})

export const layoutHasImprestAccess = computed(
	() => Boolean(imprestLayoutContext.data?.has_imprest)
)

export async function refreshLayoutContext() {
	if (!employeeResource.data?.name) return
	await Promise.allSettled([
		newsletterLayoutContext.reload().catch(() => {}),
		imprestLayoutContext.reload().catch(() => {}),
		employeeDeskVisibility.reload().catch(() => {}),
		employeeDeskPersonalization.reload().catch(() => {}),
		employeeDeskGlobalPersonalization.reload().catch(() => {}),
	])
}

watch(
	() => employeeResource.data?.name,
	(employeeName) => {
		if (!employeeName) return
		refreshLayoutContext()
	},
	{ immediate: true }
)
