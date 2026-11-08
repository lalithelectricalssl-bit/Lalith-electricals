# Install ERPNext on a Mac M2

## 1. Install the prerequisites

1. Download **Docker Desktop for Mac with Apple silicon** from the [official Mac installation page](https://docs.docker.com/desktop/setup/install/mac-install/). Install it and wait for the Docker engine to start.
2. Install **Python 3.11 or newer** from [Python's macOS downloads](https://www.python.org/downloads/macos/).
3. Open **Terminal** from Applications → Utilities and run these commands.

```sh
python3 --version
docker compose version
docker info
```

Docker needs enough space for images, records and backups. Close memory-heavy apps during the first install on an 8 GB Mac. If Docker reports a memory error, check its Resources settings.

## 2. Download the project folder

Open [Lalith-electricals on GitHub](https://github.com/lalithelectricalssl-bit/Lalith-electricals). Choose **Code → Download ZIP**. Double-click the ZIP and open Terminal in the extracted folder.

```sh
cd ~/Downloads/Lalith-electricals-main
```

If your folder is elsewhere, type `cd ` with a space, drag the folder into Terminal and press Return. Keep the folder in a permanent location after installation.

## 3. Try the practice installation

```sh
python3 tools/shop.py --demo install
python3 tools/shop.py --demo credentials
```

The first command downloads the ERPNext image, builds the custom app and creates an isolated practice site. Leave Terminal open until it prints the address. The second command prints the initial password for **Administrator**.

Open http://localhost:8081 in Safari. The company is **Lalith Practice Shop**. Try a sample sale and the [shop workflows](SHOP_GUIDE.md). The practice site has 10 sample fans and 20 sample capacitors at the start.

## 4. Create your real shop site

Stop the practice site before starting the shop site on a small-memory Mac.

```sh
python3 tools/shop.py --demo stop
python3 tools/shop.py install
python3 tools/shop.py credentials
```

Open http://localhost:8080. Sign in as **Administrator** and complete the setup wizard. Choose Sri Lanka, LKR, Asia/Colombo, your actual company name and the correct financial year. Then run the company setup command.

```sh
python3 tools/shop.py configure --company "Lalith Electricals"
```

Use the exact company name from the wizard. Add your items, barcode numbers, suppliers, company customers, price lists and agreed credit terms. Set opening stock, accounts, tax templates and staff roles before posting real transactions. Add your logo and shop details in ERPNext's **Letter Head**.

## 5. Start and stop each day

Open Docker Desktop and return to the project folder in Terminal.

```sh
python3 tools/shop.py start
```

Open http://localhost:8080. Reconcile the day's POS and payments, then back up the records and stop the services.

```sh
python3 tools/shop.py backup
python3 tools/shop.py stop
```

For practice, put `--demo` before the command. Use [the backup guide](BACKUPS.md) to keep a separate copy.

## If an error appears

```sh
python3 tools/shop.py status
python3 tools/shop.py logs
```

Use `--demo` for a practice-site error. Share the error text after removing private details. The generated `.env` files and backup folders contain confidential information. Keep those files local.

If port 8080 is busy, change just `HTTP_PORT` in the local `.env` to a free port above 1024 and run start. Back up before upgrading ERPNext or replacing Docker data. Test upgrades on practice records first. Removing Docker volumes erases the site database.
