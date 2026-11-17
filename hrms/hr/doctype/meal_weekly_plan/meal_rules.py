"""Pure reservation quota and meal-plan capacity rules."""

ACTIVE_RESERVATION_STATUSES = frozenset({"Reserved", "Delivered"})


def can_activate_reservation(existing_statuses, target_status):
    """A person may have only one active lunch for a company date."""
    if target_status not in ACTIVE_RESERVATION_STATUSES:
        return True
    return not any(status in ACTIVE_RESERVATION_STATUSES for status in existing_statuses or ())


def has_portion_capacity(reserved_count, max_portions, *, already_reserved=False):
    """Respect a plan row's optional cap while allowing updates to an existing claim."""
    if already_reserved or max_portions in (None, ""):
        return True
    try:
        return int(reserved_count or 0) < int(max_portions)
    except (TypeError, ValueError):
        return False


def retains_existing_portion_claim(
    *, previous_status, previous_plan, previous_date, plan, meal_date
):
    """An active reservation keeps its claim only while it stays on the same plan day."""
    return (
        previous_status in ACTIVE_RESERVATION_STATUSES
        and str(previous_plan or "") == str(plan or "")
        and str(previous_date or "") == str(meal_date or "")
    )
