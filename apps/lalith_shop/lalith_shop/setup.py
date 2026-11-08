"""Install shop screens and configure company masters after the ERPNext wizard."""
import json
from pathlib import Path

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def ensure(doctype, name, **values):
    if frappe.db.exists(doctype, name):
        return frappe.get_doc(doctype, name)
    return frappe.get_doc({"doctype": doctype, "name": name, **values}).insert()


def install():
    create_custom_fields({
        dt: [{"fieldname": "custom_lalith_repair_job", "label": "Electrical repair job",
              "fieldtype": "Link", "options": "Electrical Repair Job",
              "insert_after": "company", "read_only": 1, "no_copy": 1}]
        for dt in ("Stock Entry", "Sales Invoice")
    })
    html = (Path(__file__).parent / "templates" / "company_document.html").read_text()
    for doctype, title in (("Sales Invoice", "Invoice"), ("Quotation", "Quotation"), ("Delivery Note", "Delivery Note")):
        ensure("Print Format", f"Lalith Company {title}", doc_type=doctype, module="Lalith Shop",
               custom_format=1, print_format_type="Jinja", html=html, standard="No")
    if frappe.db.exists("Workspace", "Lalith Electricals"):
        return
    sections = {
        "Retail and company sales": [("Point of Sale", "Page", "point-of-sale")] + [
            (name, "DocType", name) for name in ("Quotation", "Sales Order", "Delivery Note", "Sales Invoice", "Customer")],
        "Purchases and stock": [(name, "DocType", name) for name in
            ("Item", "Stock Entry", "Stock Reconciliation", "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Supplier")],
        "Repairs and accounts": [("Electrical Repair Job", "DocType", "Electrical Repair Job"),
            ("Payment Entry", "DocType", "Payment Entry"), ("General Ledger", "Report", "General Ledger"),
            ("Accounts Receivable", "Report", "Accounts Receivable"), ("Accounts Payable", "Report", "Accounts Payable")],
    }
    links, cards = [], []
    for index, (label, items) in enumerate(sections.items()):
        cards.append({"id": f"lalith-{index}", "type": "card", "data": {"card_name": label, "col": 4}})
        links.append({"type": "Card Break", "label": label, "link_count": len(items)})
        links.extend({"type": "Link", "label": text, "link_type": kind, "link_to": target,
                      "is_query_report": int(kind == "Report")} for text, kind, target in items)
    ensure("Workspace", "Lalith Electricals", title="Lalith Electricals", label="Lalith Electricals",
           public=1, module="Lalith Shop", type="Workspace", app="lalith_shop",
           content=json.dumps(cards), links=links)


def configure(company):
    if not frappe.db.exists("Company", company):
        frappe.throw("Complete the setup wizard and enter its exact company name.")
    co = frappe.get_doc("Company", company)
    cash = co.default_cash_account or frappe.db.get_value("Account",
        {"company": company, "account_type": "Cash", "is_group": 0}, "name")
    write_off = co.get("write_off_account") or co.default_expense_account
    if not cash or not write_off or not co.cost_center:
        frappe.throw("Set up the company cash, expense and cost-center accounts before creating the POS profile.")
    for name in ("Electrical Goods", "Electrical Spare Parts", "Electrical Repair Services"):
        ensure("Item Group", name, item_group_name=name, parent_item_group="All Item Groups")
    for name in ("Retail Customers", "Business Customers"):
        ensure("Customer Group", name, customer_group_name=name, parent_customer_group="All Customer Groups")
    for name in ("Lalith Retail", "Lalith Business"):
        ensure("Price List", name, price_list_name=name, currency=co.default_currency, selling=1, enabled=1)
    labour = ensure("Item", "Repair Labour", item_code="Repair Labour", item_name="Electrical repair labour",
                    item_group="Electrical Repair Services", stock_uom="Nos", is_stock_item=0, is_sales_item=1)
    if labour.is_stock_item:
        frappe.throw("Review the existing Repair Labour item and make it a service item.")
    warehouse = ensure("Warehouse", f"Shop Stock - {co.abbr}", warehouse_name="Shop Stock", company=company, is_group=0)
    walk_in = ensure("Customer", "Walk-in Customer", customer_name="Walk-in Customer", customer_type="Individual",
                     customer_group="Retail Customers", territory=co.country)
    payment = ensure("Mode of Payment", "Cash", mode_of_payment="Cash", type="Cash")
    if not any(row.company == company for row in payment.accounts):
        payment.append("accounts", {"company": company, "default_account": cash})
        payment.save()
    profile = ensure("POS Profile", f"Lalith Counter - {co.abbr}", company=company, currency=co.default_currency,
                     warehouse=warehouse.name, selling_price_list="Lalith Retail", customer=walk_in.name,
                     update_stock=1, write_off_account=write_off, write_off_cost_center=co.cost_center,
                     payments=[{"mode_of_payment": "Cash", "default": 1}],
                     applicable_for_users=[{"user": frappe.session.user, "default": 1}])
    frappe.db.commit()
    print(f"Configured {company} with {warehouse.name} and {profile.name}.")
    return {"warehouse": warehouse.name, "profile": profile.name, "cash": cash}
