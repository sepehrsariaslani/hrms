// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee", {
	refresh: function (frm) {
		frm.set_query("payroll_cost_center", function () {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0,
				},
			};
		});

		// filter advance account based on salary currency
		if (frm.doc.salary_currency) {
			frm.set_query("employee_advance_account", function () {
				return {
					filters: {
						root_type: "Asset",
						is_group: 0,
						company: frm.doc.company,
						account_currency: frm.doc.salary_currency,
						account_type: "Receivable",
					},
				};
			});
		}
		frm.set_df_property("holiday_list", "hidden", 1);
	},
	validate(frm) {
		normalize_employee_compensation_inputs(frm);
	},
	insurance_start_date(frm) {
		if (!insuranceSyncInProgress) {
			recalculate_iran_employee_compensation(frm);
		}
	},
	insurance_start_date_persian(frm) {
		if (!insuranceSyncInProgress) {
			recalculate_iran_employee_compensation(frm);
		}
	},
	karane(frm) {
		normalize_employee_compensation_inputs(frm, "karane");
	},
	technical_allowance_monthly(frm) {
		normalize_employee_compensation_inputs(frm, "technical_allowance_monthly");
	},

	date_of_birth(frm) {
		frm.call({
			method: "hrms.overrides.employee_master.get_retirement_date",
			args: {
				date_of_birth: frm.doc.date_of_birth,
			},
		}).then((r) => {
			if (r && r.message) frm.set_value("date_of_retirement", r.message);
		});
	},
	after_save(frm) {
		recalculate_iran_employee_compensation(frm);
	},
});

const PERSIAN_DIGIT_MAP = {
	"۰": "0",
	"۱": "1",
	"۲": "2",
	"۳": "3",
	"۴": "4",
	"۵": "5",
	"۶": "6",
	"۷": "7",
	"۸": "8",
	"۹": "9",
};

const ARABIC_DIGIT_MAP = {
	"٠": "0",
	"١": "1",
	"٢": "2",
	"٣": "3",
	"٤": "4",
	"٥": "5",
	"٦": "6",
	"٧": "7",
	"٨": "8",
	"٩": "9",
};

function normalize_employee_compensation_inputs(frm, target_fieldname = null) {
	const fieldnames = target_fieldname ? [target_fieldname] : ["karane", "technical_allowance_monthly"];
	for (const fieldname of fieldnames) {
		const raw_input = get_form_field_raw_input(frm, fieldname);
		if (typeof raw_input !== "string") continue;
		const normalized = normalize_localized_number_input(raw_input);
		if (!normalized) continue;
		const parsed = flt(normalized);
		if (!Number.isFinite(parsed)) continue;
		if (flt(frm.doc[fieldname]) !== parsed) {
			frm.doc[fieldname] = parsed;
			frm.refresh_field(fieldname);
		}
	}
}

function get_form_field_raw_input(frm, fieldname) {
	const field = frm.fields_dict?.[fieldname];
	if (!field || !field.$input) return null;
	return field.$input.val();
}

function normalize_localized_number_input(value) {
	let text = value || "";
	for (const [source, target] of Object.entries(PERSIAN_DIGIT_MAP)) {
		text = text.split(source).join(target);
	}
	for (const [source, target] of Object.entries(ARABIC_DIGIT_MAP)) {
		text = text.split(source).join(target);
	}
	return text
		.replace(/[٬،]/g, ",")
		.replace(/٫/g, ".")
		.replace(/[\u200e\u200f\u200c\s]/g, "")
		.trim();
}

let insuranceSyncInProgress = false;

function recalculate_iran_employee_compensation(frm) {
	if (!frm.doc.name || !frm.doc.company || frm.is_new()) return;
	if (insuranceSyncInProgress) return;

	insuranceSyncInProgress = true;
	const insurance_start_date = normalizeInsuranceStartDateForSync(
		frm.doc.insurance_start_date || frm.doc.insurance_start_date_persian
	);
	const finish = () => {
		insuranceSyncInProgress = false;
	};

	frappe.call({
		method: "hrms.regional.iran.utils.recalculate_iran_employee_compensation_from_client",
		args: {
			employee: frm.doc.name,
			insurance_start_date,
		},
		callback: function (res) {
			const data = res && res.message;
			if (data) {
				frm.set_value({
					insurance_start_date: data.insurance_start_date || frm.doc.insurance_start_date,
					insurance_service_years: data.insurance_service_years || 0,
					employee_seniority_daily_base: data.employee_seniority_daily_base || 0,
					employee_seniority_monthly_base: data.employee_seniority_monthly_base || 0,
					employee_salary_type: data.employee_salary_type || frm.doc.employee_salary_type,
					daily_pay: data.daily_pay || 0,
					monthly_base_pay: data.monthly_base_pay || 0,
					base_pay: data.base_pay || 0,
					overtime_rate: data.overtime_rate || 0,
					absence_deduction: data.absence_deduction || 0,
					housing_allowance: data.housing_allowance || 0,
					grocery_allowance: data.grocery_allowance || 0,
					marriage_allowance: data.marriage_allowance || 0,
					child_allowance_per_child: data.child_allowance_per_child || 0,
					child_allowance: data.child_allowance || 0,
					total_receivable: data.total_receivable || 0,
				});
			}
			finish();
		},
		error: finish,
	});
}

function normalizeInsuranceStartDateForSync(rawValue) {
	if (!rawValue) return null;
	const text = String(rawValue).trim();
	if (!text) return null;

	const normalized = text.replace(/-/g, "/");
	const yearText = normalized.split("/")[0] || "";
	const year = cint(yearText);
	if (year >= 1300 && typeof window.persianToGregorian === "function") {
		const converted = window.persianToGregorian(normalized);
		if (converted) return converted.split(" ")[0];
	}

	return text;
}
