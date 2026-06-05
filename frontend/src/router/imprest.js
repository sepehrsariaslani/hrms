const routes = [
	{
		name: "ImprestHome",
		path: "/imprest",
		component: () => import("@/views/imprest/Dashboard.vue"),
	},
	{
		name: "ImprestCalendarView",
		path: "/imprest/calendar",
		component: () => import("@/views/imprest/Calendar.vue"),
	},
	{
		name: "ImprestQuickEntryView",
		path: "/imprest/quick-entry",
		component: () => import("@/views/imprest/QuickEntry.vue"),
	},
	{
		name: "ImprestQuickEntryEditView",
		path: "/imprest/quick-entry/:id",
		props: true,
		component: () => import("@/views/imprest/QuickEntry.vue"),
	},
]

export default routes
