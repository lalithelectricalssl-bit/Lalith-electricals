# Daily shop workflows

Open **Shop Operations** from the **Lalith Electricals** workspace or search for it in ERPNext. The dashboard shows open customer POs, active quotations, and upcoming and overdue amounts for the selected company. Use its buttons to create records or open the linked lists. Save creates a draft. Submit posts the transaction. Use ERPNext's return, cancel and amend actions for corrections.

## Retail POS

Open the **Lalith Counter** profile and create a POS Opening Entry for the cashier. Use Point of Sale to scan or find items, enter quantities and record the payment. Print the sale and reconcile the shift using POS Closing Entry. Assign the profile to each staff user who operates it.

The acceptance check uses ERPNext v16's **Sales Invoice** mode in POS Settings. In this mode a cash sale posts stock and accounts at submission. ERPNext also offers a separate POS Invoice mode with consolidation at closing. That mode requires its own verification.

## Company credit sales

1. Set up the **Customer**, its billing and shipping addresses, business pricing and agreed payment terms.
2. Use **New quotation** to enter the customer, product, quantity, price, validity date and **Shipping Address**. Expand an item row to record its optional **Source supplier**. ERPNext saves the most recent update time and keeps the prices on the quotation. Download the PDF when it is ready to share.
3. Use **Record customer PO** to open a **Sales Order**, or create the order from an accepted quotation. Below **Customer**, enter the reference printed on the customer's PO in **Customer PO Number**. Fill in the PO date if provided, check delivery quantities and location, and submit the order.
4. Use **Create → Delivery Note** on the submitted order. Enter the actual shipment quantities and submit when goods leave stock. Print or download the Delivery Note for the receiver to sign.
5. Use **Create → Sales Invoice** on the submitted Delivery Note. ERPNext copies the PO reference and invoices the delivery. **Update Stock** stays off because the Delivery Note already posted the stock movement. If billing ahead of dispatch, ERPNext also supports creating an invoice from the Sales Order. Leave **Update Stock** off when using a Delivery Note for the stock movement.
6. Set the payment terms before submitting. For a draft with a single payment, use **Set credit days** to count from the posting date. For instalments, adjust the individual due dates in **Payment Terms**. Set the customer's **Payment Terms Template** for recurring terms.
7. Open the invoice and create a **Payment Entry** for each receipt, including partial payments. Check the outstanding balance under **Accounts Receivable**.

## Credit reminders

The **Payment reminders** panel shows unpaid invoice instalments due today, within the reminder window, or past due. ERPNext applies posted receipts and credits before calculating the balances. Shop Operations starts with a three-day window. A System Manager can open **Reminder settings** to change the lead time, choose an authorized Desk user, or turn off bell notifications. The dashboard remains available.

The scheduler checks hourly while ERPNext is running. It places one notification in the recipient's bell for each invoice, due date and reminder stage. It catches an overdue payment when the shop system comes back online. The first recipient is **Administrator**. The selected user needs access to the relevant company, invoices and Accounts Receivable. Staff can share the PDF or contact the customer from their normal channels.

## Inventory and item prices

Use **Item** to manage inventory items and **Stock Balance** to check quantities by warehouse. Use **Item Price** to maintain separate selling and supplier prices and their validity dates. Save a changed rate on an Item Price, or create a new dated rate when a price takes effect later.

Use **Price history** on the dashboard, Item or Item Price. Filter by item, price list, supplier or customer. Each entry shows the rates, effective dates and who recorded the change. Open the entry for the percentage change when the two rates use the same pricing context. Older quotations and invoices keep their saved transaction prices. Existing Item Price records appear as opening prices when the update is installed.

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

Use **Download PDF** on a saved, printable document. Use **Print** and select **Lalith Electricals Invoice**, **Lalith Electricals Quotation** or **Lalith Electricals Delivery Note** to preview it and select a different letterhead. The invoice uses Letter paper and the shop's **Number**, **Items**, **Units**, **QTY**, **Unit Cost** and **Amount** headings. It includes the customer details, PO reference, total in words and signature lines. Delivery notes show quantities for receipt, and quotations show the price, delivery address and validity date.

To use the original branding, open **Letter Head → New**, choose the **Image** source, upload the supplied letterhead PNG and set it as default for the shop site. Use **Center** alignment and set the image width to **700 px**. Save the letterhead and confirm the invoice preview with a sample order. To adjust the layout, open **Print Format → Lalith Electricals Invoice** in ERPNext. Its editable Jinja and CSS stay in the shop database and are included in backups. To use a different format, select it in **Print**.

## Accounting

Use ERPNext's General Ledger, Trial Balance, Profit and Loss, Balance Sheet, Accounts Receivable and Accounts Payable. Confirm the financial year, bank and cash accounts, inventory valuation, opening balances and applicable tax templates with the person responsible for the shop's accounts.
