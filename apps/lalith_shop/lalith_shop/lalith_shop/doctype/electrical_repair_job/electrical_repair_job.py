import frappe
from frappe.model.document import Document
from frappe.utils import nowdate

from lalith_shop.policy import grouped_parts, validate_job
from lalith_shop.repair import LINK, active_link, invoice_lines


class ElectricalRepairJob(Document):
    def validate(self):
        try:
            validate_job(self.status, self.customer_approved, self.parts, self.labour_charge)
        except ValueError as error:
            frappe.throw(str(error))
        for row in self.parts:
            item = frappe.db.get_value("Item", row.item_code, ["is_stock_item", "has_serial_no", "has_batch_no"], as_dict=True)
            if not item or not item.is_stock_item or item.has_serial_no or item.has_batch_no:
                frappe.throw("Choose an ordinary spare part. Use ERPNext's standard Stock Entry for serial or batch items.")
            if frappe.db.get_value("Warehouse", row.warehouse, "company") != self.company:
                frappe.throw("Choose a warehouse belonging to this company.")
        if self.labour_item and frappe.db.get_value("Item", self.labour_item, "is_stock_item"):
            frappe.throw("The labour item must be a service item.")
        previous = self.get_doc_before_save()
        if previous:
            frappe.db.sql("SELECT name FROM `tabElectrical Repair Job` WHERE name=%s FOR UPDATE", (self.name,))
        issue = active_link("Stock Entry", self.name) if previous else None
        invoice = active_link("Sales Invoice", self.name) if previous else None
        if previous and (issue or invoice):
            if not self.customer_approved or self.status == "Cancelled":
                frappe.throw("Cancel linked documents before withdrawing approval or cancelling the repair.")
            if (previous.company, previous.customer) != (self.company, self.customer):
                frappe.throw("Company and customer are locked while linked documents exist.")
            if grouped_parts(previous.parts, "warehouse", True) != grouped_parts(self.parts, "warehouse", True):
                frappe.throw("Cancel linked documents before changing spare parts.")
        if previous and invoice and (previous.labour_item, previous.labour_charge) != (self.labour_item, self.labour_charge):
            frappe.throw("Cancel the linked invoice before changing labour charges.")
        if self.status == "Collected" and (self.labour_charge or any(row.rate for row in self.parts)):
            if not invoice or invoice.docstatus != 1:
                frappe.throw("Submit the repair invoice before marking the job Collected.")

    def lock_approved(self):
        self.check_permission("write")
        if self.is_new():
            frappe.throw("Save the repair job first.")
        frappe.db.sql("SELECT name FROM `tabElectrical Repair Job` WHERE name=%s FOR UPDATE", (self.name,))
        self.reload()
        if not self.customer_approved or self.status == "Cancelled":
            frappe.throw("Record customer approval before preparing linked documents.")

    @frappe.whitelist(methods=["POST"])
    def make_stock_entry(self):
        self.lock_approved()
        existing = active_link("Stock Entry", self.name)
        if existing:
            frappe.get_doc("Stock Entry", existing.name).check_permission("read")
            return existing.name
        if not self.parts:
            frappe.throw("Add spare parts first.")
        draft = frappe.get_doc({
            "doctype": "Stock Entry", "stock_entry_type": "Material Issue", "company": self.company,
            LINK: self.name, "remarks": f"Spare parts used for repair {self.name}",
            "items": [{"item_code": row.item_code, "qty": row.qty, "s_warehouse": row.warehouse} for row in self.parts],
        }).insert()
        return draft.name

    @frappe.whitelist(methods=["POST"])
    def make_sales_invoice(self):
        self.lock_approved()
        existing = active_link("Sales Invoice", self.name)
        if existing:
            frappe.get_doc("Sales Invoice", existing.name).check_permission("read")
            return existing.name
        lines = invoice_lines(self)
        if not lines:
            frappe.throw("Add spare parts or a labour charge first.")
        draft = frappe.get_doc({
            "doctype": "Sales Invoice", "company": self.company, "customer": self.customer,
            "posting_date": nowdate(), "due_date": nowdate(), "update_stock": 0, LINK: self.name,
            "remarks": f"Electrical repair {self.name}", "items": lines,
        }).insert()
        return draft.name
