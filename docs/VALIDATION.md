# Test coverage and remaining work

| Area | Check |
|---|---|
| Local setup | Native ARM64 selection, separate practice credentials and ports, local web binding and Git exclusions |
| Repair rules | Approval, valid quantities and rates, changed quantities and warehouses |
| Print templates | Local rendering tests for the six invoice columns, addresses and escaped fields |
| Credit reminders | Local tests for the configurable due-date window and overdue boundary |
| Backup tooling | File checksums, missing-file detection and stopped services after a failed restore |
| ERPNext integration | Cash POS, quotation sourcing and shipping address, PO-linked delivery and invoice, partial receipts, overdue and paid-state alerts, price history, real PDF generation, purchases and balanced ledger entries |
| Repairs in ERPNext | Approval, draft stock issue, a single deduction, labour billing, locked posted part quantities and collection |
| Backup restoration | Restore a modified fictional note and a modified private file |

The ERPNext integration, repair and restoration checks run in Docker in [GitHub Actions](https://github.com/lalithelectricalssl-bit/Lalith-electricals/actions). The latest run shows which steps passed for a given commit.

## Before real use

- Run the first install and practice workflows on your Mac M2. Test Safari, physical printing, scanners, staff permissions and POS closing.
- Add the branded Letter Head image on the Mac and check that the invoice aligns on the shop's physical printer.
- Enter actual prices, terms, tax templates, opening stock and accounting balances.
- Rehearse recovery from the separate backup drive.
- The repair shortcut covers ordinary spare parts. Serial and batch repairs use the standard stock workflow. Warranty automation and customer notifications remain outside this setup.
- The Docker test covers the shop workflows above. Alternative POS consolidation, returns and the other ERPNext modules need separate tests for your use.
