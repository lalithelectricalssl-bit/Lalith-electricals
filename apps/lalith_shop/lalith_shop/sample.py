"""Fictional practice records and acceptance checks for the isolated site."""
from pathlib import Path

import frappe
from frappe.utils import flt, getdate, nowdate, now_datetime

from lalith_shop.setup import configure, ensure

COMPANY = "Lalith Practice Shop"
CUSTOMER = "Sample Business Customer"
SUPPLIER = "Sample Electrical Supplier"
FAN = "SAMPLE-FAN"
PART = "SAMPLE-CAPACITOR"


def demo_only():
    if frappe.local.site != "demo.localhost":
        frappe.throw("Run these operations on the practice site.")
    frappe.set_user("Administrator")


def post(values):
    doc = frappe.get_doc(values).insert()
    doc.submit()
    return doc


def prepare():
    demo_only()
    if not frappe.db.exists("Company", COMPANY):
        from erpnext.setup.setup_wizard.setup_wizard import setup_complete

        year = getdate(nowdate()).year
        setup_complete(frappe._dict({
            "country": "Sri Lanka", "currency": "LKR", "company_name": COMPANY,
            "company_abbr": "LPS", "chart_of_accounts": "Standard", "domain": "Distribution",
            "fy_start_date": f"{year}-01-01", "fy_end_date": f"{year}-12-31",
            "language": "english", "time_zone": "Asia/Colombo",
        }))
        frappe.db.set_single_value("System Settings", "setup_complete", 1)
        frappe.db.set_single_value("System Settings", "time_zone", "Asia/Colombo")
        frappe.db.set_single_value("Stock Settings", "allow_negative_stock", 0)
    shop = configure(COMPANY)
    ensure("Customer", CUSTOMER, customer_name=CUSTOMER, customer_type="Company",
           customer_group="Business Customers", territory="Sri Lanka", default_price_list="Lalith Business")
    ensure("Supplier", SUPPLIER, supplier_name=SUPPLIER, supplier_type="Company", supplier_group="Electrical")
    for code, title, group, cost, retail, business in (
        (FAN, "Sample ceiling fan", "Electrical Goods", 2500, 5000, 4500),
        (PART, "Sample fan capacitor", "Electrical Spare Parts", 200, 600, 500),
    ):
        ensure("Item", code, item_code=code, item_name=title, item_group=group, stock_uom="Nos",
               is_stock_item=1, valuation_rate=cost,
               item_defaults=[{"company": COMPANY, "default_warehouse": shop["warehouse"]}])
        for price_list, rate in (("Lalith Retail", retail), ("Lalith Business", business)):
            if not frappe.db.exists("Item Price", {"item_code": code, "price_list": price_list}):
                frappe.get_doc({"doctype": "Item Price", "item_code": code, "price_list": price_list,
                                "price_list_rate": rate}).insert()
    if not frappe.db.exists("Stock Entry", {"company": COMPANY, "remarks": "Fictional practice opening stock"}):
        post({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": COMPANY,
              "remarks": "Fictional practice opening stock", "items": [
                  {"item_code": FAN, "qty": 10, "t_warehouse": shop["warehouse"], "basic_rate": 2500},
                  {"item_code": PART, "qty": 20, "t_warehouse": shop["warehouse"], "basic_rate": 200},
              ]})
    frappe.db.commit()
    return shop


def stock(code, warehouse):
    return flt(frappe.db.get_value("Bin", {"item_code": code, "warehouse": warehouse}, "actual_qty"))


def balanced(doc):
    entries = frappe.get_all("GL Entry", filters={"voucher_type": doc.doctype, "voucher_no": doc.name,
                            "is_cancelled": 0}, fields=["debit", "credit"])
    assert entries, f"Missing ledger entries for {doc.doctype}"
    assert abs(sum(flt(row.debit) - flt(row.credit) for row in entries)) < 0.001


def pay(invoice, amount, cash):
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

    entry = get_payment_entry(invoice.doctype, invoice.name, party_amount=amount, bank_account=cash)
    entry.mode_of_payment = "Cash"
    entry.paid_amount = entry.received_amount = amount
    for row in entry.references:
        row.allocated_amount = amount
    entry.insert()
    entry.submit()
    balanced(entry)
    invoice.reload()


def run_checks():
    from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
    from erpnext.selling.doctype.quotation.quotation import make_sales_order
    from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
    from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
    from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

    shop = prepare()
    warehouse = shop["warehouse"]
    before = stock(FAN, warehouse)
    opened = post({"doctype": "POS Opening Entry", "company": COMPANY, "pos_profile": shop["profile"],
        "user": "Administrator", "period_start_date": now_datetime(),
        "balance_details": [{"mode_of_payment": "Cash", "opening_amount": 0}]})
    sale = post({"doctype": "Sales Invoice", "company": COMPANY, "customer": "Walk-in Customer",
        "is_pos": 1, "update_stock": 1, "pos_profile": shop["profile"], "pos_opening_entry": opened.name,
        "selling_price_list": "Lalith Retail", "set_warehouse": warehouse,
        "items": [{"item_code": FAN, "qty": 2, "rate": 5000, "warehouse": warehouse}],
        "payments": [{"mode_of_payment": "Cash", "amount": 10000}]})
    assert stock(FAN, warehouse) == before - 2
    assert flt(sale.outstanding_amount) == 0
    balanced(sale)
    print("PASS cash POS sale updates stock and accounts")

    quote = post({"doctype": "Quotation", "quotation_to": "Customer", "party_name": CUSTOMER,
        "company": COMPANY, "transaction_date": nowdate(), "selling_price_list": "Lalith Business",
        "items": [{"item_code": FAN, "qty": 1, "rate": 4500, "warehouse": warehouse}]})
    assert stock(FAN, warehouse) == before - 2
    order = make_sales_order(quote.name)
    order.delivery_date = nowdate()
    for row in order.items:
        row.delivery_date = nowdate()
        row.warehouse = warehouse
    order.insert()
    order.submit()
    delivery = make_delivery_note(order.name)
    delivery.set_warehouse = warehouse
    for row in delivery.items:
        row.warehouse = warehouse
    delivery.insert()
    delivery.submit()
    assert stock(FAN, warehouse) == before - 3
    invoice = make_sales_invoice(delivery.name)
    invoice.insert()
    invoice.submit()
    assert not invoice.update_stock
    assert stock(FAN, warehouse) == before - 3
    assert flt(invoice.outstanding_amount) == 4500
    balanced(invoice)
    pay(invoice, 2000, shop["cash"])
    assert flt(invoice.outstanding_amount) == 2500
    pay(invoice, 2500, shop["cash"])
    assert flt(invoice.outstanding_amount) == 0
    print("PASS quotation, sales order, delivery, credit invoice and partial payment")

    order = post({"doctype": "Purchase Order", "company": COMPANY, "supplier": SUPPLIER,
        "schedule_date": nowdate(), "items": [
            {"item_code": FAN, "qty": 3, "rate": 2500, "warehouse": warehouse, "schedule_date": nowdate()}]})
    receipt = make_purchase_receipt(order.name)
    receipt.insert()
    receipt.submit()
    assert stock(FAN, warehouse) == before
    bill = make_purchase_invoice(receipt.name)
    bill.bill_no = f"SAMPLE-BILL-{order.name}"
    bill.bill_date = nowdate()
    bill.insert()
    bill.submit()
    balanced(bill)
    assert stock(FAN, warehouse) == before
    pay(bill, bill.grand_total, shop["cash"])
    assert flt(bill.outstanding_amount) == 0
    print("PASS purchase receipt, supplier invoice and payment")

    parts_before = stock(PART, warehouse)
    repair = frappe.get_doc({"doctype": "Electrical Repair Job", "customer": CUSTOMER, "company": COMPANY,
        "appliance": "Sample fan", "fault": "Fictional capacitor fault", "status": "Received",
        "labour_item": "Repair Labour", "labour_charge": 1500,
        "parts": [{"item_code": PART, "qty": 1, "warehouse": warehouse, "rate": 500}]}).insert()
    try:
        repair.make_stock_entry()
    except frappe.ValidationError:
        pass
    else:
        raise AssertionError("Repair allowed an issue before approval")
    repair.customer_approved = 1
    repair.status = "Approved"
    repair.save()
    issue = repair.make_stock_entry()
    assert repair.make_stock_entry() == issue
    assert stock(PART, warehouse) == parts_before
    frappe.get_doc("Stock Entry", issue).submit()
    assert stock(PART, warehouse) == parts_before - 1
    bill_name = repair.make_sales_invoice()
    assert repair.make_sales_invoice() == bill_name
    repair_bill = frappe.get_doc("Sales Invoice", bill_name)
    repair_bill.submit()
    assert repair_bill.grand_total == 2000
    assert stock(PART, warehouse) == parts_before - 1
    balanced(repair_bill)
    repair.reload()
    repair.parts[0].qty = 2
    try:
        repair.save()
    except frappe.ValidationError:
        repair.reload()
    else:
        raise AssertionError("The posted part quantity could be edited")
    repair.status = "Collected"
    repair.save()
    print("PASS repair approval, single stock issue, labour invoice and collection")

    for doc, format_name in ((invoice, "Invoice"), (quote, "Quotation"), (delivery, "Delivery Note")):
        html = frappe.get_print(doc.doctype, doc.name, print_format=f"Lalith Company {format_name}")
        assert doc.name in html and "Sample ceiling fan" in html
    print("PASS invoice, quotation and delivery-note HTML printing")
    frappe.db.commit()


def backup_probe(phase):
    demo_only()
    title = "Lalith fictional backup probe"
    note_name = frappe.db.get_value("Note", {"title": title}, "name")
    filename = "sample-backup-test.txt"
    file_name = frappe.db.get_value("File", {"file_name": filename}, "name")
    if phase == "create":
        if not note_name:
            note_name = frappe.get_doc({"doctype": "Note", "title": title, "content": "Sample before restore"}).insert().name
        if not file_name:
            file_name = frappe.get_doc({"doctype": "File", "file_name": filename,
                "is_private": 1, "content": "Sample private file before restore",
                "attached_to_doctype": "Note", "attached_to_name": note_name}).insert().name
        frappe.db.set_value("Note", note_name, "content", "Sample before restore")
        Path(frappe.get_doc("File", file_name).get_full_path()).write_text("Sample private file before restore")
    elif phase == "change":
        frappe.db.set_value("Note", note_name, "content", "Changed after snapshot")
        Path(frappe.get_doc("File", file_name).get_full_path()).write_text("Changed file after snapshot")
    elif phase == "verify":
        assert frappe.db.get_value("Note", note_name, "content") == "Sample before restore"
        assert Path(frappe.get_doc("File", file_name).get_full_path()).read_text() == "Sample private file before restore"
        print("PASS restored the original database record and private file contents")
    else:
        raise ValueError("Unknown restore check phase.")
    frappe.db.commit()
