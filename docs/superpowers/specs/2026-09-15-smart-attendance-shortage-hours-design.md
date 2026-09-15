# Smart Attendance Shortage Hours Design

**Date:** 2026-09-15

## Goal

Make `shortage_hours_iran` in Iranian salary slips equal the current Smart Attendance report for the same employee and payroll period, including approved leaves and overnight check-ins.

## Confirmed failure

For `HR-EMP-00015` (محمدرضا فهمیده), the Khordad period currently reports about `15.04` shortage hours even though the source attendance shows only minute-level shortage. The inflated value comes from two full-day `time_off` values:

- An overnight OUT is shown again as a single log on an approved compensatory-leave day.
- The OUT at `00:03` on the day after the payroll period is excluded because the query ends at the period end, so the final day is treated as a missing OUT.

The salary slip copies the report's `time_off` total, so the shared report calculation must be corrected first.

## Design

1. Read one calendar day after `to_date` solely so an overnight IN on the last reported day can be paired with its early-morning OUT. The extra-day row itself is never emitted in the report.
2. Mark every cross-calendar-day OUT consumed by a pair as used, including pairs found while scanning an IN. This prevents the same OUT from appearing as a second single-log row on the next day.
3. Apply approved leave precedence after all attendance branches. A day with approved hourly or full-day leave, including compensatory leave, must not contribute to `time_off`, even when a stray or incomplete check-in exists. The incomplete-log indicator remains visible for attendance follow-up.
4. Make salary-slip shortage lookup recompute from the current Smart Attendance rows instead of returning a nonzero stored value first. This prevents stale `shortage_hours_iran` from surviving after attendance or leave edits.
5. Refresh only the draft Khordad slip for محمدرضا فهمیده after deployment; do not submit it and do not modify raw check-in records.

## Non-goals

- Do not alter Employee Checkin data, Attendance records, leave applications, or shift assignments.
- Do not change overtime semantics except where the same corrected overnight pair naturally changes the day's working calculation.
- Do not hard-code `HR-EMP-00015`; all employees receive the corrected generic logic.

## Acceptance criteria

- An approved-leave day with one stray OUT has `time_off == 0` and retains an attendance issue indicator.
- An IN on the final payroll day paired with an OUT before 08:00 on the following day is complete and does not add a full-day shortage.
- The following-day OUT is not displayed or counted again as a separate row.
- Salary-slip `shortage_hours_iran` equals the fresh Smart Attendance shortage for the same employee and dates, even if the document previously contained a stale nonzero value.
- Existing overtime and ordinary minute-level shortage calculations remain unchanged.

## Verification

Add regression tests for the three behaviors above, run the focused Smart Attendance and Salary Slip tests, then run the relevant HRMS test suite. Finally recalculate the target draft slip and compare its stored fields with the live report.
