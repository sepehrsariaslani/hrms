frappe.ui.form.on("Salary Slip", {
	refresh(frm) {
		frm.add_custom_button(__("به‌روزرسانی مانده حساب کارمند"), () => {
			frm.call("update_employee_financial_summary").then(() => frm.reload_doc());
		}, __("حسابداری"));
		if (frm.doc.docstatus !== 1) return;
		if (frm.doc.journal_entry) {
			frm.add_custom_button(__("مشاهده سند تعهد حقوق"), () => {
				frappe.set_route("Form", "Journal Entry", frm.doc.journal_entry);
			}, __("حسابداری"));
			return;
		}
		frm.add_custom_button(__("ایجاد سند تعهد حقوق"), () => {
			frappe.confirm(__("این عملیات فقط بدهی حقوق کارمند را ثبت می‌کند و پرداختی انجام نمی‌دهد. اگر فیش از ثبت حقوق و دستمزد آمده باشد، در ثبت گروهی دوباره منظور نمی‌شود."), () => {
				frm.call("make_individual_accrual_journal_entry").then((r) => {
					frappe.set_route("Form", "Journal Entry", r.message);
				});
			});
		}, __("حسابداری"));
	},
});
