#!/usr/bin/env python3
"""Run the shop's ERPNext installation or its isolated practice copy."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import secrets
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v16.53.0"
APP_VERSION = "0.1.0"
RUNTIME = ("backend", "frontend", "websocket", "worker-short", "worker-long", "scheduler")
PYTHON = "/home/frappe/frappe-bench/env/bin/python"
TOOL = "/home/frappe/lalith_runtime.py"


def checksum(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_settings(path):
    result = {}
    for line in path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or not re.fullmatch("[A-Z_]+", key) or not re.fullmatch("[a-zA-Z0-9_.:/-]+", value):
            raise ValueError("Use plain KEY=value entries in the local configuration file.")
        result[key] = value
    return result


def verify_backup(folder):
    manifest = json.loads((folder / "manifest.json").read_text())
    if manifest.get("format") != 1 or manifest.get("erpnext_version") != VERSION or manifest.get("app_version") != APP_VERSION:
        raise ValueError("Use the project version recorded in this backup.")
    checksums = manifest.get("sha256", {})
    required = {"database.sql.gz", "public-files.tgz", "private-files.tgz", "site_config.json"}
    if set(checksums) != required:
        raise ValueError("Backup is missing a database, file archive or site configuration.")
    for name, expected in checksums.items():
        path = folder / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Missing or unsafe backup file: {name}")
        if checksum(path) != expected:
            raise ValueError(f"Checksum failed: {name}")
    return manifest


class Shop:
    def __init__(self, demo=False):
        self.demo = demo
        self.mode = "practice" if demo else "shop"
        self.site = "demo.localhost" if demo else "lalith.localhost"
        self.project = "lalith_demo" if demo else "lalith_erp"
        self.env_file = ROOT / (".env.demo" if demo else ".env")

    def initialize(self):
        if self.env_file.exists():
            return
        machine = platform.machine().lower()
        if machine not in ("arm64", "aarch64", "x86_64", "amd64"):
            raise ValueError("This installation supports Apple Silicon and x86-64.")
        values = {
            "LALITH_PLATFORM": "linux/arm64" if machine in ("arm64", "aarch64") else "linux/amd64",
            "SITE_NAME": self.site,
            "HTTP_PORT": 8081 if self.demo else 8080,
            "DB_PASSWORD": secrets.token_hex(32),
            "ADMIN_PASSWORD": secrets.token_hex(24),
        }
        fd = os.open(self.env_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write("".join(f"{key}={value}\n" for key, value in values.items()))

    @property
    def settings(self):
        if not self.env_file.exists():
            raise ValueError("Run install first.")
        config = read_settings(self.env_file)
        if config.get("SITE_NAME") != self.site:
            raise ValueError("The site name does not match this installation.")
        if config.get("LALITH_PLATFORM") not in ("linux/arm64", "linux/amd64"):
            raise ValueError("Select linux/arm64 or linux/amd64.")
        port = config.get("HTTP_PORT", "")
        if not port.isdecimal() or not 1024 <= int(port) <= 65535:
            raise ValueError("Choose an HTTP_PORT from 1024 to 65535.")
        for field in ("DB_PASSWORD", "ADMIN_PASSWORD"):
            if not re.fullmatch(r"[0-9a-f]{48,64}", config.get(field, "")):
                raise ValueError("Use the generated configuration from the installer.")
        return config

    def docker(self, *args, capture=False, check=True, env=None):
        process = subprocess.run(["docker", *args], cwd=ROOT, env=env, text=True,
                                 stdout=subprocess.PIPE if capture else None)
        if check and process.returncode:
            raise RuntimeError("Docker reported an error. Read the output above, or run the logs command.")
        return process.stdout or ""

    def compose(self, *args, capture=False, check=True):
        # Explicitly use this site's configuration even if the shell sets a conflicting variable.
        env = os.environ | self.settings
        return self.docker("compose", "--project-name", self.project, "--env-file", str(self.env_file),
                           "-f", str(ROOT / "compose.yaml"), *args, capture=capture, check=check, env=env)

    def check_docker(self):
        if not shutil.which("docker"):
            raise RuntimeError("Install Docker Desktop for Apple Silicon and open it first. See docs/MAC_SETUP.md.")
        self.docker("info", capture=True)
        self.docker("compose", "version", capture=True)

    def tool(self, *args):
        self.compose("run", "--rm", "--no-deps", "-T", "toolbox", *args)

    def install(self):
        self.initialize()
        self.compose("build", "--pull", "backend")
        self.compose("up", "-d", "--wait", "db", "redis-cache", "redis-queue")
        self.compose("run", "--rm", "--no-deps", "-T", "configurator")
        self.tool("init")
        if self.demo:
            self.tool("demo")
        self.start()
        print("Use Administrator and the password shown by the credentials command.")

    def start(self):
        self.compose("up", "-d", "--no-build", *RUNTIME)
        url = f"http://localhost:{self.settings['HTTP_PORT']}"
        for _ in range(90):
            try:
                with urllib.request.urlopen(url + "/api/method/ping", timeout=3) as response:
                    if json.load(response).get("message") == "pong":
                        print(f"ERPNext is ready at {url}")
                        return
            except (OSError, ValueError):
                time.sleep(2)
        raise RuntimeError("ERPNext is still starting or has an error. Run the logs command.")

    @contextmanager
    def pause(self, resume_on_error=True):
        running = self.compose("ps", "--status", "running", "--services", capture=True).split()
        paused = [service for service in RUNTIME if service in running]
        if paused:
            self.compose("stop", "-t", "90", *paused)
        successful = False
        try:
            yield
            successful = True
        finally:
            if paused and (successful or resume_on_error):
                self.compose("start", *paused)
            elif paused:
                print("Restore failed. The shop services are stopped.", file=sys.stderr)

    @contextmanager
    def maintenance(self):
        name = self.project + "-maintenance-" + secrets.token_hex(5)
        self.compose("run", "-d", "--no-deps", "--name", name, "toolbox", "hold", capture=True)
        try:
            yield name
        finally:
            self.docker("rm", "-f", name, capture=True, check=False)

    def backup(self):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(3)
        folder = ROOT / ".local" / "backups" / self.mode / stamp
        folder.mkdir(parents=True, mode=0o700)
        with self.pause(), self.maintenance() as container:
            self.docker("exec", container, PYTHON, TOOL, "backup")
            self.docker("cp", f"{container}:/tmp/lalith-backup/.", str(folder))
        names = ("database.sql.gz", "public-files.tgz", "private-files.tgz", "site_config.json")
        manifest = {
            "format": 1,
            "erpnext_version": VERSION,
            "app_version": APP_VERSION,
            "source_site": self.site,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sha256": {name: checksum(folder / name) for name in names},
        }
        for path in folder.iterdir():
            path.chmod(0o600)
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (folder / "manifest.json").chmod(0o600)
        verify_backup(folder)
        print(f"Verified backup saved at {folder}")
        return folder

    def restore(self, folder, confirm=None):
        manifest = verify_backup(folder)
        if manifest.get("source_site") != self.site:
            raise ValueError("Choose a backup from the same site mode.")
        if confirm is None:
            confirm = input(f"To replace records in {self.site}, type the site name: ").strip()
        if confirm != self.site:
            raise ValueError("Restore cancelled.")
        self.backup()
        with self.pause(resume_on_error=False), self.maintenance() as container:
            self.docker("exec", "-u", "root", container, "mkdir", "-p", "/tmp/lalith-restore")
            for filename in manifest["sha256"]:
                self.docker("cp", str(folder / filename), f"{container}:/tmp/lalith-restore/{filename}")
            self.docker("exec", "-u", "root", container, "chown", "-R", "frappe", "/tmp/lalith-restore")
            self.docker("exec", container, PYTHON, TOOL, "restore")
        print("Restore completed. Check stock, balances and a saved attachment.")

    def acceptance(self):
        if not self.demo:
            raise ValueError("Use --demo for acceptance checks.")
        self.tool("acceptance")

    def restore_check(self):
        if not self.demo:
            raise ValueError("Use --demo for the backup restore check.")
        self.tool("probe", "create")
        folder = self.backup()
        self.tool("probe", "change")
        self.restore(folder, self.site)
        self.tool("probe", "verify")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Use the isolated practice site on port 8081.")
    parser.add_argument("command", choices=("install", "start", "stop", "status", "logs", "credentials",
                        "configure", "backup", "verify-backup", "restore", "acceptance", "restore-check"))
    parser.add_argument("folder", nargs="?", type=Path)
    parser.add_argument("--company")
    args = parser.parse_args()
    shop = Shop(args.demo)
    if args.command in ("verify-backup", "restore") and not args.folder:
        parser.error("Provide the backup folder.")
    if args.command == "verify-backup":
        verify_backup(args.folder)
        print("Backup files and checksums are valid.")
        return
    if args.command == "credentials":
        print("Administrator initial password:", shop.settings["ADMIN_PASSWORD"])
        return
    shop.check_docker()
    match args.command:
        case "install":
            shop.install()
        case "start":
            shop.start()
        case "stop":
            shop.compose("stop")
        case "status":
            shop.compose("ps")
        case "logs":
            shop.compose("logs", "--tail", "100")
        case "configure":
            if not args.company:
                parser.error("Provide --company with the company name from the setup wizard.")
            shop.tool("configure", args.company)
        case "backup":
            shop.backup()
        case "restore":
            shop.restore(args.folder.resolve())
        case "acceptance":
            shop.acceptance()
        case "restore-check":
            shop.restore_check()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
