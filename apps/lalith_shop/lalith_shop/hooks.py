app_name = "lalith_shop"
app_title = "Lalith Shop"
app_publisher = "Lalith Electricals"
app_description = "Electrical retail, company supply and repair workflows"
app_email = ""
app_license = "gpl-3.0"
required_apps = ["erpnext"]
after_install = ["lalith_shop.setup.install", "lalith_shop.patches.show_customer_po.execute"]
after_migrate = "lalith_shop.setup.install"
doc_events = {
    "Stock Entry": {"validate": "lalith_shop.repair.validate_link"},
    "Sales Invoice": {"validate": "lalith_shop.repair.validate_link"},
    "Item Price": {
        "on_update": "lalith_shop.price_history.record_save",
        "on_trash": "lalith_shop.price_history.record_delete",
    },
}
doctype_js = {
    doctype: "public/js/shop_forms.js"
    for doctype in ("Sales Invoice", "Quotation", "Delivery Note", "Item", "Item Price")
}
scheduler_events = {"hourly_long": ["lalith_shop.operations.notify_payment_reminders"]}
