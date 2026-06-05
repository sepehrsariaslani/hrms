import { frappeRequest } from "frappe-ui"

export async function callImprest(method, params = {}) {
	const response = await frappeRequest({
		url: `/api/method/hrms.api.imprest.${method}`,
		params,
	})
	return response?.message ?? response
}

export function extractErrorMessage(error, fallback) {
	if (Array.isArray(error?.messages) && error.messages.length) return error.messages[0]
	if (typeof error?.message === "string" && error.message.trim()) return error.message
	return fallback
}
