import { createRouter, createWebHistory } from "@ionic/vue-router"

import TabbedView from "@/views/TabbedView.vue"
import attendanceRoutes from "./attendance"
import leaveRoutes from "./leaves"
import claimRoutes from "./claims"
import employeeAdvanceRoutes from "./advances"
import salarySlipRoutes from "./salary_slips"
import complaintRoutes from "./complaints"
import mealRoutes from "./meals"
import appraisalRoutes from "./appraisals"
import newsletterRoutes from "./newsletters"
import imprestRoutes from "./imprest"
import missionRoutes from "./missions"
import eventRoutes from "./events"

const routes = [
	{
		path: "/",
		redirect: "/home",
	},
	{
		path: "/",
		component: TabbedView,
		children: [
			{
				path: "",
				redirect: "/home",
			},
			{
				path: "/home",
				name: "Home",
				component: () => import("@/views/Home.vue"),
			},
			{
				path: "/dashboard/requests",
				name: "RequestsDashboard",
				component: () => import("@/views/requests/Dashboard.vue"),
			},
			{
				path: "/dashboard/attendance",
				name: "AttendanceDashboard",
				component: () => import("@/views/attendance/Dashboard.vue"),
			},
			{
				path: "/weekly-shift-planner",
				name: "WeeklyShiftPlannerView",
				component: () => import("@/views/attendance/WeeklyShiftPlanner.vue"),
			},
			{
				path: "/team-weekly-shifts",
				name: "TeamWeeklyShiftBoardView",
				component: () => import("@/views/attendance/TeamWeeklyShiftBoard.vue"),
			},
			{
				path: "/shift-allocator-scheduler",
				name: "ShiftAllocatorSchedulerView",
				component: () => import("@/views/attendance/ShiftAllocatorScheduler.vue"),
			},
			{
				path: "/dashboard/leaves",
				name: "LeavesDashboard",
				component: () => import("@/views/leave/Dashboard.vue"),
			},
			{
				path: "/dashboard/expense-claims",
				name: "ExpenseClaimsDashboard",
				component: () => import("@/views/expense_claim/Dashboard.vue"),
			},
			{
				path: "/dashboard/salary-slips",
				name: "SalarySlipsDashboard",
				component: () => import("@/views/salary_slip/Dashboard.vue"),
			},
			{
				path: "/dashboard/complaints",
				name: "ComplaintsDashboard",
				component: () => import("@/views/complaint/Dashboard.vue"),
			},
			{
				path: "/dashboard/meals",
				name: "MealsDashboard",
				component: () => import("@/views/meal/Dashboard.vue"),
			},
			{
				path: "/dashboard/appraisals",
				name: "AppraisalsDashboard",
				component: () => import("@/views/appraisal/Dashboard.vue"),
			},
			{
				path: "/dashboard/newsletters",
				name: "NewslettersDashboard",
				component: () => import("@/views/newsletter/Dashboard.vue"),
			},
			{
				path: "/dashboard/missions",
				name: "MissionsDashboard",
				component: () => import("@/views/mission/Dashboard.vue"),
			},
			{
				path: "/dashboard/imprest",
				name: "ImprestDashboard",
				component: () => import("@/views/imprest/Dashboard.vue"),
			},
			{
				path: "/dashboard/events",
				name: "EventsDashboard",
				component: () => import("@/views/event/Dashboard.vue"),
			},
		],
	},
	{
		path: "/login",
		name: "Login",
		component: () => import("@/views/Login.vue"),
	},
	{
		path: "/profile",
		name: "Profile",
		component: () => import("@/views/Profile.vue"),
	},
	{
		path: "/notifications",
		name: "Notifications",
		component: () => import("@/views/Notifications.vue"),
	},
	{
		path: "/settings",
		name: "Settings",
		component: () => import("@/views/AppSettings.vue"),
	},
	{
		path: "/training",
		name: "TrainingCenter",
		component: () => import("@/views/TrainingCenter.vue"),
	},
	{
		path: "/invalid-employee",
		name: "InvalidEmployee",
		component: () => import("@/views/InvalidEmployee.vue"),
	},
	...attendanceRoutes,
	...leaveRoutes,
	...claimRoutes,
	...employeeAdvanceRoutes,
	...salarySlipRoutes,
	...complaintRoutes,
	...mealRoutes,
	...appraisalRoutes,
	...newsletterRoutes,
	...imprestRoutes,
	...missionRoutes,
	...eventRoutes,
]

const router = createRouter({
	history: createWebHistory("/hrms"),
	routes,
})

export default router
