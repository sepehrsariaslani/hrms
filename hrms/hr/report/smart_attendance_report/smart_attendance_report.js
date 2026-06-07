// Copyright (c) 2024, Iran Utilities
// For license information, please see license.txt

frappe.query_reports["Smart Attendance Report"] = {
    "onload": function (report) {
        report.page.add_inner_button(__("اصلاح و پاکسازی خودکار"), function () {
            const filters = report.get_values();
            frappe.confirm(
                __("خروج‌های ۰۰:۰۰ اصلاح و لاگ‌های تکراری علامت‌گذاری (حساب نشود) شوند؟"),
                function () {
                    call_normalize_midnight(report, filters, function () {
                        call_bulk_cleanup(report, filters);
                    });
                }
            );
        });

        report.page.add_inner_button(__("🖨️ چاپ / PDF"), function () {
            smart_attendance_print_report(report);
        });
    },

    "filters": [
        {
            "fieldname": "company",
            "label": __("شرکت"),
            "fieldtype": "Link",
            "options": "Company",
            "width": 180,
            "on_change": function () {
                const company = frappe.query_report.get_filter_value("company");

                // اگر کارمندی انتخاب شده ولی متعلق به شرکت دیگری است، خالی شود
                frappe.query_report.set_filter_value("employee", "");
                frappe.query_report.set_filter_value("employees", "");
                frappe.query_report.refresh();
            }
        },
        {
            "fieldname": "employee",
            "label": __("کارمند"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 180,
            "get_query": function () {
                const company = frappe.query_report.get_filter_value("company");
                let filters = {};

                if (company) {
                    filters.company = company;
                }

                return {
                    filters: filters
                };
            }
        },
        {
            "fieldname": "employees",
            "label": __("کارمندان (جدا با کاما)"),
            "fieldtype": "Data",
            "width": 200,
            "description": __("چند کارمند با کاما جدا کنید")
        },
        {
            "fieldname": "from_date",
            "label": __("از تاریخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.nowdate(), -30),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("تا تاریخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.nowdate(),
            "reqd": 1
        },
        {
            "fieldname": "only_issues",
            "label": __("فقط روزهای مشکل‌دار"),
            "fieldtype": "Check",
            "default": 0
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {
        // ستون‌های ساعتی که باید به فرمت HH:MM نمایش داده شوند
        const HOUR_COLUMNS = ["standard_hours", "presence_hours", "break_hours", "working_hours", "time_off", "overtime", "holiday_work"];
        if (HOUR_COLUMNS.includes(column.fieldname) && data) {
            let raw = parseFloat(data[column.fieldname] || 0);
            let h = Math.floor(raw);
            let m = Math.round((raw - h) * 60);
            if (m === 60) { h += 1; m = 0; }
            let hhmm = h + ":" + String(m).padStart(2, "0");
            if (column.fieldname === "time_off" && raw > 0) {
                return "<span style='color:red;font-weight:bold'>" + hhmm + "</span>";
            }
            if (column.fieldname === "overtime" && raw > 0) {
                return "<span style='color:green;font-weight:bold'>" + hhmm + "</span>";
            }
            return hhmm;
        }

        value = default_formatter(value, row, column, data);

        if (!data) {
            return value;
        }

        // Color coding for issue flag
        if (column.fieldname === "issue_flag") {
            if (data.issue_flag === "🔴") {
                value = "<span style='color:red;font-size:16px'>🔴</span>";
            } else if (data.issue_flag === "🟡") {
                value = "<span style='color:orange;font-size:16px'>🟡</span>";
            } else if (data.issue_flag === "✅") {
                value = "<span style='color:green;font-size:16px'>✅</span>";
            }
        }

        // Color coding for log status
        if (column.fieldname === "log_status") {
            if (data.log_status && data.log_status.includes("🔴")) {
                value = "<span style='color:red'>" + value + "</span>";
            } else if (data.log_status && data.log_status.includes("🟠")) {
                value = "<span style='color:#ff6600;font-weight:bold'>" + value + "</span>";
            } else if (data.log_status && data.log_status.includes("🟡")) {
                value = "<span style='color:orange'>" + value + "</span>";
            } else if (data.log_status && data.log_status.includes("✅")) {
                value = "<span style='color:green'>" + value + "</span>";
            }

            if (data.can_mark_attendance) {
                const dayAction = `<span onclick="smart_attendance_mark_day('${data.employee}', '${data.work_date}', '${data.attendance_status || ""}')"
                                    style="cursor:pointer;margin-left:6px;" title="ثبت غیبت/مرخصی">🗓️</span>`;
                value = dayAction + value;
            }
        }

        // Make all_logs interactive with edit icons + add icon
        if (column.fieldname === "all_logs") {
            let logParts = [];

            // دکمه افزودن لاگ جدید برای همان روز
            let addIcon = `<span onclick="smart_attendance_add_checkin('${data.employee}', '${data.work_date}', '')"
                                style="cursor:pointer;color:#28a745;font-size:14px;margin-left:6px"
                                title="افزودن لاگ جدید">➕</span>`;

            if (data.all_logs_json && data.all_logs_json.length > 0) {
                for (let log of data.all_logs_json) {
                    let icon = log.log_type === "IN" ? "⬇️" : "⬆️";
                    let editIcon = `<span onclick="smart_attendance_edit_checkin('${log.name}')"
                                          style="cursor:pointer;color:#666;font-size:12px"
                                          title="ویرایش">✏️</span>`;
                    let excludeIcon, logDisplay;
                    if (log.is_excluded) {
                        excludeIcon = `<span onclick="smart_attendance_toggle_excluded('${log.name}', 0)"
                                            style="cursor:pointer;color:#28a745;font-size:12px"
                                            title="حساب شود (برداشتن علامت)">↩️</span>`;
                        logDisplay = `<s style="color:#bbb">${icon}${log.time}</s>`;
                    } else {
                        excludeIcon = `<span onclick="smart_attendance_toggle_excluded('${log.name}', 1)"
                                            style="cursor:pointer;color:#dc3545;font-size:12px"
                                            title="حساب نشود">🚫</span>`;
                        logDisplay = `${icon}${log.time}`;
                    }
                    logParts.push(`${editIcon}${excludeIcon}${logDisplay}`);
                }
            }

            // دکمه ترکیبی پاکسازی نویزی + بازسازی ترتیب
            let fixCleanupIcon = "";
            if (data.all_logs_json && data.all_logs_json.length >= 2) {
                fixCleanupIcon = `<span onclick="smart_attendance_fix_and_cleanup_day('${data.employee}', '${data.work_date}')"
                                      style="cursor:pointer;color:#6f42c1;font-size:12px;margin-left:6px"
                                      title="پاکسازی لاگ نویزی + بازسازی ترتیب">🔧</span>`;
            }

            value = addIcon + fixCleanupIcon + (logParts.length ? logParts.join(" | ") : "<span style='color:#999'>بدون لاگ</span>");
        }

        // Make actual_start (ورود) clickable with edit icon
        if (column.fieldname === "actual_start") {
            let time_display = data.actual_start || "--:--";
            let link_html = "";
            let edit_html = "";

            if (data.actual_start && data.first_in_name) {
                link_html = `<a href="/app/employee-checkin/${data.first_in_name}" style="color:#007bff;">
                               ${data.actual_start}
                            </a>`;
                edit_html = `<span class="edit-checkin-btn"
                               onclick="smart_attendance_edit_checkin('${data.first_in_name}')"
                               style="cursor:pointer;margin-right:5px;color:#666;"
                               title="ویرایش">✏️</span>`;
            } else {
                link_html = `<span style="color:#999;">${time_display}</span>`;
                edit_html = `<span class="add-checkin-btn"
                               onclick="smart_attendance_add_checkin('${data.employee}', '${data.work_date}', 'IN')"
                               style="cursor:pointer;margin-right:5px;color:#28a745;"
                               title="افزودن ورود">➕</span>`;
            }

            value = edit_html + link_html;
        }

        // Make actual_end (خروج) clickable with edit icon
        if (column.fieldname === "actual_end") {
            let time_display = data.actual_end || "--:--";
            let link_html = "";
            let edit_html = "";

            if (data.actual_end && data.last_out_name) {
                link_html = `<a href="/app/employee-checkin/${data.last_out_name}" style="color:#007bff;">
                               ${data.actual_end}
                            </a>`;
                edit_html = `<span class="edit-checkin-btn"
                               onclick="smart_attendance_edit_checkin('${data.last_out_name}')"
                               style="cursor:pointer;margin-right:5px;color:#666;"
                               title="ویرایش">✏️</span>`;
            } else {
                link_html = `<span style="color:#999;">${time_display}</span>`;
                edit_html = `<span class="add-checkin-btn"
                               onclick="smart_attendance_add_checkin('${data.employee}', '${data.work_date}', 'OUT')"
                               style="cursor:pointer;margin-right:5px;color:#dc3545;"
                               title="افزودن خروج">➕</span>`;
            }

            value = edit_html + link_html;
        }

        return value;
    }
};

function call_normalize_midnight(report, filters, callback) {
    frappe.call({
        method: "hrms.hr.report.smart_attendance_report.smart_attendance_report.normalize_midnight_checkout_logs",
        args: {
            from_date: filters.from_date,
            to_date: filters.to_date,
            employee: filters.employee,
            employees: filters.employees,
            company: filters.company
        },
        callback: function (r) {
            if (r.exc && String(r.exc).includes("has no attribute 'normalize_midnight_checkout_logs'")) {
                frappe.msgprint(__("سرور هنوز نسخه جدید را لود نکرده. لطفاً bench restart و clear-cache انجام شود."));
                return;
            }

            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: r.message.message || __("اصلاح انجام شد"),
                    indicator: "green"
                });
                if (callback) callback();
                else report.refresh();
            }
        }
    });
}

function call_bulk_cleanup(report, filters) {
    frappe.call({
        method: "hrms.hr.report.smart_attendance_report.smart_attendance_report.cleanup_noisy_logs_bulk",
        args: {
            from_date: filters.from_date,
            to_date: filters.to_date,
            employee: filters.employee,
            employees: filters.employees,
            company: filters.company
        },
        callback: function (r) {
            if (r.exc && String(r.exc).includes("has no attribute 'cleanup_noisy_logs_bulk'")) {
                frappe.msgprint(__("سرور هنوز نسخه جدید را لود نکرده. لطفاً bench restart و clear-cache انجام شود."));
                return;
            }

            if (r.message && r.message.success) {
                const msg = __("روز پردازش‌شده: {0} | روز اصلاح‌شده: {1} | لاگ علامت‌گذاری‌شده: {2}")
                    .replace("{0}", r.message.processed_days || 0)
                    .replace("{1}", r.message.affected_days || 0)
                    .replace("{2}", r.message.flagged_count || r.message.deleted_count || 0);
                frappe.show_alert({
                    message: msg,
                    indicator: "green"
                });
                report.refresh();
            }
        }
    });
}

// Global function for adding checkin
window.smart_attendance_add_checkin = function (employee, date, log_type) {
    let title = __("ثبت لاگ");
    let default_time = "08:00:00";
    let default_log_type = log_type || "IN";

    if (log_type === "OUT") {
        default_time = "17:00:00";
    }

    let dialog = new frappe.ui.Dialog({
        title: title,
        fields: [
            {
                fieldname: "info",
                fieldtype: "HTML",
                options: `<div style="margin-bottom:10px;">
                    <strong>کارمند:</strong> ${employee}<br>
                    <strong>تاریخ:</strong> ${date}
                </div>`
            },
            {
                fieldname: "time",
                label: __("ساعت"),
                fieldtype: "Time",
                reqd: 1,
                default: default_time
            },
            {
                fieldname: "log_type",
                label: __("نوع"),
                fieldtype: "Select",
                options: "IN\nOUT",
                reqd: 1,
                default: default_log_type
            }
        ],
        primary_action_label: __("ذخیره"),
        primary_action: function (values) {
            let datetime = date + " " + values.time;

            frappe.call({
                method: "hrms.hr.report.smart_attendance_report.smart_attendance_report.add_manual_checkin",
                args: {
                    employee: employee,
                    log_type: values.log_type,
                    time: datetime
                },
                callback: function (r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("لاگ با موفقیت ثبت شد"),
                            indicator: "green"
                        });
                        dialog.hide();
                        frappe.query_report.refresh();
                    }
                }
            });
        }
    });

    dialog.show();
};

// Global function for editing existing checkin
window.smart_attendance_edit_checkin = function (checkin_name) {
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Employee Checkin",
            name: checkin_name
        },
        callback: function (r) {
            if (r.message) {
                let checkin = r.message;

                // جلوگیری از مشکل timezone / day-shift
                let raw_datetime = checkin.time || "";
                let date_part = raw_datetime.split(" ")[0] || "";
                let time_part = raw_datetime.split(" ")[1] || "08:00:00";

                let isCurrentlyExcluded = !!checkin.custom_is_excluded;

                let dialog = new frappe.ui.Dialog({
                    title: __("ویرایش ورود/خروج"),
                    fields: [
                        {
                            fieldname: "info",
                            fieldtype: "HTML",
                            options: `<div style="margin-bottom:10px;padding:8px;background:#f5f5f5;border-radius:4px;">
                                <strong>کارمند:</strong> ${checkin.employee}<br>
                                <strong>تاریخ:</strong> <span style="color:#0d6efd;font-weight:bold">${date_part}</span>
                                <span style="color:#888;font-size:11px;margin-right:6px">(تاریخ قابل تغییر نیست)</span><br>
                                <strong>نوع فعلی:</strong> ${checkin.log_type === 'IN' ? 'ورود ⬇️' : 'خروج ⬆️'}
                            </div>`
                        },
                        {
                            fieldname: "time",
                            label: __("ساعت"),
                            fieldtype: "Time",
                            reqd: 1,
                            default: time_part
                        },
                        {
                            fieldname: "log_type",
                            label: __("نوع"),
                            fieldtype: "Select",
                            options: "IN\nOUT",
                            reqd: 1,
                            default: checkin.log_type
                        }
                    ],
                    primary_action_label: __("ذخیره"),
                    primary_action: function (values) {
                        // تاریخ اصلی حفظ می‌شود، فقط ساعت تغییر می‌کند
                        frappe.call({
                            method: "hrms.hr.report.smart_attendance_report.smart_attendance_report.update_checkin_log",
                            args: {
                                checkin_name: checkin_name,
                                work_date: date_part,
                                log_time: values.time,
                                log_type: values.log_type
                            },
                            callback: function (r) {
                                if (r.message && r.message.success) {
                                    frappe.show_alert({
                                        message: __("ویرایش با موفقیت انجام شد"),
                                        indicator: "green"
                                    });
                                    dialog.hide();
                                    frappe.query_report.refresh();
                                }
                            }
                        });
                    },
                    secondary_action_label: isCurrentlyExcluded ? __("↩️ حساب شود") : __("🚫 حساب نشود"),
                    secondary_action: function () {
                        smart_attendance_toggle_excluded(checkin_name, isCurrentlyExcluded ? 0 : 1, function () {
                            dialog.hide();
                            frappe.query_report.refresh();
                        });
                    }
                });

                dialog.show();
            }
        }
    });
};

// دکمه ترکیبی پاکسازی نویزی + بازسازی ترتیب (جایگزین دو دکمه 🧹 و 🛠️)
window.smart_attendance_fix_and_cleanup_day = function (employee, work_date) {
    frappe.confirm(
        __("لاگ‌های نویزی/تکراری این روز علامت‌گذاری (حساب نشود) و ترتیب ورود/خروج بازسازی شود؟"),
        function () {
            frappe.call({
                method: "hrms.hr.report.smart_attendance_report.smart_attendance_report.cleanup_noisy_day_logs",
                args: {
                    employee: employee,
                    work_date: work_date
                },
                callback: function (r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("پاکسازی و بازسازی انجام شد ({0} علامت‌گذاری، {1} اصلاح نوع)")
                                .replace("{0}", r.message.flagged_count || r.message.deleted_count || 0)
                                .replace("{1}", r.message.repaired_count || 0),
                            indicator: "green"
                        });
                        frappe.query_report.refresh();
                    }
                }
            });
        }
    );
};

window.smart_attendance_toggle_excluded = function (checkin_name, is_excluded, callback) {
    frappe.call({
        method: "hrms.hr.report.smart_attendance_report.smart_attendance_report.toggle_checkin_excluded",
        args: {
            checkin_name: checkin_name,
            is_excluded: is_excluded ? 1 : 0
        },
        callback: function (r) {
            if (r.message && r.message.success) {
                let msg = is_excluded ? __("لاگ علامت «حساب نشود» خورد") : __("علامت‌گذاری برداشته شد");
                frappe.show_alert({ message: msg, indicator: is_excluded ? "orange" : "green" });
                if (callback) callback();
                else frappe.query_report.refresh();
            }
        }
    });
};

window.smart_attendance_mark_day = function (employee, work_date, current_status) {
    const dialog = new frappe.ui.Dialog({
        title: __("ثبت وضعیت روز"),
        fields: [
            {
                fieldname: "info",
                fieldtype: "HTML",
                options: `<div style="margin-bottom:10px;">
                    <strong>کارمند:</strong> ${employee}<br>
                    <strong>تاریخ:</strong> ${work_date}<br>
                    <strong>وضعیت فعلی:</strong> ${current_status || "ثبت نشده"}
                </div>`
            },
            {
                fieldname: "status",
                label: __("وضعیت"),
                fieldtype: "Select",
                options: "Absent\nOn Leave",
                reqd: 1,
                default: current_status === "On Leave" ? "On Leave" : "Absent"
            },
            {
                fieldname: "leave_type",
                label: __("نوع مرخصی"),
                fieldtype: "Link",
                options: "Leave Type",
                depends_on: "eval:doc.status=='On Leave'"
            }
        ],
        primary_action_label: __("ذخیره"),
        primary_action: function (values) {
            frappe.call({
                method: "hrms.hr.report.smart_attendance_report.smart_attendance_report.upsert_attendance_from_report",
                args: {
                    employee: employee,
                    work_date: work_date,
                    status: values.status,
                    leave_type: values.leave_type
                },
                callback: function (r) {
                    if (r.message && r.message.success) {
                        let message = __("وضعیت روز ذخیره شد");
                        if (r.message.leave_application) {
                            message += " - " + __("مرخصی نیز ثبت شد");
                        } else if (r.message.leave_error) {
                            message += " - " + __("ثبت مرخصی خودکار ناموفق بود (Attendance ثبت شد)");
                        }
                        frappe.show_alert({
                            message: message,
                            indicator: "green"
                        });
                        dialog.hide();
                        frappe.query_report.refresh();
                    }
                }
            });
        }
    });

    dialog.show();
};

// ===================== تابع چاپ / PDF =====================
window.smart_attendance_print_report = function (report) {
    const data = frappe.query_report.data;
    const filters = frappe.query_report.get_values();

    if (!data || !data.length) {
        frappe.msgprint(__("داده\u200cای برای چاپ وجود ندارد. ابتدا گزارش را اجرا کنید."));
        return;
    }

    function toHHMM(val) {
        let v = parseFloat(val) || 0;
        if (v === 0) return "\u2014";
        let h = Math.floor(v);
        let m = Math.round((v - h) * 60);
        if (m === 60) { h++; m = 0; }
        return h + ":" + String(m).padStart(2, "0");
    }

    let employeeLabel = "\u0647\u0645\u0647 \u06a9\u0627\u0631\u0645\u0646\u062f\u0627\u0646";
    if (filters.employee && data.length > 0) {
        employeeLabel = data[0].employee_name || filters.employee;
    } else if (filters.employees) {
        employeeLabel = filters.employees;
    }

    let employeeTotals = {};
    let tableRows = "";
    let rowIdx = 0;

    for (let row of data) {
        rowIdx++;
        let isHoliday = row.day_name === "\u062c\u0645\u0639\u0647" || (!row.has_issue && row.log_status === "\u062a\u0639\u0637\u06cc\u0644");
        let rowClass = isHoliday ? "row-holiday" : (row.has_issue ? "row-issue" : "");
        let working = parseFloat(row.working_hours) || 0;
        let timeOff = parseFloat(row.time_off) || 0;
        let overtime = parseFloat(row.overtime) || 0;
        let status = (row.log_status || "").replace(/\ud83d\udfe2|\u2705|\ud83d\udd34|\ud83d\udfe1|\ud83d\udfe0|\ud83d\udfe3|\u26ab|\u2139\ufe0f/g, "").trim();

        tableRows += "<tr class=\"" + rowClass + "\">"
            + "<td class=\"idx\">" + rowIdx + "</td>"
            + "<td class=\"date\">" + (row.work_date_shamsi || row.work_date || "") + "</td>"
            + "<td class=\"day\">" + (row.day_name || "") + "</td>"
            + "<td class=\"emp\">" + (row.employee_name || row.employee || "") + "</td>"
            + "<td class=\"time\">" + (row.actual_start || "\u2014") + "</td>"
            + "<td class=\"time\">" + (row.actual_end || "\u2014") + "</td>"
            + "<td>" + (working > 0 ? toHHMM(working) : "<span style='color:#bbb'>\u2014</span>") + "</td>"
            + "<td class=\"" + (timeOff > 0 ? "cell-deficit" : "") + "\">" + (timeOff > 0 ? toHHMM(timeOff) : "\u2014") + "</td>"
            + "<td class=\"" + (overtime > 0 ? "cell-overtime" : "") + "\">" + (overtime > 0 ? toHHMM(overtime) : "\u2014") + "</td>"
            + "<td class=\"status\">" + status + "</td>"
            + "</tr>";

        let empKey = row.employee || "unknown";
        if (!employeeTotals[empKey]) {
            employeeTotals[empKey] = { name: row.employee_name || row.employee || empKey, working: 0, timeOff: 0, overtime: 0, workDays: 0, totalDays: 0 };
        }
        employeeTotals[empKey].working += working;
        employeeTotals[empKey].timeOff += timeOff;
        employeeTotals[empKey].overtime += overtime;
        employeeTotals[empKey].totalDays++;
        if (working > 0) employeeTotals[empKey].workDays++;
    }

    let summaryRows = "";
    for (let empKey of Object.keys(employeeTotals)) {
        let t = employeeTotals[empKey];
        summaryRows += "<tr class=\"row-summary\">"
            + "<td colspan=\"3\" style=\"text-align:right;padding-right:10px\">\ud83d\udd22 \u062c\u0645\u0639: " + t.name + "</td>"
            + "<td>" + t.workDays + " \u0631\u0648\u0632 \u0627\u0632 " + t.totalDays + "</td>"
            + "<td colspan=\"2\"></td>"
            + "<td>" + toHHMM(t.working) + "</td>"
            + "<td class=\"" + (t.timeOff > 0 ? "cell-deficit" : "") + "\">" + toHHMM(t.timeOff) + "</td>"
            + "<td class=\"" + (t.overtime > 0 ? "cell-overtime" : "") + "\">" + toHHMM(t.overtime) + "</td>"
            + "<td></td>"
            + "</tr>";
    }

    let nowDate = new Date().toLocaleDateString("fa-IR", { year: "numeric", month: "long", day: "numeric" });

    let css = [
        "* { box-sizing:border-box; margin:0; padding:0 }",
        "body { font-family:Tahoma,Arial,sans-serif; direction:rtl; background:#f0f2f5; color:#1a1a2e; font-size:12px }",
        ".print-bar { background:linear-gradient(135deg,#1e3a5f,#2980b9); color:white; padding:12px 20px; display:flex; align-items:center; gap:12px; position:sticky; top:0; z-index:100; box-shadow:0 2px 8px rgba(0,0,0,.2) }",
        ".print-bar button { background:white; color:#1e3a5f; border:none; padding:8px 22px; border-radius:6px; cursor:pointer; font-size:13px; font-weight:bold; font-family:inherit }",
        ".print-bar button:hover { background:#e8f0fe }",
        ".page { max-width:1060px; margin:24px auto; background:white; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,.12); overflow:hidden }",
        ".report-header { background:linear-gradient(135deg,#1e3a5f 0%,#2c5f8a 100%); color:white; padding:26px 30px 0; text-align:center }",
        ".report-header h1 { font-size:21px; font-weight:700; margin-bottom:6px }",
        ".report-header .sub { font-size:12px; opacity:.8; margin-bottom:16px }",
        ".accent-bar { height:4px; background:linear-gradient(90deg,#f39c12,#e74c3c,#f39c12) }",
        ".meta-bar { display:flex; justify-content:center; gap:22px; flex-wrap:wrap; padding:12px 30px; background:#f8fafc; border-bottom:1px solid #e2e8f0 }",
        ".meta-item { display:flex; align-items:center; gap:5px; font-size:12px; color:#4a5568 }",
        ".meta-item strong { color:#1e3a5f }",
        ".table-wrapper { padding-bottom:14px; overflow-x:auto }",
        "table { width:100%; border-collapse:collapse }",
        "thead tr { background:#1e3a5f }",
        "th { color:white; padding:10px 6px; text-align:center; font-size:11px; font-weight:600; border:1px solid #2c5f8a; white-space:nowrap }",
        "td { padding:6px 5px; text-align:center; border:1px solid #e2e8f0; font-size:11px; vertical-align:middle }",
        "tbody tr:nth-child(even) td { background:#f7fafc }",
        ".row-holiday td { background:#fffbeb !important; color:#92400e }",
        ".row-issue td { background:#fff5f5 !important }",
        ".row-summary td { background:#dbeafe !important; font-weight:700; border-top:2px solid #1e3a5f; border-bottom:2px solid #1e3a5f }",
        ".cell-deficit { color:#dc2626; font-weight:700 }",
        ".cell-overtime { color:#16a34a; font-weight:700 }",
        ".idx { color:#94a3b8; font-size:10px } .date,.time { white-space:nowrap }",
        ".emp { text-align:right; padding-right:8px; font-weight:500 }",
        ".status { font-size:10px; text-align:right; padding-right:6px; color:#555 }",
        ".signature-section { padding:28px 30px 10px; border-top:2px solid #e2e8f0 }",
        ".sig-title { font-size:13px; font-weight:700; color:#1e3a5f; padding-bottom:8px; border-bottom:1px dashed #cbd5e0; margin-bottom:14px }",
        ".sig-row { display:flex; justify-content:space-between; gap:18px; margin-top:10px }",
        ".sig-box { flex:1; text-align:center }",
        ".sig-role { font-size:12px; font-weight:600; color:#2d3748; margin-bottom:4px }",
        ".sig-name-line { font-size:11px; color:#718096; margin-bottom:58px }",
        ".sig-line { border-top:1px solid #4a5568; padding-top:6px; font-size:10px; color:#94a3b8 }",
        ".report-footer { padding:10px 30px; background:#f8fafc; border-top:1px solid #e2e8f0; display:flex; justify-content:space-between; font-size:10px; color:#94a3b8 }",
        "@media print { body{background:white} .print-bar{display:none!important} .page{max-width:100%;margin:0;border-radius:0;box-shadow:none} .report-header{padding:14px 20px 0} .report-header h1{font-size:17px} th,td{font-size:10px;padding:5px 3px} .signature-section{padding:18px 20px;margin-top:2px} .sig-name-line{margin-bottom:42px} table{page-break-inside:auto} tr{page-break-inside:avoid} thead{display:table-header-group} }"
    ].join("\n");

    let html = "<!DOCTYPE html><html dir=\"rtl\" lang=\"fa\"><head><meta charset=\"UTF-8\">"
        + "<title>\u06af\u0632\u0627\u0631\u0634 \u062d\u0636\u0648\u0631 \u0648 \u063a\u06cc\u0627\u0628 - " + employeeLabel + "</title>"
        + "<style>" + css + "</style></head><body>"
        + "<div class=\"print-bar\">"
        + "<button onclick=\"window.print()\">\ud83d\udda8\ufe0f \u0686\u0627\u067e / \u0630\u062e\u06cc\u0631\u0647 PDF</button>"
        + "<span style=\"font-size:15px;font-weight:bold\">\u06af\u0632\u0627\u0631\u0634 \u062d\u0636\u0648\u0631 \u0648 \u063a\u06cc\u0627\u0628 \u0647\u0648\u0634\u0645\u0646\u062f</span>"
        + "<span style=\"margin-right:auto;font-size:11px;opacity:.8\">\u0628\u0631\u0627\u06cc PDF: \u0686\u0627\u067e \u2190 \u0645\u0642\u0635\u062f: \u0630\u062e\u06cc\u0631\u0647 \u0628\u0647 \u0639\u0646\u0648\u0627\u0646 PDF</span>"
        + "</div>"
        + "<div class=\"page\">"
        + "<div class=\"report-header\"><h1>\ud83d\udccb \u06af\u0632\u0627\u0631\u0634 \u062d\u0636\u0648\u0631 \u0648 \u063a\u06cc\u0627\u0628 \u0647\u0648\u0634\u0645\u0646\u062f</h1><div class=\"sub\">Human Resource Management System</div></div>"
        + "<div class=\"accent-bar\"></div>"
        + "<div class=\"meta-bar\">"
        + "<div class=\"meta-item\">\ud83d\udcc5 \u0627\u0632: <strong>" + (filters.from_date || "\u2014") + "</strong></div>"
        + "<div class=\"meta-item\">\ud83d\udcc5 \u062a\u0627: <strong>" + (filters.to_date || "\u2014") + "</strong></div>"
        + "<div class=\"meta-item\">\ud83d\udc64 \u06a9\u0627\u0631\u0645\u0646\u062f: <strong>" + employeeLabel + "</strong></div>"
        + "<div class=\"meta-item\">\ud83d\udcca \u062a\u0639\u062f\u0627\u062f \u0631\u062f\u06cc\u0641: <strong>" + data.length + "</strong></div>"
        + "<div class=\"meta-item\">\ud83d\uddd3\ufe0f \u062a\u0627\u0631\u06cc\u062e \u0686\u0627\u067e: <strong>" + nowDate + "</strong></div>"
        + "</div>"
        + "<div class=\"table-wrapper\"><table>"
        + "<thead><tr>"
        + "<th style=\"width:28px\">#</th>"
        + "<th style=\"width:88px\">\u062a\u0627\u0631\u06cc\u062e (\u0634\u0645\u0633\u06cc)</th>"
        + "<th style=\"width:55px\">\u0631\u0648\u0632 \u0647\u0641\u062a\u0647</th>"
        + "<th style=\"min-width:110px\">\u0646\u0627\u0645 \u06a9\u0627\u0631\u0645\u0646\u062f</th>"
        + "<th style=\"width:58px\">\u0648\u0631\u0648\u062f</th>"
        + "<th style=\"width:58px\">\u062e\u0631\u0648\u062c</th>"
        + "<th style=\"width:62px\">\u0633\u0627\u0639\u062a \u06a9\u0627\u0631\u06cc</th>"
        + "<th style=\"width:52px\">\u06a9\u0633\u0631\u06cc</th>"
        + "<th style=\"width:62px\">\u0627\u0636\u0627\u0641\u0647\u200c\u06a9\u0627\u0631</th>"
        + "<th>\u0648\u0636\u0639\u06cc\u062a</th>"
        + "</tr></thead>"
        + "<tbody>" + tableRows + summaryRows + "</tbody></table></div>"
        + "<div class=\"signature-section\">"
        + "<div class=\"sig-title\">\u270d\ufe0f \u062a\u0623\u06cc\u06cc\u062f\u06cc\u0647 \u0648 \u0627\u0645\u0636\u0627</div>"
        + "<div class=\"sig-row\">"
        + "<div class=\"sig-box\"><div class=\"sig-role\">\u06a9\u0627\u0631\u0645\u0646\u062f</div><div class=\"sig-name-line\">\u0646\u0627\u0645: ................................</div><div class=\"sig-line\">\u0627\u0645\u0636\u0627 \u0648 \u062a\u0627\u0631\u06cc\u062e</div></div>"
        + "<div class=\"sig-box\"><div class=\"sig-role\">\u0633\u0631\u067e\u0631\u0633\u062a \u0645\u0633\u062a\u0642\u06cc\u0645</div><div class=\"sig-name-line\">\u0646\u0627\u0645: ................................</div><div class=\"sig-line\">\u0627\u0645\u0636\u0627 \u0648 \u062a\u0627\u0631\u06cc\u062e</div></div>"
        + "<div class=\"sig-box\"><div class=\"sig-role\">\u0645\u062f\u06cc\u0631 \u0645\u0646\u0627\u0628\u0639 \u0627\u0646\u0633\u0627\u0646\u06cc</div><div class=\"sig-name-line\">\u0646\u0627\u0645: ................................</div><div class=\"sig-line\">\u0627\u0645\u0636\u0627 \u0648 \u062a\u0627\u0631\u06cc\u062e</div></div>"
        + "<div class=\"sig-box\"><div class=\"sig-role\">\u0645\u062f\u06cc\u0631\u0639\u0627\u0645\u0644</div><div class=\"sig-name-line\">&nbsp;</div><div class=\"sig-line\">\u0645\u0647\u0631 \u0648 \u0627\u0645\u0636\u0627</div></div>"
        + "</div></div>"
        + "<div class=\"report-footer\"><span>\u0633\u06cc\u0633\u062a\u0645 \u062d\u0636\u0648\u0631 \u0648 \u063a\u06cc\u0627\u0628 \u0647\u0648\u0634\u0645\u0646\u062f</span><span>\u062a\u0627\u0631\u06cc\u062e \u0686\u0627\u067e: " + nowDate + "</span></div>"
        + "</div></body></html>";

    let w = window.open("", "_blank", "width=1100,height=800");
    if (!w) {
        frappe.msgprint(__("پنجره جدید باز نشد. لطفاً Pop-up Blocker مرورگر را غیرفعال کنید."));
        return;
    }
    w.document.write(html);
    w.document.close();
};
