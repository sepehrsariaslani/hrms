const routes = [
	{
		name: "EmployeeGrievanceListView",
		path: "/employee-grievances",
		component: () => import("@/views/complaint/List.vue"),
	},
	{
		name: "EmployeeGrievanceFormView",
		path: "/employee-grievances/new",
		component: () => import("@/views/complaint/Form.vue"),
	},
	{
		name: "EmployeeGrievanceDetailView",
		path: "/employee-grievances/:id",
		props: true,
		component: () => import("@/views/complaint/Form.vue"),
	},
]

export default routes
