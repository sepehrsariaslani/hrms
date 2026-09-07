# Zero-Amount Hourly Additional Salary Summary Design

## Goal

Display hourly Additional Salary hours on Salary Slip even when Smart Attendance deliberately sends zero monetary amount.

## Scope

- Accumulate `Hours` Additional Salary records before the zero-value row removal check.
- Keep zero-value components out of earnings/deductions when `remove_if_zero_valued` is enabled.
- Do not alter the Salary Slip monetary totals.
- Preserve blank `hour_rate_type`: such rows increase the earning/deduction total but not ordinary/overtime subtotals.

## Design

`SalarySlip.add_additional_salary_components()` currently skips a zero-value component before calling `accumulate_additional_salary_hours()`. The method will call the accumulation function immediately after loading component metadata, then keep the existing zero-value skip for creating monetary rows. This changes only the read-only hours summary fields.

## Acceptance Criteria

- A zero-amount, Hours-based earning with 3 hours increases `additional_earning_hours` by 3.
- The same record does not create a monetary Salary Detail row when its component removes zero values.
- Salary gross pay, deductions, and net pay remain unchanged.
