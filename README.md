# Lalith Electricals ERPNext

Run actual ERPNext v16.53.0 on your Mac M2. It provides stock, POS, company credit sales, quotations, sales orders, delivery notes, invoices, purchases, suppliers, payments and double-entry accounting. The Lalith Shop app adds a workspace, electrical repair jobs and company print formats.

[Start with the Mac installation guide](docs/MAC_SETUP.md). The practice installation uses fictional customers, a supplier, fans and spare parts in its own database.

## Practice first

Install and open Docker Desktop for Apple Silicon. Install Python 3.11 or newer. Download the project with **Code → Download ZIP**, unzip it and open Terminal in that folder.

```sh
python3 tools/shop.py --demo install
python3 tools/shop.py --demo credentials
```

Open http://localhost:8081 and sign in as **Administrator** with the initial password from Terminal. Search for **Lalith Electricals** or **Electrical Repair Job** in ERPNext.

## Set up the shop

```sh
python3 tools/shop.py --demo stop
python3 tools/shop.py install
python3 tools/shop.py credentials
```

Open http://localhost:8080. Complete ERPNext's setup wizard with your actual company details, then run the next command with the company name you entered.

```sh
python3 tools/shop.py configure --company "Lalith Electricals"
```

The company setup adds a Shop Stock warehouse, item groups, retail and business price lists, a walk-in customer, a repair labour service item and a cash POS profile.

## Operate the system

```sh
python3 tools/shop.py start
python3 tools/shop.py backup
python3 tools/shop.py stop
```

Keep Docker Desktop open and the Mac awake while trading. This setup serves the Mac itself on localhost and has no paid hosting dependency. Docker Desktop is free for qualifying small businesses under [Docker's licence terms](https://docs.docker.com/subscription-billing/desktop-license/).

- [Installation and startup](docs/MAC_SETUP.md)
- [Sales, purchasing, repairs and printing](docs/SHOP_GUIDE.md)
- [Backup and recovery](docs/BACKUPS.md)
- [Checks and remaining work](docs/VALIDATION.md)
- [Versions and licences](docs/UPSTREAM.md)

## Code and test results

GitHub stores the source and fictional test data. Real accounts, passwords, customer invoices and backups stay on your computer. The `.gitignore` excludes generated configuration and backup folders.

[GitHub Actions](https://github.com/lalithelectricalssl-bit/Lalith-electricals/actions) checks the local tools and attempts the ERPNext transactions and a restore on a disposable practice site. See the latest run for the actual result.

The three generic Lalith Company print formats support ERPNext Letter Head. The supplied Word invoice is encrypted, so matching its layout requires an unlocked copy or clear full-page image. Use PDF for a styled document and ERPNext's export for CSV data.
