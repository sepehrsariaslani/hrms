const routes = [
	{
		name: "MissionListView",
		path: "/missions",
		component: () => import("@/views/mission/List.vue"),
	},
	{
		name: "MissionFormView",
		path: "/missions/new",
		component: () => import("@/views/mission/Form.vue"),
	},
	{
		name: "MissionDetailView",
		path: "/missions/:id",
		props: true,
		component: () => import("@/views/mission/Form.vue"),
	},
]

export default routes
