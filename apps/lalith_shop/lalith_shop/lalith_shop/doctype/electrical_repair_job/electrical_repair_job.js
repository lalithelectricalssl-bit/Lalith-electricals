frappe.ui.form.on("Electrical Repair Job", {
  refresh(frm) {
    if (frm.is_new() || frm.doc.status === "Cancelled") return;
    function prepare(method, doctype) {
      if (frm.is_dirty()) {
        frappe.msgprint(__("Save your changes first."));
        return;
      }
      frm.call(method).then(({message}) => {
        if (message) frappe.set_route("Form", doctype, message);
      });
    }
    if (frm.doc.parts?.length) {
      frm.add_custom_button(__("Prepare spare-parts issue"),
        () => prepare("make_stock_entry", "Stock Entry"), __("Create"));
    }
    frm.add_custom_button(__("Prepare repair invoice"),
      () => prepare("make_sales_invoice", "Sales Invoice"), __("Create"));
    for (const doctype of ["Stock Entry", "Sales Invoice"]) {
      frm.add_custom_button(__(doctype), () => frappe.set_route("List", doctype,
        {custom_lalith_repair_job: frm.doc.name}), __("Linked documents"));
    }
  }
});
