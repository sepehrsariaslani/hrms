const routes = [
	{
		name: "AppraisalListView",
		path: "/appraisals",
		component: () => import("@/views/appraisal/List.vue"),
	},
	{
		name: "AppraisalFormView",
		path: "/appraisals/new",
		component: () => import("@/views/appraisal/Form.vue"),
	},
	{
		name: "AppraisalDetailView",
		path: "/appraisals/:id",
		props: true,
		component: () => import("@/views/appraisal/Form.vue"),
	},
]

export default routes
