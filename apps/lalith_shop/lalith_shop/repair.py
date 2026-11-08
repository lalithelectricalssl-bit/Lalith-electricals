import frappe

from lalith_shop.policy import grouped_parts

LINK = "custom_lalith_repair_job"


def active_link(doctype, job):
    if doctype not in ("Stock Entry", "Sales Invoice"):
        raise ValueError("Invalid repair document type.")
    result = frappe.db.sql(
        f"SELECT name, docstatus FROM `tab{doctype}` WHERE {LINK}=%s AND docstatus<2 ORDER BY creation LIMIT 1 FOR UPDATE",
        (job,), as_dict=True,
    )
    return result[0] if result else None


def invoice_lines(job):
    lines = [{"item_code": row.item_code, "qty": row.qty, "rate": row.rate, "warehouse": row.warehouse} for row in job.parts]
    if job.labour_charge:
        if not job.labour_item:
            frappe.throw("Choose a labour service item.")
        lines.append({"item_code": job.labour_item, "qty": 1, "rate": job.labour_charge})
    return lines


def validate_link(doc, method=None):
    previous = doc.get_doc_before_save()
    job_name = doc.get(LINK)
    if previous and previous.get(LINK) and previous.get(LINK) != job_name:
        frappe.throw("Cancel the linked document before changing its repair reference.")
    if not job_name:
        return
    job = frappe.get_doc("Electrical Repair Job", job_name)
    job.lock_approved()
    existing = active_link(doc.doctype, job.name)
    if existing and existing.name != doc.name:
        frappe.throw("This repair already has an active linked document.")
    if job.company != doc.company:
        frappe.throw("Choose the same company as the repair job.")
    try:
        if doc.doctype == "Stock Entry":
            if doc.stock_entry_type != "Material Issue":
                frappe.throw("Use Material Issue for repair parts.")
            expected = grouped_parts(job.parts, "warehouse")
            actual = grouped_parts(doc.items, "s_warehouse")
        else:
            if doc.customer != job.customer or doc.update_stock:
                frappe.throw("Use the repair customer and leave Update Stock off.")
            issue = active_link("Stock Entry", job.name)
            if job.parts and (not issue or issue.docstatus != 1):
                frappe.throw("Submit the spare-parts issue before billing this job.")
            expected = grouped_parts(invoice_lines(job), include_rate=True)
            actual = grouped_parts(doc.items, include_rate=True)
        if expected != actual:
            frappe.throw("The document lines must match the approved repair.")
    except ValueError as error:
        frappe.throw(str(error))
