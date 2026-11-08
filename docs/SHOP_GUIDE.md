# Daily shop workflows

Use the **Lalith Electricals** workspace or search for each document in ERPNext. Save creates a draft. Submit posts the transaction. Use ERPNext's standard return, cancel and amend actions for corrections.

## Retail POS

Open the **Lalith Counter** profile and create a POS Opening Entry for the cashier. Use Point of Sale to scan or find items, enter quantities and record the payment. Print the sale and reconcile the shift using POS Closing Entry. Assign the profile to each staff user who operates it.

The acceptance check uses ERPNext v16's **Sales Invoice** mode in POS Settings. In this mode a cash sale posts stock and accounts at submission. ERPNext also offers a separate POS Invoice mode with consolidation at closing. That mode requires its own verification.

## Company credit sales

1. Create the Customer and its billing address, delivery address, business prices and agreed payment terms.
2. Submit a **Quotation**. This leaves stock as it is.
3. Create a **Sales Order** from the accepted quotation and enter the customer's PO number.
4. Create and submit the **Delivery Note** from the sales order. This deducts stock.
5. Create the **Sales Invoice** from that delivery note. Leave Update Stock off for delivered goods.
6. Record and allocate each receipt through **Payment Entry**. Review the remaining balance in Accounts Receivable.

## Purchases and suppliers

Create **Purchase Order → Purchase Receipt → Purchase Invoice → Payment Entry**. The receipt adds stock and the supplier invoice records the amount owed. Create the invoice from the receipt and check Update Stock. Use Accounts Payable to see what remains due.

## Electrical repairs

1. Create an **Electrical Repair Job** for the customer. Enter the appliance, model, serial number and reported fault.
2. Add the estimate and record customer approval before starting work.
3. Enter ordinary spare parts with their source warehouse, quantities and selling rates. Add the **Repair Labour** service item and charge.
4. Save the job. Choose **Create → Prepare spare-parts issue**. Review the draft Material Issue and submit it when parts are used.
5. Choose **Create → Prepare repair invoice**. Review the draft and submit it. The parts were already issued, so the invoice leaves Update Stock off.
6. Record the payment, then mark the job Ready or Collected. A repair with charges requires a submitted invoice before collection.

The repair buttons reopen an active linked document. Parts and company/customer details lock once a linked document exists. Cancel the linked documents before changing those details. Serial or batch controlled spare parts need the standard ERPNext Stock Entry workflow.

## Invoice, quotation and delivery note

Configure your real Letter Head in ERPNext. In Print, choose **Lalith Company Invoice**, **Lalith Company Quotation** or **Lalith Company Delivery Note**. Select the letterhead and print or save as PDF. Delivery notes show quantities, and invoices and quotations show amounts.

The supplied Word invoice is encrypted. The generic formats are ready for review while the exact layout awaits a readable reference. For CSV, export the document list or report with the required fields.

## Accounting

Use ERPNext's General Ledger, Trial Balance, Profit and Loss, Balance Sheet, Accounts Receivable and Accounts Payable. Confirm the financial year, bank and cash accounts, inventory valuation, opening balances and applicable tax templates with the person responsible for the shop's accounts.
