frappe.pages["attendance-interpolation"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("درون یابی حضور و غیاب"),
		single_column: true,
	});

	new hrms.AttendanceInterpolationPage(page, wrapper);
};

frappe.provide("hrms");

hrms.AttendanceInterpolationPage = class AttendanceInterpolationPage {
	constructor(page, wrapper) {
		this.page = page;
		this.wrapper = $(wrapper);
		this.previewData = null;
		this.importEnabled = true;
		this.currentJob = null;
		this.pollTimer = null;
		this.render();
		this.loadDefaults();
	}

	render() {
		const body = $(`
			<div class="attendance-interpolation-page">
				<div class="attendance-interpolation-card">
					<div class="attendance-interpolation-header">
						<h3>${__("تنظیمات اجرای سریع")}</h3>
						<p>${__("در این مرحله فقط پیش‌نمایش و بررسی جدول انجام می‌شود.")}</p>
					</div>
					<div class="attendance-interpolation-fields"></div>
					<div class="attendance-interpolation-actions">
						<button class="btn btn-default btn-open-settings">${__("باز کردن تنظیمات")}</button>
						<button class="btn btn-primary btn-preview">${__("پیش‌نمایش")}</button>
						<button class="btn btn-danger btn-import" disabled>${__("ایمپورت نهایی")}</button>
					</div>
				</div>
				<div class="attendance-interpolation-card">
					<h4>${__("خروجی")}</h4>
					<pre class="attendance-interpolation-output"></pre>
					<div class="attendance-interpolation-table-container"></div>
				</div>
			</div>
		`).appendTo(this.page.main);

		this.$fields = body.find(".attendance-interpolation-fields");
		this.$output = body.find(".attendance-interpolation-output");
		this.$tableContainer = body.find(".attendance-interpolation-table-container");
		this.$btnPreview = body.find(".btn-preview");
		this.$btnImport = body.find(".btn-import");

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
					placeholder: "1405/02/01",
				},
				parent: this.$fields,
				render_input: true,
			}),
			max_source_rows: frappe.ui.form.make_control({
				df: {
					fieldname: "max_source_rows",
					fieldtype: "Int",
					label: __("حداکثر رکورد"),
					default: 2000,
				},
				parent: this.$fields,
				render_input: true,
			}),
			preview_limit: frappe.ui.form.make_control({
				df: {
					fieldname: "preview_limit",
					fieldtype: "Int",
					label: __("تعداد پیش‌نمایش"),
					default: 30,
				},
				parent: this.$fields,
				render_input: true,
			}),
		};

		body.find(".btn-open-settings").on("click", () => {
			frappe.set_route("Form", "Attendance Interpolation Settings", "Attendance Interpolation Settings");
		});
		this.$btnPreview.on("click", () => this.runPreview());
		this.$btnImport.on("click", () => this.runImport());
	}

	loadDefaults() {
		frappe.call({
			method: "hrms.hr.page.attendance_interpolation.attendance_interpolation.get_interpolation_settings",
			freeze: true,
			freeze_message: __("در حال دریافت تنظیمات..."),
			callback: (r) => {
				const data = r.message || {};
				this.fields.source_date_from.set_value(data.source_date_from || "");
				this.fields.source_date_to.set_value(data.source_date_to || "");
				this.fields.max_source_rows.set_value(data.max_source_rows || 2000);
				this.fields.preview_limit.set_value(data.preview_limit || 30);
				this.importEnabled = Boolean(data.enabled);
				this.printOutput(data, __("تنظیمات بارگذاری شد"));
			},
		});
	}

	getArgs() {
		return {
			source_date_from: this.fields.source_date_from.get_value() || "",
			source_date_to: this.fields.source_date_to.get_value() || "",
			max_source_rows: this.fields.max_source_rows.get_value() || 0,
			preview_limit: this.fields.preview_limit.get_value() || 30,
		};
	}

	runPreview() {
		this.clearPollTimer();
		this.$btnImport.prop("disabled", true);
		frappe.call({
			method: "hrms.hr.page.attendance_interpolation.attendance_interpolation.enqueue_preview_interpolation",
			args: this.getArgs(),
			freeze: true,
			freeze_message: __("در حال ثبت درخواست پیش‌نمایش..."),
			callback: (r) => {
				const job = r.message || {};
				this.currentJob = job;
				this.printOutput(job, __("پیش‌نمایش در صف قرار گرفت"));
				this.pollJob(job.job_token, {
					onSuccess: (result) => {
						this.previewData = result;
						this.printOutput(result, __("پیش‌نمایش با موفقیت انجام شد"));
						this.renderPreviewTable(result);
						this.$btnImport.prop("disabled", !this.importEnabled);
					},
				});
			},
		});
	}

	runImport() {
		if (!this.importEnabled) {
			frappe.msgprint({
				title: __("غیرفعال"),
				message: __("ایمپورت فعلا غیرفعال است. فعلا فقط پیش‌نمایش و بررسی جدول انجام می‌شود."),
				indicator: "orange",
			});
			return;
		}

		if (!this.previewData) {
			frappe.msgprint({
				title: __("نیاز به پیش‌نمایش"),
				message: __("ابتدا یک پیش‌نمایش بگیرید."),
				indicator: "orange",
			});
			return;
		}

		frappe.confirm(
			__("آیا از ایمپورت نهایی به Employee Checkin مطمئن هستید؟"),
			() => {
				this.clearPollTimer();
				const args = this.getArgs();
				args.confirmed = 1;
				frappe.call({
					method: "hrms.hr.page.attendance_interpolation.attendance_interpolation.enqueue_import_interpolation",
					args,
					freeze: true,
					freeze_message: __("در حال ثبت درخواست ایمپورت..."),
					callback: (r) => {
						const job = r.message || {};
						this.currentJob = job;
						this.printOutput(job, __("ایمپورت در صف قرار گرفت"));
						this.pollJob(job.job_token, {
							onSuccess: (result) => {
								this.printOutput(result, __("ایمپورت با موفقیت انجام شد"));
							},
						});
					},
				});
			}
		);
	}

	clearPollTimer() {
		if (this.pollTimer) {
			clearTimeout(this.pollTimer);
			this.pollTimer = null;
		}
	}

	pollJob(jobToken, { onSuccess }) {
		if (!jobToken) {
			frappe.msgprint(__("شناسه کار نامعتبر است."));
			return;
		}

		const poll = () => {
			frappe.call({
				method: "hrms.hr.page.attendance_interpolation.attendance_interpolation.get_interpolation_job_status",
				args: { job_token: jobToken },
				callback: (r) => {
					const statusPayload = r.message || {};
					const status = String(statusPayload.status || "").toLowerCase();
					if (status === "finished") {
						this.clearPollTimer();
						onSuccess(statusPayload.result || {});
						return;
					}
					if (status === "failed" || status === "canceled") {
						this.clearPollTimer();
						const errorText = statusPayload.error || __("اجرای پس‌زمینه با خطا متوقف شد.");
						this.printOutput(statusPayload, __("خطا در اجرای پس‌زمینه"));
						frappe.msgprint({
							title: __("خطا"),
							message: `<pre style="white-space: pre-wrap;">${frappe.utils.escape_html(String(errorText))}</pre>`,
							indicator: "red",
						});
						return;
					}

					this.printOutput(statusPayload, __("در حال اجرا در پس‌زمینه"));
					this.pollTimer = setTimeout(poll, 2000);
				},
				error: () => {
					this.pollTimer = setTimeout(poll, 3000);
				},
			});
		};

		poll();
	}

	printOutput(data, title) {
		const payload = {
			title,
			timestamp: frappe.datetime.now_datetime(),
			data,
		};
		this.$output.text(JSON.stringify(payload, null, 2));
	}

	renderPreviewTable(data) {
		const rows = (data && (data.preview_rows || data.sample_results)) || [];
		if (!rows.length) {
			this.$tableContainer.html(
				`<div class="attendance-interpolation-empty">${__("برای این بازه رکورد قابل نمایش پیدا نشد.")}</div>`
			);
			return;
		}

		const statusLabel = {
			would_create: __("جدید (قابل ایجاد)"),
			new: __("ایجاد شد"),
			existing: __("تکراری/موجود"),
			skipped_manual_override: __("نادیده گرفته شد (تغییر/حذف دستی)"),
			missing_employee: __("بدون کارمند"),
			invalid_datetime: __("تاریخ/ساعت نامعتبر"),
			error: __("خطا"),
		};

		const columns = [
			["row", __("ردیف")],
			["status", __("وضعیت")],
			["employee", __("کد کارمند")],
			["employee_name", __("نام کارمند")],
			["log_type", __("ورود/خروج")],
			["time", __("زمان میلادی")],
			["source_date", __("تاریخ شمسی")],
			["source_time", __("ساعت منبع")],
			["source_person_id", __("Person ID")],
			["source_employee_code", __("Employee Code")],
			["source_full_name", __("نام منبع")],
			["source_database", __("دیتابیس منبع")],
			["source_table", __("جدول منبع")],
			["device_id", __("دستگاه")],
			["match_rule", __("روش تطبیق")],
			["error", __("خطا")],
		];

		const headerHtml = columns.map(([, label]) => `<th>${frappe.utils.escape_html(label)}</th>`).join("");
		const bodyHtml = rows
			.map((row) => {
				return `<tr>${columns
					.map(([field]) => {
						let value = row[field] || "";
						if (field === "status") {
							value = statusLabel[value] || value || "-";
						}
						return `<td>${frappe.utils.escape_html(String(value))}</td>`;
					})
					.join("")}</tr>`;
			})
			.join("");

		this.$tableContainer.html(`
			<div class="attendance-interpolation-table-title">
				${__("جدول پیش‌نمایش رکوردها")} (${rows.length})
			</div>
			<div class="attendance-interpolation-table-wrap">
				<table class="attendance-interpolation-table">
					<thead><tr>${headerHtml}</tr></thead>
					<tbody>${bodyHtml}</tbody>
				</table>
			</div>
		`);
	}
};
