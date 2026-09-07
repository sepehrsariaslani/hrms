# Bulk Salary Slip Refresh Design

## Goal

Allow payroll users to refresh multiple draft Salary Slips from Smart Attendance directly from the Salary Slip list.

## Scope

- Add a list action named «رفرش گروهی از حضور و غیاب».
- Accept one or more selected Salary Slip names.
- Process each selected draft independently through `refresh_from_smart_attendance()`.
- Skip submitted and cancelled slips without modifying them.
- Continue after an individual failure and return per-slip results.
- Reload the list and show a compact success/skip/error summary.

## Design

A whitelisted server function `bulk_refresh_from_smart_attendance(salary_slips)` parses the incoming list, validates it, and processes each item inside its own database savepoint. It checks write permission and draft state before calling the existing single-slip refresh method. Successful refreshes are committed as part of the request; a failed item rolls back only its own savepoint.

The list-view action collects checked records, asks for confirmation, calls the server function, then reports the number refreshed, skipped, and failed. It does not change submitted or cancelled Salary Slips, Journal Entries, Payroll Entries, or MCP.

## Acceptance Criteria

- Selecting draft slips refreshes each selected draft and saves the recalculated employer insurance amount.
- Submitted/cancelled selected slips are skipped.
- A failure in one draft does not stop the remaining drafts.
- The list displays the final count summary and refreshes.
