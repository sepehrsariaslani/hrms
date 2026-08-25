frappe.pages["attendance-device-database"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("پایگاه داده سیستم های حضور و غیاب"),
		single_column: true,
	});
	new hrms.AttendanceDeviceDatabasePage(page, wrapper);
};

frappe.provide("hrms");

hrms.AttendanceDeviceDatabasePage = class AttendanceDeviceDatabasePage {
	constructor(page, wrapper) {
		this.page = page;
		this.wrapper = $(wrapper);
		this.lastArgs = null;
		this.lastJobToken = "";
		this.pollTimer = null;
		this.render();
	}

	render() {
		const body = $(`
			<div class="attendance-device-db-page">
				<div class="attendance-device-db-card">
					<div class="attendance-device-db-header">
						<h3>${__("گزارش دستگاه و کارمندان")}</h3>
						<p>${__("از همان اتصال صفحه درون یابی استفاده می‌شود. ابتدا پیش‌نمایش بگیرید.")}</p>
					</div>
					<div class="attendance-device-db-fields"></div>
					<div class="attendance-device-db-actions">
						<button class="btn btn-primary btn-preview">${__("دریافت گزارش")}</button>
						<button class="btn btn-default btn-download" disabled>${__("دانلود CSV")}</button>
					</div>
				</div>
				<div class="attendance-device-db-card">
					<div class="attendance-device-db-summary"></div>
					<div class="attendance-device-db-table-wrap">
						<table class="attendance-device-db-table">
							<thead></thead>
							<tbody></tbody>
						</table>
					</div>
				</div>
			</div>
		`).appendTo(this.page.main);

		this.$fields = body.find(".attendance-device-db-fields");
		this.$summary = body.find(".attendance-device-db-summary");
		this.$thead = body.find(".attendance-device-db-table thead");
		this.$tbody = body.find(".attendance-device-db-table tbody");
		this.$btnPreview = body.find(".btn-preview");
		this.$btnDownload = body.find(".btn-download");

		this.fields = {
			source_date_from: frappe.ui.form.make_control({
				df: {
					fieldname: "source_date_from",
					fieldtype: "Data",
					label: __("از تاریخ (جلالی)"),
					placeholder: "1405/02/01",
				},
				parent: this.$fields,
				render_input: true,
			}),
			source_date_to: frappe.ui.form.make_control({
				df: {
					fieldname: "source_date_to",
					fieldtype: "Data",
					label: __("تا تاریخ (جلالی)"),
					placeholder: "1405/02/30",
				},
				parent: this.$fields,
				render_input: true,
			}),
			max_source_rows: frappe.ui.form.make_control({
				df: {
					fieldname: "max_source_rows",
					fieldtype: "Int",
					label: __("حداکثر رکورد منبع"),
					default: 2000,
				},
				parent: this.$fields,
				render_input: true,
			}),
		};

		this.$btnPreview.on("click", () => this.runPreview());
		this.$btnDownload.on("click", () => this.downloadCsv());
	}

	getArgs() {
		return {
			source_date_from: this.fields.source_date_from.get_value() || "",
			source_date_to: this.fields.source_date_to.get_value() || "",
			max_source_rows: this.fields.max_source_rows.get_value() || 0,
		};
	}

	runPreview() {
		this.clearPollTimer();
		this.$btnDownload.prop("disabled", true);
		const args = this.getArgs();
		frappe.call({
			method: "hrms.hr.page.attendance_device_database.attendance_device_database.enqueue_preview_device_database",
			args,
			freeze: true,
			freeze_message: __("در حال ثبت درخواست گزارش دستگاه‌ها..."),
			callback: (r) => {
				const job = r.message || {};
				this.lastArgs = args;
				this.lastJobToken = job.job_token || "";
				this.renderSummary(
					{
						connection: {
							connection_message: __("در صف اجرا"),
							connection_mode: __("background"),
						},
						source_device_count: 0,
						mapped_device_count: 0,
					},
					[]
				);
				this.renderTable([]);
				this.pollJob(job.job_token);
			},
		});
	}

	clearPollTimer() {
		if (this.pollTimer) {
			clearTimeout(this.pollTimer);
			this.pollTimer = null;
		}
	}

	pollJob(jobToken) {
		if (!jobToken) {
			frappe.msgprint(__("شناسه کار نامعتبر است."));
			return;
		}

		const poll = () => {
			frappe.call({
				method: "hrms.hr.page.attendance_device_database.attendance_device_database.get_device_database_job_status",
				args: { job_token: jobToken },
				callback: (r) => {
					const payload = r.message || {};
					const status = String(payload.status || "").toLowerCase();
					if (status === "finished") {
						this.clearPollTimer();
						const data = payload.result || {};
						const rows = data.rows || [];
						this.renderSummary(data, rows);
						this.renderTable(rows);
						this.$btnDownload.prop("disabled", false);
						return;
					}
					if (status === "failed" || status === "canceled") {
						this.clearPollTimer();
						const errorText = payload.error || __("گزارش در پس‌زمینه با خطا متوقف شد.");
						frappe.msgprint({
							title: __("خطا"),
							message: `<pre style="white-space: pre-wrap;">${frappe.utils.escape_html(String(errorText))}</pre>`,
							indicator: "red",
						});
						return;
					}
					this.pollTimer = setTimeout(poll, 2000);
				},
				error: () => {
					this.pollTimer = setTimeout(poll, 3000);
				},
			});
		};

		poll();
	}

	normalizeCode(value) {
		return String(value || "").trim().toUpperCase();
	}

	normalizeName(value) {
		return String(value || "").trim().toUpperCase();
	}

	isMatchedRow(row) {
		const sourceEmployeeCode = this.normalizeCode(row.source_employee_code || row.device_code);
		const systemEmployeeCode = this.normalizeCode(row.employee);
		const sourceBranchCode = this.normalizeCode(row.source_branch_code);
		const systemBranchCode = this.normalizeCode(row.system_branch_code || row.device_identifier);
		const sourceName = this.normalizeName(row.source_full_name);
		const systemName = this.normalizeName(row.employee_name);

		const employeeCodeMatch =
			sourceEmployeeCode && systemEmployeeCode && sourceEmployeeCode === systemEmployeeCode;
		const branchMatch = sourceBranchCode && systemBranchCode && sourceBranchCode === systemBranchCode;
		const nameMatch = !sourceName || !systemName || sourceName === systemName;

		return Boolean(employeeCodeMatch && branchMatch && nameMatch);
	}

	renderSummary(data, rows) {
		const connection = data.connection || {};
		const sourceOnlyCount = rows.filter((row) => (row.mapping_source || "") === "missing_employee").length;
		const systemOnlyCount = rows.filter((row) => {
			const mappingSource = row.mapping_source || "";
			if (mappingSource === "employee_missing_device_code") {
				return true;
			}
			const sourceHits = Number.parseInt(row.source_hits, 10) || 0;
			if ((mappingSource === "custom_table" || mappingSource === "legacy_field") && sourceHits === 0) {
				return true;
			}
			return false;
		}).length;
		const matchedCount = rows.filter((row) => this.isMatchedRow(row)).length;

		this.$summary.html(`
			<div class="attendance-device-db-kpis">
				<div><b>${__("وضعیت اتصال")}:</b> ${frappe.utils.escape_html(connection.connection_message || "-")}</div>
				<div><b>${__("حالت")}:</b> ${frappe.utils.escape_html(connection.connection_mode || "-")}</div>
				<div><b>${__("تعداد دستگاه منبع")}:</b> ${data.source_device_count || 0}</div>
				<div><b>${__("تعداد دستگاه در گزارش")}:</b> ${data.mapped_device_count || 0}</div>
				<div><b>${__("ردیف تطبیق‌شده (سبز)")}:</b> ${matchedCount}</div>
				<div><b>${__("فقط در دستگاه (در سیستم نیست)")}:</b> ${sourceOnlyCount}</div>
				<div><b>${__("فقط در سیستم (در دستگاه نیست)")}:</b> ${systemOnlyCount}</div>
				<div><b>${__("تعداد ردیف")}:</b> ${rows.length}</div>
			</div>
		`);
	}

	renderTable(rows) {
		const columns = [
			["source_employee_code", __("کد کارمند (از دستگاه)")],
			["source_branch_code", __("کد شعبه (از دستگاه)")],
			["source_full_name", __("نام در دستگاه")],
			["employee", __("کد کارمند (HRMS)")],
			["employee_name", __("نام کارمند (سیستم)")],
			["system_branch_code", __("کد شعبه (سیستم)")],
			["system_branch_name", __("نام شعبه (سیستم)")],
			["mapping_source", __("منبع نگاشت")],
			["source_machine_no", __("شماره دستگاه منبع")],
			["source_hits", __("تعداد رکورد منبع")],
			["source_database", __("دیتابیس منبع")],
		];
		const sourceColumns = new Set([
			"source_employee_code",
			"source_branch_code",
			"source_full_name",
			"source_machine_no",
			"source_database",
			"source_hits",
		]);

		this.$thead.html(
			`<tr>${columns
				.map(([field, label]) => {
					const cls = sourceColumns.has(field) ? "col-source" : "col-system";
					return `<th class="${cls}">${frappe.utils.escape_html(label)}</th>`;
				})
				.join("")}</tr>`
		);

		if (!rows.length) {
			this.$tbody.html(`<tr><td colspan="${columns.length}">${__("داده‌ای برای نمایش پیدا نشد.")}</td></tr>`);
			return;
		}

		const mappingSourceLabel = {
			custom_table: __("نگاشت سفارشی"),
			legacy_field: __("فیلد قدیمی"),
			not_mapped: __("در دستگاه هست، نگاشت ندارد"),
			missing_employee: __("در دستگاه هست، کارمند در سیستم نیست"),
			employee_missing_device_code: __("در سیستم هست، کد/نگاشت دستگاه ندارد"),
		};

		this.$tbody.html(
			rows
				.map((row) => {
					const rowClass = this.isMatchedRow(row) ? "row-full-match" : "";

					return `<tr class="${rowClass}">${columns
						.map(([field]) => {
							let value = row[field] || "";
							if (field === "source_employee_code") {
								value = value || row.device_code || "";
							}
							if (field === "system_branch_code") {
								value = value || row.device_identifier || "";
							}
							if (field === "system_branch_name") {
								value = value || row.device_location || row.device_company || "";
							}
							if (field === "mapping_source") {
								value = mappingSourceLabel[value] || value;
							}
							const cls = sourceColumns.has(field) ? "col-source" : "col-system";
							return `<td class="${cls}">${frappe.utils.escape_html(String(value))}</td>`;
						})
						.join("")}</tr>`;
				})
				.join("")
		);
	}

	downloadCsv() {
		if (!this.lastArgs) {
			frappe.msgprint(__("ابتدا یک گزارش بگیرید."));
			return;
		}
		const args = Object.assign({}, this.lastArgs);
		if (this.lastJobToken) {
			args.job_token = this.lastJobToken;
		}
		const query = $.param(args);
		window.open(
			`/api/method/hrms.hr.page.attendance_device_database.attendance_device_database.download_device_database_csv?${query}`,
			"_blank"
		);
	}
};
