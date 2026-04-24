// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Weekly Shift Plan", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === "Approved") {
			frm.set_intro(__("This weekly plan is approved and linked shift assignments are generated."), "green");
		}
	},
});
