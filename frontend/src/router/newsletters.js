const routes = [
	{
		name: "NewsletterFormView",
		path: "/newsletters/new",
		component: () => import("@/views/newsletter/Form.vue"),
	},
	{
		name: "NewsletterEditView",
		path: "/newsletters/:id/edit",
		props: true,
		component: () => import("@/views/newsletter/Form.vue"),
	},
	{
		name: "NewsletterDetailView",
		path: "/newsletters/:id",
		props: true,
		component: () => import("@/views/newsletter/Detail.vue"),
	},
	{
		name: "NewsletterReportView",
		path: "/newsletters/:id/report",
		props: true,
		component: () => import("@/views/newsletter/Report.vue"),
	},
]

export default routes
