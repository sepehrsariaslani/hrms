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
})

export const imprestLayoutContext = createResource({
	url: "hrms.api.imprest.get_imprest_context",
	auto: false,
	cache: "hrms:layout_imprest_context",
})

export const employeeDeskVisibility = createResource({
	url: "hrms.api.get_employee_desk_visibility",
	auto: false,
	cache: "hrms:employee_desk_visibility",
	transform(data) {
		return data?.visibility || {}
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

export function refreshLayoutContext() {
	if (!employeeResource.data?.name) return
	newsletterLayoutContext.reload()
	imprestLayoutContext.reload()
	employeeDeskVisibility.reload()
	employeeDeskPersonalization.reload()
	employeeDeskGlobalPersonalization.reload()
}

watch(
	() => employeeResource.data?.name,
	(employeeName) => {
		if (!employeeName) return
		refreshLayoutContext()
	},
	{ immediate: true }
)
