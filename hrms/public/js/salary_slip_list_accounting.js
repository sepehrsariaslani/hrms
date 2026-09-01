frappe.listview_settings["Salary Slip"] = {
	onload(listview) {
		listview.page.add_action_item(__("ایجاد اسناد تعهد حقوق"), () => {
			const slips = listview.get_checked_items().map((item) => item.name);
			if (!slips.length) {
				frappe.msgprint(__("حداقل یک فیش حقوقی را انتخاب کنید."));
				return;
			}
			frappe.confirm(
				__("برای هر فیش انتخاب‌شده یک سند تعهد جداگانه ساخته می‌شود. فیش‌های دارای سند، نادیده گرفته می‌شوند."),
				() => frappe.call({
					method: "hrms.payroll.doctype.salary_slip.salary_slip.make_individual_accrual_journal_entries",
					args: { salary_slips: slips },
					freeze: true,
					freeze_message: __("در حال ساخت اسناد تعهد حقوق"),
					callback: (r) => {
						const result = r.message || {};
						frappe.msgprint(__("{0} سند ساخته شد؛ {1} فیش نادیده گرفته شد.", [
							(result.created || []).length,
							(result.skipped || []).length,
						]));
						listview.refresh();
					},
				}),
			);
		});
	},
};
