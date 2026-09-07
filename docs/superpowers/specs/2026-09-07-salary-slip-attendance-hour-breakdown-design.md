# Salary Slip Attendance Hour Breakdown Design

## Goal

Show a clear attendance-hour breakdown on Iranian Salary Slips, including presence, deducted breaks, net work, overtime, and regular work.

## Fields

- `presence_hours_iran` — ساعات حضور: total time from recorded entry to exit before deducted breaks.
- `break_hours_iran` — ساعات استراحت: total deductible break time based on assigned Break Hours rules.
- `net_worked_hours_iran` — ساعات کارکرد خالص: `presence_hours_iran - break_hours_iran`; includes overtime because it is actual net work time.
- `regular_worked_hours_iran` — ساعات کارکرد عادی: `max(net_worked_hours_iran - overtime_hours_iran, 0)`; excludes overtime.

## Design

The Smart Attendance report is the sole source. Its rows already expose `presence_hours`, `break_hours`, `working_hours`, and `overtime`. `apply_smart_attendance_summary()` will sum these values per Salary Slip employee and period, calculate regular work defensively, and write the four read-only fields. The existing `worked_hours_iran` remains unchanged for compatibility.

The fields are placed in the existing «خلاصه کارکرد هوشمند» section, before the previous generic work-hours field, and each has an inline Persian description explaining the source and formula. Single and bulk Salary Slip refresh already call this calculation path, so no separate refresh logic is needed.

## Acceptance Criteria

- The four fields are created for Salary Slip with Persian labels and descriptions.
- Presence, break, net, overtime, and regular work obey the documented formulas.
- Values refresh on individual and bulk Smart Attendance refresh.
- Existing `worked_hours_iran`, payroll amounts, and submitted historical records are not changed.
