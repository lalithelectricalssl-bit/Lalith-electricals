(() => {
	if (frappe.lalith_shop_forms_loaded) return;
	frappe.lalith_shop_forms_loaded = true;

	const formats = {
		"Sales Invoice": "Lalith Electricals Invoice",
		"Quotation": "Lalith Electricals Quotation",
		"Delivery Note": "Lalith Electricals Delivery Note",
	};
	for (const [doctype, format] of Object.entries(formats)) {
		frappe.ui.form.on(doctype, {
			refresh(frm) {
				if (frm.is_new() || !frappe.model.can_print_doc(frm)) return;
				frm.add_custom_button(__("Download PDF"), () => {
					const params = new URLSearchParams({
						doctype: frm.doctype,
						name: frm.docname,
						format,
						no_letterhead: "0",
					});
					window.open("/api/method/frappe.utils.print_format.download_pdf?" + params, "_blank", "noopener");
				});
			},
		});
	}

	frappe.ui.form.on("Sales Invoice", {
		refresh(frm) {
			if (frm.doc.docstatus !== 0 || frm.doc.is_pos || frm.doc.is_return || !frm.doc.posting_date) return;
			if ((frm.doc.payment_schedule || []).length > 1) return;
			frm.add_custom_button(__("Set credit days"), () => {
				const date = frm.doc.payment_schedule?.[0]?.due_date || frm.doc.due_date;
				frappe.prompt([{
					fieldname: "days", label: __("Days from posting date"), fieldtype: "Int",
					reqd: 1, default: date ? frappe.datetime.get_diff(date, frm.doc.posting_date) : 0,
				}], async ({ days }) => {
					if (!Number.isInteger(days) || days < 0) {
						frappe.throw(__("Enter a whole number of credit days, zero or greater."));
					}
					const due = frappe.datetime.add_days(frm.doc.posting_date, days);
					const term = frm.doc.payment_schedule?.[0];
					if (!term && frm.doc.payment_terms_template) {
						frappe.throw(__("Select and load the payment terms before setting a credit period."));
					}
					await frm.set_value("due_date", due);
					if (term) await frappe.model.set_value(term.doctype, term.name, "due_date", due);
				}, __("Set credit days"), __("Apply"));
			});
		},
	});

	for (const doctype of ["Item", "Item Price"]) {
		frappe.ui.form.on(doctype, {
			refresh(frm) {
				if (frm.is_new() || !frappe.model.can_read("Lalith Price Change")) return;
				const item_code = frm.doc.item_code;
				if (item_code) frm.add_custom_button(__("Price history"), () => {
					frappe.set_route("List", "Lalith Price Change", { item_code });
				});
			},
		});
	}
})();
