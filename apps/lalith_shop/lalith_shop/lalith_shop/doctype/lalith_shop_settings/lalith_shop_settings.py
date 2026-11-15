import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class LalithShopSettings(Document):
    def validate(self):
        if cint(self.reminder_lead_days) < 0:
            frappe.throw(_("Reminder lead days must be zero or greater."))
        if self.enable_payment_reminders and self.reminder_user and not frappe.db.exists(
            "User", {"name": self.reminder_user, "enabled": 1, "user_type": "System User"}
        ):
            frappe.throw(_("Choose an enabled Desk user to receive payment reminders."))
