app_name = "lalith_shop"
app_title = "Lalith Shop"
app_publisher = "Lalith Electricals"
app_description = "Electrical retail, company supply and repair workflows"
app_email = ""
app_license = "gpl-3.0"
required_apps = ["erpnext"]
after_install = "lalith_shop.setup.install"
after_migrate = "lalith_shop.setup.install"
doc_events = {
    "Stock Entry": {"validate": "lalith_shop.repair.validate_link"},
    "Sales Invoice": {"validate": "lalith_shop.repair.validate_link"},
}
