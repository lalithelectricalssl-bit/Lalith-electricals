"""Keep an audit record alongside ERPNext Item Price records."""
from decimal import Decimal

import frappe
from frappe.utils import now_datetime

HISTORY = "Lalith Price Change"
SCOPE = ("item_code", "price_list", "currency", "uom", "customer", "supplier", "batch_no", "packing_unit")
DATES = ("valid_from", "valid_upto")
FIELDS = (*SCOPE, *DATES, "price_list_rate")


def snapshot(price, fields=FIELDS):
    return {field: price.get(field) for field in fields}


def record_save(price, method=None):
    before = price.get_doc_before_save()
    if before is None:
        write_change(price, "Created")
    elif snapshot(before) != snapshot(price):
        write_change(price, "Updated", before)


def record_delete(price, method=None):
    write_change(price, "Deleted", price)


def write_change(price, event, before=None):
    old_rate = before.price_list_rate if before else None
    new_rate = price.price_list_rate if event != "Deleted" else None
    comparable = (
        old_rate and new_rate is not None
        and before and snapshot(before, SCOPE) == snapshot(price, SCOPE)
    )
    percent = None
    if comparable:
        previous, current = Decimal(str(old_rate)), Decimal(str(new_rate))
        percent = (current - previous) / previous * 100

    record = {
        "doctype": HISTORY,
        **snapshot(price, (*SCOPE, *DATES)),
        "source_item_price": price.name,
        "event": event,
        "old_rate": old_rate,
        "previous_currency": before.currency if before else None,
        "new_rate": new_rate,
        "change_percent": percent,
        "comparable": int(bool(comparable)),
        "changed_on": now_datetime(),
        "changed_by": frappe.session.user,
    }
    if before and event == "Updated" and snapshot(before, (*SCOPE, *DATES)) != snapshot(price, (*SCOPE, *DATES)):
        record["previous_context"] = frappe.as_json(snapshot(before, (*SCOPE, *DATES)))

    frappe.get_doc(record).insert(ignore_permissions=True)


def backfill_current_prices():
    """Record existing prices once, without assigning a synthetic past change date."""
    recorded = set(frappe.get_all(HISTORY, distinct=True, pluck="source_item_price"))
    for row in frappe.get_all("Item Price", fields=["name", *FIELDS]):
        if row.name not in recorded:
            write_change(row, "Opening price")
