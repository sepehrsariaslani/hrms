export function buildNavbarGroups(
	translate,
	{
		unreadNewsletterCount = 0,
		hasImprestAccess = false,
		canSeeAllocatorShiftTools = false,
		canSeeWeeklyShiftPlanner = false,
	} = {}
) {
	const __ = translate || ((text) => text)

	const mainItems = [
		{ route: "/home", label: __("خانه"), icon: "home" },
	]

	const shiftItems = [
		{ route: "/dashboard/attendance", label: __("تقویم حضور و غیاب"), icon: "calendar" },
		{ route: "/dashboard/leaves", label: __("مرخصی"), icon: "coffee" },
		{ route: "/dashboard/missions", label: __("ماموریت‌ها"), icon: "briefcase" },
	]

	if (canSeeWeeklyShiftPlanner) {
		shiftItems.push({
			route: "/weekly-shift-planner",
			label: __("برنامه شیفت هفتگی"),
			icon: "clock",
		})
	}

	if (canSeeAllocatorShiftTools) {
		shiftItems.push(
			{ route: "/shift-allocator-scheduler", label: __("تقویم شیفت هفتگی"), icon: "calendar-days" },
			{ route: "/team-weekly-shifts", label: __("شیفت هفتگی تیم"), icon: "users" }
		)
	}

	const expenseItems = [
		{ route: "/dashboard/expense-claims", label: __("مطالبه هزینه"), icon: "credit-card" },
		{ route: "/employee-advances", label: __("درخواست مساعده"), icon: "wallet" },
	]

	if (hasImprestAccess) {
		expenseItems.unshift({
			route: "/dashboard/imprest",
			label: __("تنخواه"),
			icon: "briefcase",
		})
	}

	const otherItems = [
		{ route: "/dashboard/events", label: __("رویدادها"), icon: "calendar" },
		{ route: "/dashboard/salary-slips", label: __("حقوق"), icon: "dollar-sign" },
		{ route: "/dashboard/appraisals", label: __("ارزیابی"), icon: "bar-chart-2" },
		{ route: "/dashboard/meals", label: __("غذا"), icon: "shopping-bag" },
		{ route: "/dashboard/complaints", label: __("شکایات"), icon: "message-square" },
		{
			route: "/dashboard/newsletters",
			label: __("خبرنامه"),
			icon: "book-open",
			badge: unreadNewsletterCount,
		},
	]

	return [
		{
			title: __("اصلی"),
			items: mainItems,
		},
		{
			title: __("شیفت"),
			items: shiftItems,
		},
		{
			title: __("هزینه"),
			items: expenseItems,
		},
		{
			title: __("سایر"),
			items: otherItems,
		},
		{
			title: __("حساب کاربری"),
			items: [
				{ route: "/profile", label: __("پروفایل"), icon: "user" },
				{ route: "/notifications", label: __("اعلان‌ها"), icon: "bell" },
				{ route: "/settings", label: __("تنظیمات"), icon: "settings" },
			],
		},
	]
}
