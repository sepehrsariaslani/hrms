# Employer Insurance Derived From Employee Share

## Goal

Ensure future Iranian Salary Slips calculate the employer insurance share from the actual employee-insurance deduction on the same slip.

## Scope

- Use the submitted/draft Salary Slip deduction with abbreviation `EI` as the source value.
- Calculate employer insurance as `employee_insurance * 23 / 7`.
- Use the derived amount for the Salary Slip display field and for a newly-created individual accrual Journal Entry.
- Preserve all existing Salary Slips and Journal Entries unchanged.

## Design

`SalarySlip.get_employer_insurance_share()` will first read the `EI` deduction in `self.deductions`. When a non-zero employee insurance amount is present, it will return the derived `23 / 7` amount even if `employer_insurance_share_iran` contains an older value. If the deduction is absent, the method will retain the stored field as a backward-compatible fallback for historical/imported slips.

The 23% represents the employer's total statutory burden for this workflow, including unemployment insurance. The employee share is 7%; therefore the derived ratio is 23/7. The calculation is limited to future recalculations and newly created accrual entries. No submitted historical record is rewritten.

## Acceptance Criteria

- A Salary Slip with `EI = 7,000` returns `23,000` employer insurance even if its stored employer-insurance field is `1`.
- A Salary Slip without an `EI` deduction returns its stored employer-insurance field.
- Existing financial summary and journal-creation code continue using `get_employer_insurance_share()`.
- Targeted HRMS payroll tests pass.
