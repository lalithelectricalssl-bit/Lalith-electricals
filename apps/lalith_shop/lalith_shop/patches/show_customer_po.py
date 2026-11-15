"""Show ERPNext's purchase order reference near the customer on Sales Order."""
import json

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
    doctype = "Sales Order"
    meta = frappe.get_meta(doctype, cached=False)
    current_order = [field.fieldname for field in meta.fields]
    po_fields = ("po_no", "po_date")
    field_order = [name for name in current_order if name not in po_fields]
    position = field_order.index("customer_name") + 1
    field_order[position:position] = po_fields
    if field_order != current_order:
        make_property_setter(doctype, None, "field_order", json.dumps(field_order), "Data", for_doctype=True)
    if meta.get_field("po_no").label == "Customer's Purchase Order":
        make_property_setter(doctype, "po_no", "label", "Customer PO Number", "Data")
