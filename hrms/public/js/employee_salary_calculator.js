/**
 * Salary Calculator for Employee Form
 * Calculates salary components from total monthly salary based on Iranian labor law
 */

frappe.ui.form.on('Employee', {
    refresh: function (frm) {
        // Enable for all employees
        if (!frm.is_new()) {
            frm.add_custom_button(__('محاسبه حقوق'), function () {
                show_salary_calculator(frm);
            }, __('ابزارها'));
        }
    }
});

function show_salary_calculator(frm) {
    // Default fixed amounts (Iranian labor law 1404)
    const HOUSING_ALLOWANCE = 9000000;  // حق مسکن
    const GROCERY_ALLOWANCE = 22000000; // بن خوار و بار
    const MARRIAGE_ALLOWANCE = 5000000; // حق تاهل
    const CHILD_ALLOWANCE = 10390968;   // حق اولاد per child
    const SEVERANCE_DAILY_1404 = 94000; // پایه سنوات روزانه 1404 - 94,000 ریال
    const MIN_HOURLY_WAGE_1404 = 472522; // حداقل مزد ساعتی 1404
    const MIN_DAILY_WAGE_1404 = 3463656; // حداقل مزد روزانه 1404
    const MIN_MONTHLY_WAGE_1404 = 103909680; // حداقل مزد ماهیانه 1404
    const WORKING_HOURS_PER_DAY = 7.33;
    const DAYS_PER_MONTH = 30;
    const OVERTIME_MULTIPLIER = 1.4;

    // Calculate current total salary from existing fields
    const current_monthly_base = flt(frm.doc.base_pay) * WORKING_HOURS_PER_DAY * DAYS_PER_MONTH;
    const current_monthly_tech = flt(frm.doc.monthly_technical_bonus);
    const current_fixed = HOUSING_ALLOWANCE + GROCERY_ALLOWANCE +
        (frm.doc.marital_status === 'Married' ? MARRIAGE_ALLOWANCE : 0) +
        (CHILD_ALLOWANCE * flt(frm.doc.children_count)) +
        flt(frm.doc.supervision_allowance);
    const current_total = current_monthly_base + current_monthly_tech + current_fixed;

    let dialog = new frappe.ui.Dialog({
        title: __('محاسبه حقوق و دستمزد'),
        size: 'large',
        fields: [
            {
                fieldtype: 'Section Break',
                label: __('وضعیت فعلی کارمند')
            },
            {
                fieldname: 'current_status',
                fieldtype: 'HTML',
                options: `
                    <div class="alert alert-secondary">
                        <h5>${frm.doc.employee_name}</h5>
                        <table class="table table-sm table-bordered" style="font-size:12px;margin-bottom:0;">
                            <tr>
                                <td>حقوق ساعتی (base_pay)</td>
                                <td><strong>${format_currency(flt(frm.doc.base_pay), 'ریال')}</strong></td>
                                <td>حق فنی ساعتی (technical_bonus)</td>
                                <td><strong>${format_currency(flt(frm.doc.technical_bonus), 'ریال')}</strong></td>
                            </tr>
                            <tr>
                                <td>حقوق روزانه</td>
                                <td>${format_currency(flt(frm.doc.daily_pay), 'ریال')}</td>
                                <td>حق فنی ماهیانه</td>
                                <td>${format_currency(flt(frm.doc.monthly_technical_bonus), 'ریال')}</td>
                            </tr>
                            <tr>
                                <td>نرخ اضافه‌کاری</td>
                                <td>${format_currency(flt(frm.doc.overtime_rate), 'ریال')}</td>
                                <td>کسر کار ساعتی</td>
                                <td>${format_currency(flt(frm.doc.absence_deduction), 'ریال')}</td>
                            </tr>
                            <tr>
                                <td>حق سرپرستی</td>
                                <td>${format_currency(flt(frm.doc.supervision_allowance), 'ریال')}</td>
                                <td colspan="2"><strong>تخمین حقوق کل ماهیانه: ${format_currency(current_total, 'ریال')}</strong></td>
                            </tr>
                            <tr style="background:#e3f2fd;">
                                <td>تاریخ استخدام</td>
                                <td><strong>${frm.doc.date_of_joining || 'نامشخص'}</strong></td>
                                <td>سابقه کار</td>
                                <td><strong>${calculate_years_of_service(frm.doc.date_of_joining)} سال</strong></td>
                            </tr>
                        </table>
                    </div>
                `
            },
            {
                fieldtype: 'Section Break',
                label: __('محاسبه حقوق جدید')
            },
            {
                fieldname: 'total_salary',
                label: __('حقوق کل ماهیانه (ریال)'),
                fieldtype: 'Currency',
                reqd: 1,
                default: current_total,
                description: __('مبلغ کل ناخالص ماهیانه - تمام مبلغ متغیر به حق فنی منتقل می‌شود')
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldname: 'is_married',
                label: __('متاهل'),
                fieldtype: 'Check',
                default: frm.doc.marital_status === 'Married' ? 1 : 0
            },
            {
                fieldname: 'children_count',
                label: __('تعداد فرزند'),
                fieldtype: 'Int',
                default: frm.doc.children_count || 0
            },
            {
                fieldtype: 'Section Break',
                label: __('مزایای اختیاری')
            },
            {
                fieldname: 'has_supervision',
                label: __('حق سرپرستی'),
                fieldtype: 'Check',
                default: frm.doc.supervision_allowance > 0 ? 1 : 0
            },
            {
                fieldname: 'supervision_amount',
                label: __('مبلغ حق سرپرستی'),
                fieldtype: 'Currency',
                default: frm.doc.supervision_allowance || 0,
                depends_on: 'eval:doc.has_supervision'
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldname: 'years_of_service',
                label: __('سابقه کار (سال)'),
                fieldtype: 'Int',
                default: calculate_years_of_service(frm.doc.date_of_joining),
                description: __('برای محاسبه پایه سنوات - طبق جدول ۱۴۰۴')
            },
            {
                fieldtype: 'Section Break',
                label: __('مزایای ثابت (طبق وزارت کار ۱۴۰۴)')
            },
            {
                fieldname: 'housing_info',
                fieldtype: 'HTML',
                options: `
                    <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #eee;">
                        <span>حق مسکن:</span><strong>${format_currency(HOUSING_ALLOWANCE, 'ریال')}</strong>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #eee;">
                        <span>بن خوار و بار:</span><strong>${format_currency(GROCERY_ALLOWANCE, 'ریال')}</strong>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #eee;">
                        <span>حق تاهل (اگر متاهل):</span><strong>${format_currency(MARRIAGE_ALLOWANCE, 'ریال')}</strong>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #eee;">
                        <span>حق اولاد (هر فرزند):</span><strong>${format_currency(CHILD_ALLOWANCE, 'ریال')}</strong>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding:5px 0;background:#f0f0f0;">
                        <span>پایه سنوات (روزانه ۱۴۰۴):</span><strong>${format_currency(SEVERANCE_DAILY_1404, 'ریال')} × سال‌های سابقه × ۳۰</strong>
                    </div>
                `
            },
            {
                fieldtype: 'Section Break',
                label: __('نتایج محاسبات')
            },
            {
                fieldname: 'results_html',
                fieldtype: 'HTML',
                options: '<div id="salary-calc-results" style="color:#666;"><em>روی دکمه "محاسبه" کلیک کنید</em></div>'
            }
        ],
        primary_action_label: __('اعمال به کارمند'),
        primary_action: function (values) {
            apply_calculated_values(frm, dialog);
        }
    });

    // Add calculate button
    dialog.$wrapper.find('.modal-footer').prepend(
        `<button class="btn btn-primary btn-sm" id="calc-btn" style="margin-left:10px;">
            ${__('محاسبه')}
        </button>`
    );

    dialog.$wrapper.find('#calc-btn').on('click', function () {
        calculate_salary(dialog, frm);
    });

    dialog.show();
}

function calculate_years_of_service(date_of_joining) {
    if (!date_of_joining) return 0;
    const joining = new Date(date_of_joining);
    const now = new Date();
    return Math.floor((now - joining) / (365.25 * 24 * 60 * 60 * 1000));
}

function calculate_salary(dialog, frm) {
    const values = dialog.get_values();

    // Fixed amounts - Iranian labor law 1404
    const HOUSING_ALLOWANCE = 9000000;
    const GROCERY_ALLOWANCE = 22000000;
    const MARRIAGE_ALLOWANCE = 5000000;
    const CHILD_ALLOWANCE = 10390968;
    const SEVERANCE_DAILY_1404 = 94000;  // پایه سنوات روزانه ۱۴۰۴
    const MIN_HOURLY_WAGE_1404 = 472522; // حداقل مزد ساعتی 1404
    const MIN_MONTHLY_WAGE_1404 = 103909680; // حداقل مزد ماهیانه 1404
    const WORKING_HOURS_PER_DAY = 7.33;
    const DAYS_PER_MONTH = 30;
    const OVERTIME_MULTIPLIER = 1.4;

    const total_salary = flt(values.total_salary);
    if (!total_salary) {
        frappe.msgprint(__('لطفاً مبلغ حقوق کل را وارد کنید'));
        return;
    }

    // Calculate fixed allowances
    let fixed_total = HOUSING_ALLOWANCE + GROCERY_ALLOWANCE;

    if (values.is_married) {
        fixed_total += MARRIAGE_ALLOWANCE;
    }

    fixed_total += CHILD_ALLOWANCE * flt(values.children_count);

    // Severance pay (پایه سنوات) - cumulative based on Iranian 1404 law
    // 70,000 Rials per day × years of service × 30 days
    const years = flt(values.years_of_service);
    const severance_pay = SEVERANCE_DAILY_1404 * years * DAYS_PER_MONTH;
    fixed_total += severance_pay;

    if (values.has_supervision) {
        fixed_total += flt(values.supervision_amount);
    }

    // Variable salary - goes to base_pay + technical_bonus
    const variable_salary = total_salary - fixed_total;

    if (variable_salary <= 0) {
        frappe.msgprint(__('مبلغ کل کمتر از مزایای ثابت است. لطفاً مبلغ بیشتری وارد کنید.'));
        return;
    }

    // Base pay = min(official minimum wage, variable salary)
    // If salary is less than minimum wage, all variable goes to base_pay
    // If salary is more than minimum wage, base_pay = minimum wage, rest goes to technical_bonus
    const monthly_base = Math.min(MIN_MONTHLY_WAGE_1404, variable_salary);

    // Technical bonus = remaining after base pay (can be 0 if salary < minimum wage)
    const monthly_technical = Math.max(0, variable_salary - monthly_base);

    // Calculate daily and hourly rates
    const daily_pay = monthly_base / DAYS_PER_MONTH;
    const hourly_base = daily_pay / WORKING_HOURS_PER_DAY;
    const hourly_technical = monthly_technical / DAYS_PER_MONTH / WORKING_HOURS_PER_DAY;

    // Overtime rate
    const overtime_rate = (hourly_base + hourly_technical) * OVERTIME_MULTIPLIER;

    // Absence deduction = Total monthly salary / 30 / 7.33
    // This includes ALL items: base pay + technical bonus + housing + grocery + marriage + children + supervision + severance
    // So if employee works 15 days, they get exactly half of total salary
    const absence_deduction = total_salary / DAYS_PER_MONTH / WORKING_HOURS_PER_DAY;

    // Store calculated values
    dialog.calculated_values = {
        base_pay: hourly_base,
        technical_bonus: hourly_technical,
        daily_pay: daily_pay,
        monthly_technical_bonus: monthly_technical,
        overtime_rate: overtime_rate,
        absence_deduction: absence_deduction,
        supervision_allowance: values.has_supervision ? flt(values.supervision_amount) : 0,
        children_count: flt(values.children_count)
    };

    // Display results
    const results_html = `
        <table class="table table-bordered" style="font-size:13px;">
            <thead style="background:#f5f5f5;">
                <tr>
                    <th>${__('فیلد')}</th>
                    <th>${__('مقدار (ریال)')}</th>
                    <th>${__('توضیح')}</th>
                </tr>
            </thead>
            <tbody>
                <tr style="background:${monthly_base >= MIN_MONTHLY_WAGE_1404 ? '#d4edda' : '#fff3cd'};">
                    <td><strong>حقوق ساعتی</strong> (base_pay)</td>
                    <td>${format_currency(hourly_base, 'ریال')}</td>
                    <td>${monthly_base >= MIN_MONTHLY_WAGE_1404 ? 'حداقل مزد ساعتی وزارت کار ۱۴۰۴' : 'کمتر از حداقل - کل حقوق متغیر'}</td>
                </tr>
                <tr style="background:#d4edda;">
                    <td><strong>حق فنی ساعتی</strong> (technical_bonus)</td>
                    <td>${format_currency(hourly_technical, 'ریال')}</td>
                    <td>${monthly_technical > 0 ? 'مابقی بعد از حداقل دستمزد' : 'صفر - حقوق کمتر از حداقل وزارت کار'}</td>
                </tr>
                <tr>
                    <td><strong>حق فنی ماهیانه</strong></td>
                    <td>${format_currency(monthly_technical, 'ریال')}</td>
                    <td>حقوق متغیر - حقوق پایه</td>
                </tr>
                <tr>
                    <td><strong>نرخ اضافه‌کاری</strong></td>
                    <td>${format_currency(overtime_rate, 'ریال')}</td>
                    <td>حق فنی ساعتی × 1.4</td>
                </tr>
                <tr style="background:#f8d7da;">
                    <td><strong>کسر کار ساعتی</strong></td>
                    <td>${format_currency(absence_deduction, 'ریال')}</td>
                    <td>کل حقوق (شامل سرپرستی) ÷ 30 ÷ 7.33</td>
                </tr>
                <tr style="background:#e9ecef;">
                    <td><strong>پایه سنوات ماهیانه</strong></td>
                    <td>${format_currency(severance_pay, 'ریال')}</td>
                    <td>${years} سال × ${format_currency(SEVERANCE_DAILY_1404, 'ریال')} × 30</td>
                </tr>
                ${values.has_supervision ? `
                <tr>
                    <td><strong>حق سرپرستی</strong></td>
                    <td>${format_currency(flt(values.supervision_amount), 'ریال')}</td>
                    <td>ثابت ماهیانه</td>
                </tr>
                ` : ''}
            </tbody>
            <tfoot style="background:#e8f4f8;">
                <tr>
                    <td><strong>مجموع حقوق ماهیانه</strong></td>
                    <td><strong>${format_currency(total_salary, 'ریال')}</strong></td>
                    <td></td>
                </tr>
            </tfoot>
        </table>
        <div class="alert alert-info" style="margin-top:10px;">
            <strong>خلاصه تفکیک:</strong><br>
            <div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:5px;">
                <span class="badge badge-secondary" style="font-size:12px;">مسکن: ${format_currency(HOUSING_ALLOWANCE, '')}</span>
                <span class="badge badge-secondary" style="font-size:12px;">بن: ${format_currency(GROCERY_ALLOWANCE, '')}</span>
                ${values.is_married ? `<span class="badge badge-secondary" style="font-size:12px;">تاهل: ${format_currency(MARRIAGE_ALLOWANCE, '')}</span>` : ''}
                ${flt(values.children_count) > 0 ? `<span class="badge badge-secondary" style="font-size:12px;">اولاد: ${format_currency(CHILD_ALLOWANCE * flt(values.children_count), '')}</span>` : ''}
                <span class="badge badge-secondary" style="font-size:12px;">سنوات: ${format_currency(severance_pay, '')}</span>
                ${values.has_supervision ? `<span class="badge badge-secondary" style="font-size:12px;">سرپرستی: ${format_currency(flt(values.supervision_amount), '')}</span>` : ''}
                <span class="badge badge-success" style="font-size:12px;">حق فنی: ${format_currency(variable_salary, '')}</span>
            </div>
            <hr>
            <strong>مثال کسر کار:</strong><br>
            اگر ${flt(values.years_of_service) > 0 ? 'این کارمند با ' + years + ' سال سابقه' : 'کارمند'} 15 روز از 30 روز بیاید:<br>
            دریافتی = ${format_currency(total_salary / 2, 'ریال')} (نصف حقوق کل)
        </div>
    `;

    dialog.$wrapper.find('#salary-calc-results').html(results_html);
}

function apply_calculated_values(frm, dialog) {
    if (!dialog.calculated_values) {
        frappe.msgprint(__('لطفاً ابتدا روی دکمه "محاسبه" کلیک کنید'));
        return;
    }

    const vals = dialog.calculated_values;

    frm.set_value('base_pay', vals.base_pay);
    frm.set_value('technical_bonus', vals.technical_bonus);
    frm.set_value('daily_pay', vals.daily_pay);
    frm.set_value('monthly_technical_bonus', vals.monthly_technical_bonus);
    frm.set_value('overtime_rate', vals.overtime_rate);
    frm.set_value('absence_deduction', vals.absence_deduction);
    frm.set_value('supervision_allowance', vals.supervision_allowance);
    frm.set_value('children_count', vals.children_count);

    frappe.show_alert({
        message: __('مقادیر حقوق با موفقیت اعمال شد. لطفاً ذخیره کنید.'),
        indicator: 'green'
    });

    dialog.hide();
}
