export function buildNavbarGroups(
	translate,
	{
		unreadNewsletterCount = 0,
		hasImprestAccess = false,
		canSeeAllocatorShiftTools = false,
		canSeeWeeklyShiftPlanner = false,
		visibility = {},
		hiddenRoutes = [],
		routeOrder = [],
		customLabels = {},
	} = {}
) {
	const __ = translate || ((text) => text)
	const isEnabled = (key) => visibility?.[key] !== false
	const hiddenRouteSet = new Set(hiddenRoutes || [])
	const includeRoute = (route) => !hiddenRouteSet.has(route)
	const routeOrderMap = new Map((routeOrder || []).map((route, index) => [route, index]))
	const labelFor = (route, fallbackLabel) => customLabels?.[route] || fallbackLabel
	const sortByCustomOrder = (items) =>
		[...(items || [])].sort((left, right) => {
			const leftOrder = routeOrderMap.has(left.route) ? routeOrderMap.get(left.route) : Number.MAX_SAFE_INTEGER
			const rightOrder = routeOrderMap.has(right.route) ? routeOrderMap.get(right.route) : Number.MAX_SAFE_INTEGER
			if (leftOrder !== rightOrder) return leftOrder - rightOrder
			return 0
		})

	const mainItems = [
		{ route: "/home", label: labelFor("/home", __("خانه")), icon: "home" },
	].filter((item) => includeRoute(item.route))
	if (isEnabled("enable_requests_center")) {
		if (includeRoute("/dashboard/requests")) {
			mainItems.push({
				route: "/dashboard/requests",
				label: labelFor("/dashboard/requests", __("درخواست‌ها")),
				icon: "inbox",
			})
		}
	}

	const shiftItems = []
	if (isEnabled("enable_attendance")) {
		if (includeRoute("/dashboard/attendance")) {
			shiftItems.push({
				route: "/dashboard/attendance",
				label: labelFor("/dashboard/attendance", __("تقویم حضور و غیاب")),
				icon: "calendar",
			})
		}
	}
	if (isEnabled("enable_leaves")) {
		if (includeRoute("/dashboard/leaves")) {
			shiftItems.push({
				route: "/dashboard/leaves",
				label: labelFor("/dashboard/leaves", __("مرخصی")),
				icon: "coffee",
			})
		}
	}
	if (isEnabled("enable_missions")) {
		if (includeRoute("/dashboard/missions")) {
			shiftItems.push({
				route: "/dashboard/missions",
				label: labelFor("/dashboard/missions", __("ماموریت‌ها")),
				icon: "briefcase",
			})
		}
	}

	if (canSeeWeeklyShiftPlanner && isEnabled("enable_attendance")) {
		if (includeRoute("/weekly-shift-planner")) {
			shiftItems.push({
				route: "/weekly-shift-planner",
				label: labelFor("/weekly-shift-planner", __("برنامه شیفت هفتگی")),
				icon: "clock",
			})
		}
	}

	if (canSeeAllocatorShiftTools && isEnabled("enable_attendance")) {
		if (includeRoute("/shift-allocator-scheduler")) {
			shiftItems.push({
				route: "/shift-allocator-scheduler",
				label: labelFor("/shift-allocator-scheduler", __("تقویم شیفت هفتگی")),
				icon: "calendar-days",
			})
		}
	}

	const expenseItems = []
	if (isEnabled("enable_expense_claims")) {
		if (includeRoute("/dashboard/expense-claims")) {
			expenseItems.push({
				route: "/dashboard/expense-claims",
				label: labelFor("/dashboard/expense-claims", __("مطالبه هزینه")),
				icon: "credit-card",
			})
		}
	}
	if (isEnabled("enable_employee_advances")) {
		if (includeRoute("/employee-advances")) {
			expenseItems.push({
				route: "/employee-advances",
				label: labelFor("/employee-advances", __("درخواست مساعده")),
				icon: "wallet",
			})
		}
	}

	if (hasImprestAccess && isEnabled("enable_imprest")) {
		if (includeRoute("/dashboard/imprest")) {
			expenseItems.unshift({
				route: "/dashboard/imprest",
				label: labelFor("/dashboard/imprest", __("تنخواه")),
				icon: "briefcase",
			})
		}
	}

	const otherItems = []
	if (isEnabled("enable_events")) {
		if (includeRoute("/dashboard/events")) {
			otherItems.push({
				route: "/dashboard/events",
				label: labelFor("/dashboard/events", __("رویدادها")),
				icon: "calendar",
			})
		}
	}
	if (isEnabled("enable_salary_slips")) {
		if (includeRoute("/dashboard/salary-slips")) {
			otherItems.push({
				route: "/dashboard/salary-slips",
				label: labelFor("/dashboard/salary-slips", __("حقوق")),
				icon: "dollar-sign",
			})
		}
	}
	if (isEnabled("enable_appraisals")) {
		if (includeRoute("/dashboard/appraisals")) {
			otherItems.push({
				route: "/dashboard/appraisals",
				label: labelFor("/dashboard/appraisals", __("ارزیابی")),
				icon: "bar-chart-2",
			})
		}
	}
	if (isEnabled("enable_meals")) {
		if (includeRoute("/dashboard/meals")) {
			otherItems.push({
				route: "/dashboard/meals",
				label: labelFor("/dashboard/meals", __("غذا")),
				icon: "shopping-bag",
			})
		}
	}
	if (isEnabled("enable_complaints")) {
		if (includeRoute("/dashboard/complaints")) {
			otherItems.push({
				route: "/dashboard/complaints",
				label: labelFor("/dashboard/complaints", __("شکایات")),
				icon: "message-square",
			})
		}
	}
	if (isEnabled("enable_newsletters")) {
		if (includeRoute("/dashboard/newsletters")) {
			otherItems.push({
				route: "/dashboard/newsletters",
				label: labelFor("/dashboard/newsletters", __("خبرنامه")),
				icon: "book-open",
				badge: unreadNewsletterCount,
			})
		}
	}

	const groups = [
		{
			title: __("اصلی"),
			items: sortByCustomOrder(mainItems),
		},
		{
			title: __("شیفت"),
			items: sortByCustomOrder(shiftItems),
		},
		{
			title: __("هزینه"),
			items: sortByCustomOrder(expenseItems),
		},
		{
			title: __("سایر"),
			items: sortByCustomOrder(otherItems),
		},
		{
			title: __("حساب کاربری"),
			items: sortByCustomOrder([
				{ route: "/profile", label: labelFor("/profile", __("پروفایل")), icon: "user" },
				{ route: "/notifications", label: labelFor("/notifications", __("اعلان‌ها")), icon: "bell" },
				{ route: "/settings", label: labelFor("/settings", __("تنظیمات")), icon: "settings" },
			].filter((item) => includeRoute(item.route)),
			),
		},
	]

	return groups.filter((group) => (group.items || []).length)
}
