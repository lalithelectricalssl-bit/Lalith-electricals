frappe.listview_settings["Lalith Price Change"] = {
	add_fields: ["event", "currency", "previous_currency"],
	formatters: {
		old_rate(value, field, row) {
			return ["Updated", "Deleted"].includes(row.event) ? format_currency(value, row.previous_currency) : "—";
		},
		new_rate(value, field, row) {
			return row.event === "Deleted" ? "—" : format_currency(value, row.currency);
		},
	},
};
