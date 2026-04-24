// Copyright (c) 2024, Iran Utilities
// For license information, please see license.txt

frappe.query_reports["Smart Attendance Report"] = {
    "onload": function (report) {
        report.page.add_inner_button(__("اصلاح خروج‌های ساعت ۰۰:۰۰"), function () {
            const filters = report.get_values();
            frappe.confirm(
                __("خروج‌های دقیقاً ساعت ۰۰:۰۰:۰۰ در بازه انتخابی به ۰۰:۰۰:۰۱ تغییر کند؟"),
                function () {
                    call_normalize_midnight(report, filters);
                }
            );
        });

        report.page.add_inner_button(__("پاکسازی خودکار لاگ تکراری"), function () {
            const filters = report.get_values();
            frappe.confirm(
                __("برای کل بازه انتخابی، روزهای دارای لاگ تکراری خودکار اصلاح شوند؟"),
                function () {
                    call_bulk_cleanup(report, filters);
                }
            );
        });
    },

    "filters": [
        {
            "fieldname": "employee",
            "label": __("کارمند"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 180
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
        value = default_formatter(value, row, column, data);

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

        // Make all_logs interactive with edit icons
        if (column.fieldname === "all_logs" && data.all_logs_json && data.all_logs_json.length > 0) {
            let logParts = [];
            for (let log of data.all_logs_json) {
                let icon = log.log_type === "IN" ? "⬇️" : "⬆️";
                let editIcon = `<span onclick="smart_attendance_edit_checkin('${log.name}')" 
                                      style="cursor:pointer;color:#666;font-size:12px" 
                                      title="ویرایش">✏️</span>`;
                logParts.push(`${editIcon}${icon}${log.time}`);
            }
            let fixIcon = "";
            if (data.all_logs_json.length >= 2) {
                fixIcon = `<span onclick="smart_attendance_repair_day('${data.employee}', '${data.work_date}')"
                                 style="cursor:pointer;color:#0d6efd;font-size:12px;margin-left:6px"
                                 title="بازسازی ترتیب ورود/خروج">🛠️</span>`;
            }
            let cleanupIcon = "";
            if (data.all_logs_json.length >= 2) {
                cleanupIcon = `<span onclick="smart_attendance_cleanup_day('${data.employee}', '${data.work_date}')"
                                     style="cursor:pointer;color:#dc3545;font-size:12px;margin-left:6px"
                                     title="حذف لاگ‌های نویزی">🧹</span>`;
            }
            value = cleanupIcon + fixIcon + logParts.join(" | ");
        }

        // Make actual_start (ورود) clickable with edit icon
        if (column.fieldname === "actual_start") {
            let time_display = data.actual_start || "--:--";
            let link_html = "";
            let edit_html = "";

            if (data.actual_start && data.first_in_name) {
                link_html = `<a href="/app/employee-checkin/${data.first_in_name}" 
                               style="color:#007bff;">
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
                link_html = `<a href="/app/employee-checkin/${data.last_out_name}" 
                               style="color:#007bff;">
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

        // Highlight time_off
        if (column.fieldname === "time_off" && data.time_off > 0) {
            value = "<span style='color:red;font-weight:bold'>" + value + "</span>";
        }

        // Highlight overtime
        if (column.fieldname === "overtime" && data.overtime > 0) {
            value = "<span style='color:green;font-weight:bold'>" + value + "</span>";
        }

        return value;
    }
};

function call_normalize_midnight(report, filters) {
    frappe.call({
        method: "hrms.hr.report.smart_attendance_report.smart_attendance_report.normalize_midnight_checkout_logs",
        args: {
            from_date: filters.from_date,
            to_date: filters.to_date,
            employee: filters.employee,
            employees: filters.employees
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
                report.refresh();
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
            employees: filters.employees
        },
        callback: function (r) {
            if (r.exc && String(r.exc).includes("has no attribute 'cleanup_noisy_logs_bulk'")) {
                frappe.msgprint(__("سرور هنوز نسخه جدید را لود نکرده. لطفاً bench restart و clear-cache انجام شود."));
                return;
            }

            if (r.message && r.message.success) {
                const msg = __("روز پردازش‌شده: {0} | روز اصلاح‌شده: {1} | لاگ حذف‌شده: {2}")
                    .replace("{0}", r.message.processed_days || 0)
                    .replace("{1}", r.message.affected_days || 0)
                    .replace("{2}", r.message.deleted_count || 0);
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
    let title = log_type === "IN" ? "ثبت ورود" : "ثبت خروج";
    let default_time = log_type === "IN" ? "08:00:00" : "17:00:00";

    let dialog = new frappe.ui.Dialog({
        title: __(title),
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
            }
        ],
        primary_action_label: __("ذخیره"),
        primary_action: function (values) {
            let datetime = date + " " + values.time;

            frappe.call({
                method: "hrms.hr.report.smart_attendance_report.smart_attendance_report.add_manual_checkin",
                args: {
                    employee: employee,
                    log_type: log_type,
                    time: datetime
                },
                callback: function (r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: log_type === "IN" ? __("ورود ثبت شد") : __("خروج ثبت شد"),
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
                let current_time = checkin.time.split(" ")[1] || "08:00:00";

                let dialog = new frappe.ui.Dialog({
                    title: __("ویرایش ورود/خروج"),
                    fields: [
                        {
                            fieldname: "info",
                            fieldtype: "HTML",
                            options: `<div style="margin-bottom:10px;">
                                <strong>کارمند:</strong> ${checkin.employee}<br>
                                <strong>نوع فعلی:</strong> ${checkin.log_type === 'IN' ? 'ورود' : 'خروج'}
                            </div>`
                        },
                        {
                            fieldname: "date",
                            label: __("تاریخ"),
                            fieldtype: "Date",
                            reqd: 1,
                            default: checkin.time.split(" ")[0]
                        },
                        {
                            fieldname: "time",
                            label: __("ساعت"),
                            fieldtype: "Time",
                            reqd: 1,
                            default: current_time
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
                        let datetime = values.date + " " + values.time;

                        frappe.call({
                            method: "frappe.client.set_value",
                            args: {
                                doctype: "Employee Checkin",
                                name: checkin_name,
                                fieldname: {
                                    time: datetime,
                                    log_type: values.log_type
                                }
                            },
                            callback: function (r) {
                                if (r.message) {
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
                    secondary_action_label: __("حذف"),
                    secondary_action: function () {
                        frappe.confirm(
                            __("آیا از حذف این رکورد مطمئن هستید؟"),
                            function () {
                                frappe.call({
                                    method: "frappe.client.delete",
                                    args: {
                                        doctype: "Employee Checkin",
                                        name: checkin_name
                                    },
                                    callback: function (r) {
                                        frappe.show_alert({
                                            message: __("رکورد حذف شد"),
                                            indicator: "orange"
                                        });
                                        dialog.hide();
                                        frappe.query_report.refresh();
                                    }
                                });
                            }
                        );
                    }
                });

                dialog.show();
            }
        }
    });
};

window.smart_attendance_repair_day = function (employee, work_date) {
    frappe.confirm(
        __("ترتیب ورود/خروج این روز بر اساس زمان بازسازی شود؟"),
        function () {
            frappe.call({
                method: "hrms.hr.report.smart_attendance_report.smart_attendance_report.auto_repair_day_checkins",
                args: {
                    employee: employee,
                    work_date: work_date
                },
                callback: function (r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("بازسازی انجام شد ({0} لاگ تغییر کرد)").replace("{0}", r.message.updated_count || 0),
                            indicator: "green"
                        });
                        frappe.query_report.refresh();
                    }
                }
            });
        }
    );
};

window.smart_attendance_cleanup_day = function (employee, work_date) {
    frappe.confirm(
        __("لاگ‌های نویزی/تکراری این روز حذف شوند؟"),
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
                            message: __("پاکسازی انجام شد ({0} حذف، {1} اصلاح نوع)").replace("{0}", r.message.deleted_count || 0).replace("{1}", r.message.repaired_count || 0),
                            indicator: "green"
                        });
                        frappe.query_report.refresh();
                    }
                }
            });
        }
    );
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
