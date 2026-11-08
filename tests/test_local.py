import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from jinja2 import Environment, StrictUndefined
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "lalith_shop"))
from lalith_shop.policy import grouped_parts, validate_job
from tools import shop


class RepairRules(unittest.TestCase):
    def test_inspection_is_allowed_before_approval_but_work_is_not(self):
        validate_job("Inspecting", False, [], 0)
        for status in ("Approved", "In progress", "Ready", "Collected"):
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "approval"):
                validate_job(status, False, [], 100)

    def test_invalid_parts_are_rejected(self):
        base = {"item_code": "SAMPLE", "warehouse": "Shop", "qty": 1, "rate": 500}
        for field, value in (("qty", 0), ("qty", -1), ("qty", "Infinity"), ("rate", "NaN"),
                             ("rate", -100), ("warehouse", ""), ("item_code", "")):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate_job("Received", False, [{**base, field: value}], 0)

    def test_grouping_detects_rate_and_warehouse_changes(self):
        row = {"item_code": "SAMPLE", "warehouse": "Shop", "qty": 1.5, "rate": 500}
        self.assertEqual(grouped_parts([row], "warehouse", True),
                         grouped_parts([{**row, "qty": "1.500", "rate": "500.00"}], "warehouse", True))
        self.assertNotEqual(grouped_parts([row], "warehouse", True),
                            grouped_parts([{**row, "warehouse": "Other"}], "warehouse", True))


class LocalSetup(unittest.TestCase):
    def test_practice_and_production_have_independent_credentials_and_ports(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(shop, "ROOT", Path(tmp)):
            practice, production = shop.Shop(demo=True), shop.Shop()
            practice.initialize()
            production.initialize()
            self.assertNotEqual(practice.project, production.project)
            self.assertNotEqual(practice.settings["HTTP_PORT"], production.settings["HTTP_PORT"])
            self.assertNotEqual(practice.settings["DB_PASSWORD"], production.settings["DB_PASSWORD"])
            self.assertEqual(production.env_file.stat().st_mode & 0o777, 0o600)
            original = production.settings["ADMIN_PASSWORD"]
            production.initialize()
            self.assertEqual(production.settings["ADMIN_PASSWORD"], original)

    def test_arm64_platform_selection(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(shop, "ROOT", Path(tmp)), patch.object(shop.platform, "machine", return_value="arm64"):
            instance = shop.Shop()
            instance.initialize()
            self.assertEqual(instance.settings["LALITH_PLATFORM"], "linux/arm64")

    def test_web_port_and_credential_scope(self):
        config = yaml.safe_load((ROOT / "compose.yaml").read_text())
        ports = [(name, value) for name, svc in config["services"].items() for value in svc.get("ports", [])]
        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0][0], "frontend")
        self.assertTrue(ports[0][1].startswith("127.0.0.1:"))
        self.assertNotIn("DB_ROOT_PASSWORD", config["services"]["backend"]["environment"])

    def test_actual_records_and_backups_are_ignored(self):
        paths = [".env", ".env.demo", ".local/backups/shop/example/database.sql.gz",
                 "sites/lalith.localhost/site_config.json", "private/invoice.pdf"]
        result = subprocess.run(["git", "check-ignore", "--no-index", *paths], cwd=ROOT,
                                text=True, capture_output=True)
        self.assertEqual(set(result.stdout.splitlines()), set(paths))

    def test_sample_checks_refuse_production(self):
        with self.assertRaisesRegex(ValueError, "--demo"):
            shop.Shop().acceptance()
        with self.assertRaisesRegex(ValueError, "--demo"):
            shop.Shop().restore_check()


class Backups(unittest.TestCase):
    def test_corrupt_and_missing_backups_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            names = ("database.sql.gz", "public-files.tgz", "private-files.tgz", "site_config.json")
            for name in names:
                (folder / name).write_text("fictional")
            (folder / "manifest.json").write_text(json.dumps({
                "format": 1, "erpnext_version": shop.VERSION, "app_version": shop.APP_VERSION,
                "sha256": {name: shop.checksum(folder / name) for name in names},
            }))
            shop.verify_backup(folder)
            (folder / "database.sql.gz").write_text("corrupt")
            with self.assertRaisesRegex(ValueError, "Checksum"):
                shop.verify_backup(folder)
            (folder / "database.sql.gz").unlink()
            with self.assertRaisesRegex(ValueError, "Missing"):
                shop.verify_backup(folder)

    def test_failed_restore_keeps_web_services_stopped(self):
        instance = shop.Shop()
        calls = []
        def fake_compose(*args, **kwargs):
            calls.append(args)
            return "backend\nfrontend\ndb\n"
        instance.compose = fake_compose
        with self.assertRaises(RuntimeError):
            with instance.pause(resume_on_error=False):
                raise RuntimeError("restore error")
        self.assertIn(("stop", "-t", "90", "backend", "frontend"), calls)
        self.assertFalse(any(call[0] == "start" for call in calls))


class Doc(SimpleNamespace):
    def get(self, key, default=None):
        return getattr(self, key, default)

    def get_formatted(self, key):
        return str(self.get(key, ""))


class Printing(unittest.TestCase):
    def test_print_formats_render_and_escape_user_fields(self):
        source = ROOT / "apps" / "lalith_shop" / "lalith_shop" / "templates" / "company_document.html"
        template = Environment(undefined=StrictUndefined).from_string(source.read_text())
        item = Doc(item_name="<script>bad()</script>", qty=1, uom="Nos", rate=500, amount=500)
        for doctype in ("Sales Invoice", "Quotation", "Delivery Note"):
            doc = Doc(doctype=doctype, company="Lalith Practice Shop", name="DEMO-01", docstatus=0,
                      customer_name="Sample & Co", posting_date="2026-01-01", items=[item],
                      net_total=500, grand_total=500, outstanding_amount=500)
            html = template.render(doc=doc, letter_head=None, no_letterhead=False, footer=None)
            self.assertIn("DEMO-01", html)
            self.assertIn("Sample &amp; Co", html)
            self.assertNotIn("<script>bad()", html)
            self.assertEqual("Net total" in html, doctype != "Delivery Note")


if __name__ == "__main__":
    unittest.main()
