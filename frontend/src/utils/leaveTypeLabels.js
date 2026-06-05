const LEAVE_TYPE_LABEL_MAP = {
	"Leave Without Pay": "مرخصی بدون حقوق",
	"Privilege Leave": "مرخصی استحقاقی",
	"Sick Leave": "مرخصی استعلاجی",
	"Compensatory Off": "مرخصی جبرانی",
	"Casual Leave": "مرخصی اتفاقی",
}

export function localizeLeaveType(leaveType) {
	if (!leaveType) return ""
	return LEAVE_TYPE_LABEL_MAP[leaveType] || leaveType
}

