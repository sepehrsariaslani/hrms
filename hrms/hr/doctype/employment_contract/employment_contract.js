frappe.ui.form.on('Employment Contract', {
	setup(frm) {
		frm.events.set_work_location_query(frm)
	},

	refresh(frm) {
		frm.add_custom_button(__('تنظیم قرارداد کار'), () => {
			frappe.set_route('Form', 'Employment Contract Settings', 'Employment Contract Settings')
		}, __('تنظیمات'))

		frm.events.set_work_location_query(frm)
		if (frm.doc.employee && (!frm.doc.salary_items || !frm.doc.salary_items.length)) {
			frm.events.fetch_employee_defaults(frm)
		}
	},

	employee(frm) {
		if (!frm.doc.employee) return
		frm.events.fetch_employee_defaults(frm)
	},

	start_date(frm) {
		frm.trigger('calculate_duration')
	},

	end_date(frm) {
		frm.trigger('calculate_duration')
		if (frm.doc.employee && (!frm.doc.salary_items || !frm.doc.salary_items.length)) {
			frm.events.fetch_employee_defaults(frm)
		}
	},

	calculate_duration(frm) {
		if (!frm.doc.start_date || !frm.doc.end_date) {
			frm.set_value('duration_months', 0)
			return
		}

		const start = frappe.datetime.str_to_obj(frm.doc.start_date)
		const end = frappe.datetime.str_to_obj(frm.doc.end_date)

		if (end < start) {
			frm.set_value('duration_months', 0)
			return
		}

		let months = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth())
		if (end.getDate() < start.getDate()) months -= 1
		if (months === 0 && end >= start) months = 1
		frm.set_value('duration_months', Math.max(months, 0))
	},

	set_work_location_query(frm) {
		let allowed_branches = []
		frappe.call({
			method: 'hrms.api.employment_contract.get_contract_settings_defaults',
			callback: function (r) {
				const workplaces = r.message?.workplaces || []
				allowed_branches = workplaces.map((row) => row.branch).filter(Boolean)
				frm.set_query('branch', 'work_locations', function () {
					if (!allowed_branches.length) return {}
					return {
						filters: {
							name: ['in', allowed_branches]
						}
					}
				})
			}
		})
	},

	fetch_employee_defaults(frm) {
		frappe.call({
			method: 'hrms.api.employment_contract.get_employee_contract_defaults',
			args: {
				employee: frm.doc.employee,
				start_date: frm.doc.start_date || frappe.datetime.nowdate()
			},
			callback: function (r) {
				if (!r.message) return
				const data = r.message
				frm.set_value({
					employee_name: data.employee_name,
					company: data.company,
					designation: data.designation,
					department: data.department,
					branch: data.branch,
					employee_phone: data.employee_phone,
					employee_address: data.employee_address,
					national_id: data.national_id,
					id_number: data.id_number,
					id_issue_place: data.id_issue_place,
					father_name: data.father_name,
					employee_bank_name: data.employee_bank_name,
					employee_bank_account: data.employee_bank_account,
					employee_iban: data.employee_iban
				})

				const components = data.payroll_components || []
				const rows = []
				for (const item of components) {
					const amount31 = flt(item.amount_31_days || 0)
					const amount30 = flt(item.amount_30_days || 0)
					if (!item.label) continue
					if (amount31 <= 0 && amount30 <= 0) continue
					rows.push({
						salary_component_label: item.label,
						amount_31_days: amount31,
						amount_30_days: amount30,
						remarks: item.remarks || ''
					})
				}
				frm.set_value('salary_items', rows)
			}
		})
	}
})
