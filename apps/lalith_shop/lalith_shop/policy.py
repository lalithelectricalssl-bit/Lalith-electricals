from collections import defaultdict
from decimal import Decimal, InvalidOperation

STATUSES = ("Received", "Inspecting", "Awaiting approval", "Approved", "In progress", "Ready", "Collected", "Cancelled")
APPROVAL_REQUIRED = {"Approved", "In progress", "Ready", "Collected"}


def number(value, label, positive=False):
    try:
        result = Decimal(str(0 if value is None else value))
    except InvalidOperation as error:
        raise ValueError(f"{label} must be a number.") from error
    if not result.is_finite() or result < 0 or (positive and result == 0):
        raise ValueError(f"Enter a valid {label.lower()}.")
    return result


def validate_job(status, approved, parts, labour):
    if status not in STATUSES:
        raise ValueError("Choose a repair status.")
    if status in APPROVAL_REQUIRED and not approved:
        raise ValueError("Record the customer's approval first.")
    number(labour, "Labour charge")
    for row in parts:
        if not row.get("item_code") or not row.get("warehouse"):
            raise ValueError("Choose an item and source warehouse for each part.")
        number(row.get("qty"), "Quantity", positive=True)
        number(row.get("rate"), "Rate")


def grouped_parts(rows, warehouse=None, include_rate=False):
    counts = defaultdict(Decimal)
    for row in rows:
        key = (row.get("item_code"), row.get(warehouse) if warehouse else None,
               number(row.get("rate"), "Rate") if include_rate else None)
        counts[key] += number(row.get("qty"), "Quantity", positive=True)
    return dict(counts)
