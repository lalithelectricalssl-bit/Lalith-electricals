# Backup and restore

From the project folder with Docker Desktop running, run the backup after closing the day's transactions.

```sh
python3 tools/shop.py backup
```

The tool briefly pauses the site and writes the database, public and private attachments and site configuration into a dated folder under `.local/backups/shop`. It checks file hashes before reporting success. The practice site uses `.local/backups/practice`.

Copy the entire dated folder to a separate encrypted drive. The snapshot contains confidential shop records and encryption keys. Use an encrypted location because the archives themselves are unencrypted.

## Check a backup copy

Replace the example path with the full path printed by the backup command.

```sh
python3 tools/shop.py verify-backup "/full/path/to/dated-backup-folder"
```

This detects missing or damaged files. Run a practice restore to verify the database and attachments open.

## Restore an existing site or recover on a new Mac

1. Use the same ERPNext and app versions recorded in the backup. On a new Mac, install a fresh site with the same practice or shop mode first.
2. Verify the copied folder.
3. Run the command below. It asks you to type the target site name, then takes a safety backup and replaces the site's records. Use `--demo` to restore a practice snapshot.

```sh
python3 tools/shop.py restore "/full/path/to/dated-backup-folder"
```

The tool restores the database, attachments and encryption key and keeps the target's database connection settings. A failed restore leaves the web and worker services stopped. Keep the error and safety backup for recovery.

Check stock, customer and supplier balances, the General Ledger, a saved attachment and a printable invoice before trading. Login credentials return to those in the backup.

## Practice restore test

```sh
python3 tools/shop.py --demo restore-check
```

The test creates a fictional note and private attachment, backs them up, changes both, restores the snapshot and verifies their original contents. Use the daily backup command for the shop's real records.
