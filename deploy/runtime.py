"""Bench operations in the ERPNext image."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

BENCH = Path("/home/frappe/frappe-bench")
SITE = os.environ["SITE_NAME"]
CONFIG = BENCH / "sites" / SITE / "site_config.json"


def run(*arguments):
    # Avoid printing command arguments because initialization and restore use passwords.
    result = subprocess.run(["bench", *arguments], cwd=BENCH)
    if result.returncode:
        raise SystemExit(result.returncode)


def site_run(*arguments):
    run("--site", SITE, *arguments)


def initialize():
    if CONFIG.exists():
        site_run("list-apps")
        print("Reusing the existing site.")
        return
    run("new-site", SITE, "--db-root-username", "root", "--db-root-password", os.environ["DB_ROOT_PASSWORD"],
        "--admin-password", os.environ["ADMIN_PASSWORD"], "--mariadb-user-host-login-scope=%",
        "--install-app", "erpnext", "--install-app", "lalith_shop", "--set-default")


def backup():
    path = Path("/tmp/lalith-backup")
    path.mkdir(mode=0o700, exist_ok=True)
    site_run("backup", "--with-files", "--compress", "--ignore-backup-conf", "--backup-path", str(path),
             "--backup-path-db", str(path / "database.sql.gz"),
             "--backup-path-files", str(path / "public-files.tgz"),
             "--backup-path-private-files", str(path / "private-files.tgz"),
             "--backup-path-conf", str(path / "site_config.json"))


def restore():
    path = Path("/tmp/lalith-restore")
    saved_config = json.loads((path / "site_config.json").read_text())
    target_config = json.loads(CONFIG.read_text())
    for key in ("encryption_key", "backup_encryption_key"):
        if key in saved_config:
            target_config[key] = saved_config[key]
    CONFIG.write_text(json.dumps(target_config, indent=2))
    site_run("restore", str(path / "database.sql.gz"), "--with-public-files", str(path / "public-files.tgz"),
             "--with-private-files", str(path / "private-files.tgz"), "--db-root-username", "root",
             "--db-root-password", os.environ["DB_ROOT_PASSWORD"])
    site_run("migrate")
    site_run("clear-cache")


def main():
    action, *args = sys.argv[1:]
    if SITE not in ("lalith.localhost", "demo.localhost"):
        raise SystemExit("Invalid site name.")
    if action in ("demo", "acceptance", "probe") and SITE != "demo.localhost":
        raise SystemExit("Sample data is limited to the practice site.")
    match action:
        case "init":
            initialize()
        case "hold":
            while True:
                time.sleep(60)
        case "configure":
            site_run("execute", "lalith_shop.setup.configure", "--kwargs", json.dumps({"company": args[0]}))
        case "demo":
            site_run("execute", "lalith_shop.sample.prepare")
        case "acceptance":
            site_run("execute", "lalith_shop.sample.run_checks")
        case "probe":
            site_run("execute", "lalith_shop.sample.backup_probe", "--kwargs", json.dumps({"phase": args[0]}))
        case "backup":
            backup()
        case "restore":
            restore()
        case _:
            raise SystemExit("Unknown toolbox operation.")


if __name__ == "__main__":
    main()
