# Earned Leave Repair Design

## Goal

Fix `مرخصی استحقاقی` so existing balances on `dehati.ir` match each employee's actual accrual by date of joining, and future accrual adds `2.5` days automatically at the end of each month instead of granting the full annual quota upfront.

## Root Cause

- The current earned-leave allocation flow grants the full annual allocation upfront for earned leave.
- The current earned-leave schedule marks future schedule rows as already allocated.
- On `dehati.ir`, `مرخصی استحقاقی` was also configured with `max_leaves_allowed = 2.5`, but the system interprets that field as the maximum allocation for the whole leave period, not the monthly accrual amount.

## Approved Repair

1. Restore earned-leave policy assignment behavior so new allocations only include accrual for already-passed periods.
2. Ensure future earned-leave schedule rows remain pending until the scheduler reaches their allocation date.
3. Add a repair helper that recalculates current-year earned-leave allocations for a target leave type on a site and updates:
   - `Leave Allocation`
   - initial `Leave Ledger Entry` rows linked to the allocation
   - `Earned Leave Schedule`
4. Run the repair on `dehati.ir` for `مرخصی استحقاقی` as of `2026-08-08`.
5. Correct the site configuration so `max_leaves_allowed` returns to the annual cap (`30`) while monthly accrual continues to come from leave policy annual allocation (`30 / 12 = 2.5`).

## Data Handling Rules

- Preserve all existing `Leave Application` rows.
- Recompute each allocation using the employee's date of joining and the linked leave policy assignment period.
- Keep the submitted allocation records themselves; repair their allocation totals and schedule instead of replacing employee-facing document names.

## Verification

- Inspect `Leave Type`, `Leave Allocation`, `Earned Leave Schedule`, and `Leave Ledger Entry` on `dehati.ir`.
- Confirm no active employee still has a `30` day upfront allocation unless the accrual through `2026-08-08` genuinely equals that amount.
- Confirm future schedule rows remain unallocated before their month-end date.
