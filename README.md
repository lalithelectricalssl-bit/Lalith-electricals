# Lalith Electricals — ERPNext on your Mac

This project runs **real ERPNext v16.53.0**, with a small electrical-shop customization app. ERPNext supplies POS, company credit sales, accounts, purchases, suppliers, stock, quotations, sales orders, delivery notes, invoices, payments and reports. The custom app adds repair intake, approval, spare-part issues, labour billing and company print formats.

The software runs on your own Mac M2 using Docker Desktop. There is no paid hosting dependency. The pinned ERPNext image includes a native ARM64 image for Apple Silicon. GitHub stores this source code and runs checks; your business database stays in Docker volumes on your computer.

**Begin here: [Mac installation, step by step](docs/MAC_SETUP.md).** Try the separate practice installation first. It uses fictional records and port 8081. The real shop installation uses separate volumes and port 8080.

## Quick start after installing Docker Desktop and Python 3.11+

Download this repository with **Code → Download ZIP**, unzip it, and open Terminal in the extracted folder.

```sh
python3 tools/shop.py --demo install
python3 tools/shop.py --demo credentials
```

Open **http://localhost:8081** and sign in as **Administrator** using the generated password shown by the second command.

When you are ready to configure the real shop:

```sh
python3 tools/shop.py --demo stop
python3 tools/shop.py install
python3 tools/shop.py credentials
```

Open **http://localhost:8080**, complete ERPNext's setup wizard with your actual company details, then:

```sh
python3 tools/shop.py configure --company "Lalith Electricals"
```

Use the exact company name you entered in the wizard. Shop setup creates item groups, retail/business price lists, a Shop Stock warehouse, a walk-in customer, a Repair Labour service item and a cash POS profile. It preserves existing prices, tax settings and account mappings.

## Daily operation

```sh
python3 tools/shop.py start
python3 tools/shop.py status
python3 tools/shop.py backup
python3 tools/shop.py stop
```

Add `--demo` before the command when operating the practice installation. Keep Docker Desktop running and the Mac awake while using the system. This installation is accessible only on the same computer; LAN access and public hosting are not configured.

- [Daily sales, company supplies and repairs](docs/SHOP_GUIDE.md)
- [Backups, verification and restoration](docs/BACKUPS.md)
- [What is checked and what still needs review](docs/VALIDATION.md)
- [Versions and upstream sources](docs/UPSTREAM.md)

## Invoice design and exports

The app provides **Lalith Company Invoice**, **Lalith Company Quotation** and **Lalith Company Delivery Note** print formats. They use your ERPNext Letter Head. In a document, open Print, select the format, then print or download PDF.

The previously supplied invoice file was encrypted, so its exact design has **not** been reproduced. Upload an unlocked copy or clear full-page image before matching the letterhead. No invoice attachment, actual customer list, bank details, passwords or real business transactions are included here.

Use ERPNext's list/report **Export** for CSV. CSV contains values; print/PDF preserves the visual letterhead.

## Checks

GitHub Actions runs:
1. Local tooling, backup-integrity, repair-policy and print-template checks.
2. A disposable ERPNext installation with fictional sales, company credit payments, purchasing, supplier payments, repairs and ledger checks.
3. A database-and-private-file backup/restore check on that practice site.

See the current **[Actions results](https://github.com/lalithelectricalssl-bit/Lalith-electricals/actions)**. A committed workflow is not evidence that it passed; check its latest result and [validation notes](docs/VALIDATION.md).

## Cost and first use

ERPNext has no software licence fee. Docker Desktop is free for qualifying small businesses under Docker's current terms (fewer than 250 employees and less than US$10 million annual revenue). You supply the computer, storage, electricity, backups and maintenance. Downloading the images initially requires internet; normal local work does not require a hosting subscription.

Before official use, enter and reconcile opening stock, opening balances, taxes, bank/cash accounts, credit terms and staff permissions. Confirm them with the person responsible for your accounts. Live Mac hardware, printers and your exact tax/letterhead configuration must be checked on your machine.

## Licence

The customization code is GPL-3.0-or-later. ERPNext/Frappe retain their own licences. Vendored Docker configuration is covered by its included Frappe Docker MIT licence. This project is not an official Frappe product.

