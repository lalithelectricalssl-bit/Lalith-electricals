# Test coverage and remaining work

| Area | Check |
|---|---|
| Local setup | Native ARM64 selection, separate practice credentials and ports, local web binding and Git exclusions |
| Repair rules | Approval, valid quantities and rates, changed quantities and warehouses |
| Print templates | Invoice, quotation and delivery-note HTML rendering with sample records and escaped fields |
| Backup tooling | File checksums, missing-file detection and stopped services after a failed restore |
| ERPNext integration | Cash POS sale, quotation, sales order, delivery, credit invoice, receipts, purchases, supplier payment and balanced ledger entries |
| Repairs in ERPNext | Approval, draft stock issue, a single deduction, labour billing, locked posted part quantities and collection |
| Backup restoration | Restore a modified fictional note and a modified private file |

The last three rows require the Docker integration job in [GitHub Actions](https://github.com/lalithelectricalssl-bit/Lalith-electricals/actions). The latest run shows which steps passed.

## Before real use

- Run the first install and practice workflows on your Mac M2. Test Safari, physical printing, scanners, staff permissions and POS closing.
- Match the exact invoice design when an unlocked invoice or clear image is available.
- Enter actual prices, terms, tax templates, opening stock and accounting balances.
- Rehearse recovery from the separate backup drive.
- The repair shortcut covers ordinary spare parts. Serial and batch repairs use the standard stock workflow. Warranty automation and customer notifications remain outside this setup.
- The Docker test covers the shop workflows above. Alternative POS consolidation, returns and the other ERPNext modules need separate tests for your use.
