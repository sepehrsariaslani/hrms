// This config holds the fields that should be shown in the request summary action sheet
// TODO: This should be config-driven somehow

export const LEAVE_FIELDS = [
	{
		fieldname: "name",
		label: "شناسه",
		fieldtype: "Data",
	},
	{
		fieldname: "leave_duration_mode",
		label: "نوع مدت مرخصی",
		fieldtype: "Data",
	},
	{
		fieldname: "hourly_date",
		label: "تاریخ مرخصی ساعتی",
		fieldtype: "Date",
	},
	{
		fieldname: "hourly_from_time",
		label: "از ساعت",
		fieldtype: "Time",
	},
	{
		fieldname: "hourly_to_time",
		label: "تا ساعت",
		fieldtype: "Time",
	},
	{
		fieldname: "leave_type",
		label: "نوع مرخصی",
		fieldtype: "Link",
	},
	{
		fieldname: "leave_dates",
		label: "بازه مرخصی",
		fieldtype: "Data",
	},
	{
		fieldname: "half_day",
		label: "نیم‌روز",
		fieldtype: "Check",
	},
	{
		fieldname: "half_day_date",
		label: "تاریخ نیم‌روز",
		fieldtype: "Date",
	},
	{
		fieldname: "total_leave_days",
		label: "تعداد روز مرخصی",
		fieldtype: "Float",
	},
	{
		fieldname: "total_leave_hours",
		label: "کل ساعات مرخصی",
		fieldtype: "Float",
	},
	{
		fieldname: "employee",
		label: "کارمند",
		fieldtype: "Link",
	},
	{
		fieldname: "leave_balance",
		label: "مانده مرخصی",
		fieldtype: "Float",
	},
	{
		fieldname: "status",
		label: "وضعیت",
		fieldtype: "Select",
	},
	{
		fieldname: "description",
		label: "دلیل",
		fieldtype: "Small Text",
	},
]

export const EXPENSE_CLAIM_FIELDS = [
	{
		fieldname: "name",
		label: "ID",
		fieldtype: "Data",
	},
	{
		fieldname: "posting_date",
		label: "Posting Date",
		fieldtype: "Date",
	},
	{
		fieldname: "employee",
		label: "Employee",
		fieldtype: "Link",
	},
	{
		fieldname: "expenses",
		label: "Expenses",
		fieldtype: "Table",
		componentName: "ExpenseItems",
	},
	{
		fieldname: "total_claimed_amount",
		label: "Total Claimed Amount",
		fieldtype: "Currency",
	},
	{
		fieldname: "total_sanctioned_amount",
		label: "Total Sanctioned Amount",
		fieldtype: "Currency",
	},
	{
		fieldname: "total_taxes_and_charges",
		label: "Total Taxes and Charges",
		fieldtype: "Currency",
	},
	{
		fieldname: "total_advance_amount",
		label: "Total Advance Amount",
		fieldtype: "Currency",
	},
	{
		fieldname: "grand_total",
		label: "Grand Total",
		fieldtype: "Currency",
	},
	{
		fieldname: "status",
		label: "Status",
		fieldtype: "Select",
	},
	{
		fieldname: "approval_status",
		label: "Approval Status",
		fieldtype: "Select",
	},
]

export const ATTENDANCE_REQUEST_FIELDS = [
	{
		fieldname: "name",
		label: "شناسه",
		fieldtype: "Data",
	},
	{
		fieldname: "request_mode",
		label: "نوع درخواست",
		fieldtype: "Select",
	},
	{
		fieldname: "review_status",
		label: "وضعیت بررسی",
		fieldtype: "Select",
	},
	{
		fieldname: "requested_log_type",
		label: "نوع ورود/خروج درخواستی",
		fieldtype: "Data",
	},
	{
		fieldname: "requested_time",
		label: "زمان درخواستی",
		fieldtype: "Time",
	},
	{
		fieldname: "reviewed_log_type",
		label: "نوع ورود/خروج تاییدشده",
		fieldtype: "Data",
	},
	{
		fieldname: "reviewed_time",
		label: "زمان تاییدشده",
		fieldtype: "Time",
	},
	{
		fieldname: "employee_checkin",
		label: "لاگ حضور ثبت‌شده",
		fieldtype: "Link",
	},
	{
		fieldname: "review_comment",
		label: "توضیح بررسی",
		fieldtype: "Small Text",
	},
	{
		fieldname: "attendance_dates",
		label: "تاریخ حضور",
		fieldtype: "Data",
	},
	{
		fieldname: "total_attendance_days",
		label: "تعداد روز",
		fieldtype: "Data",
	},
	{
		fieldname: "include_holidays",
		label: "با احتساب تعطیلات",
		fieldtype: "Check",
	},
	{
		fieldname: "shift",
		label: "شیفت",
		fieldtype: "Link",
	},
	{
		fieldname: "reason",
		label: "دلیل",
		fieldtype: "Select",
	},
	{
		fieldname: "employee",
		label: "کارمند",
		fieldtype: "Link",
	},
]

export const COMPLAINT_FIELDS = [
	{
		fieldname: "name",
		label: "شناسه",
		fieldtype: "Data",
	},
	{
		fieldname: "feedback_type",
		label: "نوع بازخورد",
		fieldtype: "Select",
	},
	{
		fieldname: "subject",
		label: "موضوع",
		fieldtype: "Data",
	},
	{
		fieldname: "grievance_type",
		label: "نوع شکایت",
		fieldtype: "Link",
	},
	{
		fieldname: "status",
		label: "وضعیت",
		fieldtype: "Select",
	},
	{
		fieldname: "raised_by",
		label: "کارمند",
		fieldtype: "Link",
	},
	{
		fieldname: "employee_name",
		label: "نام کارمند",
		fieldtype: "Data",
	},
	{
		fieldname: "date",
		label: "تاریخ",
		fieldtype: "Date",
	},
	{
		fieldname: "description",
		label: "شرح شکایت",
		fieldtype: "Text",
	},
	{
		fieldname: "cause_of_grievance",
		label: "علت شکایت",
		fieldtype: "Text",
	},
	{
		fieldname: "resolution_detail",
		label: "پاسخ سرپرست",
		fieldtype: "Small Text",
	},
	{
		fieldname: "resolved_by",
		label: "بررسی‌کننده",
		fieldtype: "Link",
	},
	{
		fieldname: "resolution_date",
		label: "تاریخ رسیدگی",
		fieldtype: "Date",
	},
]

export const SHIFT_FIELDS = [
	{
		fieldname: "name",
		label: "ID",
		fieldtype: "Data",
	},
	{
		fieldname: "shift_type",
		label: "Shift Type",
		fieldtype: "Link",
	},
	{
		fieldname: "shift_timing",
		label: "Shift Timing",
		fieldtype: "Data",
	},
	{
		fieldname: "shift_dates",
		label: "Shift Dates",
		fieldtype: "Data",
	},
	{
		fieldname: "total_shift_days",
		label: "Total Shift Days",
		fieldtype: "Data",
	},
	{
		fieldname: "employee",
		label: "Employee",
		fieldtype: "Link",
	},
]

export const SHIFT_REQUEST_FIELDS = [
	{
		fieldname: "name",
		label: "ID",
		fieldtype: "Data",
	},
	{
		fieldname: "shift_type",
		label: "Shift Type",
		fieldtype: "Link",
	},
	{
		fieldname: "shift_dates",
		label: "Shift Dates",
		fieldtype: "Data",
	},
	{
		fieldname: "total_shift_days",
		label: "Total Shift Days",
		fieldtype: "Data",
	},
	{
		fieldname: "employee",
		label: "Employee",
		fieldtype: "Link",
	},
	{
		fieldname: "status",
		label: "Status",
		fieldtype: "Select",
	},
]

export const EMPLOYEE_CHECKIN_FIELDS = [
	{
		fieldname: "name",
		label: "ID",
		fieldtype: "Data",
	},
	{
		fieldname: "log_type",
		label: "Log Type",
		fieldtype: "Data",
	},
	{
		fieldname: "date",
		label: "Date",
		fieldtype: "Date",
	},
	{
		fieldname: "formatted_time",
		label: "Time",
		fieldtype: "Time",
	},
	{
		fieldname: "formatted_latitude",
		label: "Latitude",
		fieldtype: "Data",
	},
	{
		fieldname: "formatted_longitude",
		label: "Longitude",
		fieldtype: "Data",
	},
	{
		fieldname: "geolocation",
		label: "Geolocation",
		fieldtype: "geolocation",
	},
]
