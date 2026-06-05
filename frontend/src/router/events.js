const routes = [
	{
		name: "EventListView",
		path: "/events",
		component: () => import("@/views/event/List.vue"),
	},
	{
		name: "EventFormView",
		path: "/events/new",
		component: () => import("@/views/event/Form.vue"),
	},
	{
		name: "EventDetailView",
		path: "/events/:id",
		props: true,
		component: () => import("@/views/event/Form.vue"),
	},
]

export default routes
