frappe.listview_settings["Salary Slip"] = {
	add_fields: ["salary_accrual_status", "journal_entry"],
	get_indicator(doc) {
		if (doc.salary_accrual_status === "تعهد ثبت شد") {
			return [__("تعهد ثبت شد"), "green", "salary_accrual_status,=,تعهد ثبت شد"];
		}
		if (doc.docstatus === 0) return [__("پیش‌نویس"), "orange", "docstatus,=,0"];
		if (doc.docstatus === 2) return [__("لغو شده"), "red", "docstatus,=,2"];
		return [__("ارسال شده"), "blue", "docstatus,=,1"];
	},
	onload(listview) {
		listview.page.add_action_item(__("رفرش گروهی از حضور و غیاب"), () => {
			const slips = listview.get_checked_items().map((item) => item.name);
			if (!slips.length) {
				frappe.msgprint(__("حداقل یک فیش حقوقی را انتخاب کنید."));
				return;
			}
			frappe.confirm(
				__("فقط فیش‌های پیش‌نویس انتخاب‌شده از حضور و غیاب رفرش می‌شوند. فیش‌های ارسال‌شده و لغوشده نادیده گرفته می‌شوند."),
				() => frappe.call({
					method: "hrms.payroll.doctype.salary_slip.salary_slip.bulk_refresh_from_smart_attendance",
					args: { salary_slips: slips },
					freeze: true,
					freeze_message: __("در حال رفرش فیش‌های حقوقی"),
					callback: (r) => {
						const result = r.message || {};
						const errors = result.errors || [];
						const details = errors.length
							? `<br><br>${errors.map((item) => `${frappe.utils.escape_html(item.salary_slip)}: ${frappe.utils.escape_html(item.error)}`).join("<br>")}`
							: "";
						frappe.msgprint({
							title: __("نتیجه رفرش گروهی"),
							message: __("{0} فیش رفرش شد؛ {1} فیش نادیده گرفته شد؛ {2} خطا داشت.", [
								(result.refreshed || []).length,
								(result.skipped || []).length,
								errors.length,
							]) + details,
							indicator: errors.length ? "orange" : "green",
						});
						listview.refresh();
					},
				}),
			);
		});

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
