# Payroll Entry Recovery and Employee Liability Design

## Purpose

Recover payroll runs that submitted Salary Slips but failed before their accrual Journal Entry was created. The recovery must create the payable liability against each employee, prevent duplicate accounting entries, and leave payment creation as a separate, explicit action.

## Current failure

`HR-PRUN-2026-00001` on dehati.ir has 19 submitted Salary Slips, no linked accrual Journal Entry, and a stale failed status. The original failure was a missing account for Salary Component `حق اولاد`; that component is now configured. The standard Submit Salary Slips action only selects draft slips, so it cannot recover this state.

## Design

### Recovery action

Add a whitelisted `Payroll Entry` method named `recover_accrual_journal_entry`.

- Only Payroll Entries with submitted Salary Slips and no existing accrual Journal Entry may use it.
- It validates every Salary Component account before making any accounting change, returning all missing components in one error.
- It loads the submitted, unlinked Salary Slips, calls the existing accrual-entry accounting path, and links the created Journal Entry back to those slips.
- It sets the Payroll Entry to `Submitted`, marks `salary_slips_submitted`, and clears the stale failure message only after the Journal Entry submits successfully.
- It refuses recovery when an accrual Journal Entry already exists. A payment Journal Entry is not treated as an accrual Journal Entry.

### Employee-level liability

The recovery action and normal payroll submission must respect Payroll Settings > `process_payroll_accounting_entry_based_on_employee`.

When enabled, each credit to the Payroll Payable account includes `party_type = Employee` and `party = <employee>`. This makes the actual outstanding liability visible per employee and allows later partial payment entries to reduce only that employee's balance.

### Payments and advances

The recovery action never creates, submits, cancels, or modifies payment Journal Entries. Existing payment drafts remain for the user to review.

Mid-month advances are represented by submitted `Employee Advance` documents. Payroll accounting already has a dedicated advance-deduction flow when the deduction comes from an Employee Advance reference; no inferred classification of ordinary bank entries is allowed.

### Interface

Expose a Persian button, `بازیابی سند تعهد حقوق`, on a failed Payroll Entry only when it has submitted Salary Slips without an accrual Journal Entry. The dialog states that it creates a submitted accrual Journal Entry and does not pay employees. On success, show and link to the Journal Entry and refresh the form.

## Error handling

- Missing component account: list all component names and link to each component.
- Existing accrual: link to it and do not create another.
- No submitted unlinked Salary Slips: explain that nothing is eligible for recovery.
- A failed recovery leaves existing documents and status untouched.

## Testing

- Recovery creates one submitted accrual Journal Entry from already-submitted slips and links all slips.
- Recovery uses employee party tagging when the Payroll Setting is enabled.
- Recovery rejects an already-accrued Payroll Entry without creating a second Journal Entry.
- Recovery reports all missing Salary Component accounts before creating any Journal Entry.
- Salary Slip hourly leave creation computes `to_time` relative to `from_time` so hourly leave submission remains valid.

## Scope boundaries

This delivery does not infer historic advances from generic Payment Entries, automatically cancel payment drafts, or alter already-submitted payment vouchers.
