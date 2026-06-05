const routes = [
	{
		name: "MealPlanFormView",
		path: "/meal-plans/new",
		component: () => import("@/views/meal/PlanForm.vue"),
	},
	{
		name: "MealPlanDetailView",
		path: "/meal-plans/:id",
		props: true,
		component: () => import("@/views/meal/PlanForm.vue"),
	},
	{
		name: "MealCoordinatorBoardView",
		path: "/meal-coordinator",
		component: () => import("@/views/meal/CoordinatorBoard.vue"),
	},
]

export default routes
