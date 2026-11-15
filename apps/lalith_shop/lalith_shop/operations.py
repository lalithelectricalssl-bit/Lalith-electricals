"""Read-only shop operations overview and internal collection reminders."""
from collections import defaultdict
from datetime import timedelta
from hashlib import sha256

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate
from erpnext.accounts.report.accounts_receivable.accounts_receivable import execute as accounts_receivable

from lalith_shop.policy import payment_stage

SETTINGS = "Lalith Shop Settings"
AR = "Accounts Receivable"


def allowed_companies():
    if not frappe.has_permission("Company", "read"):
        return []
    return frappe.get_list("Company", fields=["name", "default_currency"], order_by="name", limit=0)


def receivables_allowed():
    return (
        frappe.has_permission("Sales Invoice", "read")
        and frappe.has_permission("Sales Invoice", "report")
        and frappe.get_cached_doc("Report", AR).is_permitted()
    )


def reminder_settings():
    settings = frappe.get_single(SETTINGS)
    return (
        settings.get("enable_payment_reminders") is None or cint(settings.enable_payment_reminders),
        settings.reminder_user or "Administrator",
        3 if settings.get("reminder_lead_days") is None else cint(settings.reminder_lead_days),
    )


def payment_rows(company, today, lead_days):
    # The standard payment ledger report covers credits, partial receipts, and instalments.
    if not receivables_allowed():
        return []

    cutoff = today + timedelta(days=lead_days)
    invoices = frappe.get_list(
        "Sales Invoice",
        filters={
            "company": company, "docstatus": 1, "is_return": 0, "is_pos": 0,
            "posting_date": ["<=", today], "outstanding_amount": [">", 0],
        },
        fields=["name", "customer_name", "po_no", "due_date"],
        limit=0,
    )
    visible = {invoice.name: invoice for invoice in invoices}
    if not visible:
        return []

    _, data, *_ = accounts_receivable({
        "company": company, "report_date": today, "ageing_based_on": "Due Date",
        "based_on_payment_terms": 1, "in_party_currency": 0,
    })
    balances = defaultdict(float)
    for row in data:
        if row.get("voucher_type") != "Sales Invoice" or row.get("voucher_no") not in visible:
            continue
        invoice = visible[row.voucher_no]
        due = row.get("due_date") or invoice.due_date
        if due and getdate(due) <= cutoff and flt(row.get("outstanding")) > 0:
            balances[(invoice.name, getdate(due))] += flt(row.outstanding)

    return [
        {
            "invoice": name, "customer": visible[name].customer_name, "po_no": visible[name].po_no,
            "due": due, "amount": amount, "status": payment_stage(due, today, lead_days),
        }
        for (name, due), amount in sorted(balances.items(), key=lambda entry: (entry[0][1], entry[0][0]))
    ]


def open_orders(company):
    if not frappe.has_permission("Sales Order", "read"):
        return None
    return frappe.get_list(
        "Sales Order",
        fields=["name", "po_no", "customer_name", "delivery_date", "shipping_address_name", "per_delivered", "per_billed", "status"],
        filters={"company": company, "docstatus": 1, "po_no": ["is", "set"], "status": ["not in", ["Cancelled", "Closed", "Completed"]]},
        order_by="delivery_date asc, name asc",
        limit=0,
    )


def active_quotations(company, today):
    if not frappe.has_permission("Quotation", "read"):
        return None
    return len(frappe.get_list(
        "Quotation",
        filters={"company": company, "docstatus": 1, "status": "Open"},
        or_filters=[["valid_till", ">=", today], ["valid_till", "is", "not set"]],
        pluck="name",
        limit=0,
    ))


@frappe.whitelist(methods=["GET"])
def overview(company=None):
    companies = allowed_companies()
    if not companies:
        return {"companies": []}
    choices = {entry.name: entry.default_currency for entry in companies}
    if not company:
        default = frappe.defaults.get_user_default("Company")
        company = default if default in choices else companies[0].name
    if company not in choices:
        frappe.throw(_("You do not have access to this company."), frappe.PermissionError)

    today = getdate(nowdate())
    lead_days = reminder_settings()[2]
    ar_allowed = receivables_allowed()
    payments = payment_rows(company, today, lead_days) if ar_allowed else []
    orders = open_orders(company)
    return {
        "companies": list(choices), "company": company, "currency": choices[company], "date": today,
        "reminder_lead_days": lead_days, "can_view_receivables": bool(ar_allowed),
        "due_soon_amount": sum(row["amount"] for row in payments if row["status"] != "Overdue"),
        "overdue_amount": sum(row["amount"] for row in payments if row["status"] == "Overdue"),
        "payment_count": len(payments), "payments": payments[:6],
        "order_count": len(orders) if orders is not None else None, "orders": (orders or [])[:6],
        "quote_count": active_quotations(company, today),
    }


def notify_payment_reminders():
    enabled, user, lead_days = reminder_settings()
    if not enabled or not frappe.db.exists("User", {"name": user, "enabled": 1, "user_type": "System User"}):
        return
    actor = frappe.session.user
    try:
        frappe.set_user(user)
        if not receivables_allowed():
            return
        today = getdate(nowdate())
        for company in allowed_companies():
            for row in payment_rows(company.name, today, lead_days):
                add_payment_alert(user, row)
    finally:
        frappe.set_user(actor)


def add_payment_alert(user, row):
    invoice, due, status = row["invoice"], row["due"], row["status"]
    key = sha256(f"{user}\0{invoice}\0{due}\0{status}".encode()).hexdigest()
    if frappe.db.exists("Notification Log", key):
        return
    subject = _("{0}: Invoice {1} · {2}").format(_(status), invoice, due)
    frappe.get_doc({
        "doctype": "Notification Log", "type": "Alert", "for_user": user,
        "from_user": "Administrator", "subject": frappe.utils.escape_html(subject),
        "document_type": "Sales Invoice", "document_name": invoice,
    }).insert(set_name=key, ignore_permissions=True, ignore_if_duplicate=True)
