frappe.pages["shop-operations"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper, title: __("Shop Operations"), single_column: true,
	});
	const root = document.createElement("main");
	root.className = "lalith-operations";
	page.main[0].appendChild(root);

	const h = (value) => frappe.utils.escape_html(String(value ?? ""));
	const date = (value) => value ? frappe.datetime.str_to_user(value) : __("Unscheduled");
	const links = [
		["Customer POs", "Sales Order", { po_no: ["is", "set"] }],
		["Quotations", "Quotation"],
		["Invoices", "Sales Invoice"],
		["Delivery notes", "Delivery Note"],
		["Payments", "Payment Entry"],
		["Stock", "Item"],
		["Price history", "Lalith Price Change"],
		["Purchasing", "Purchase Order"],
		["Suppliers", "Supplier"],
		["Repairs", "Electrical Repair Job"],
	];
	let company;
	let request = 0;

	function button(label, action, className = "", code = "") {
		return `<button class="shop-button ${className}" type="button" data-action="${action}" data-code="${h(code)}">${h(label)}</button>`;
	}

	function metric(label, value, detail, tone = "") {
		return `<div class="shop-metric ${tone}">
			<div class="shop-metric-label">${h(label)}</div>
			<strong>${h(value ?? "—")}</strong>
			<small>${h(detail)}</small>
		</div>`;
	}

	function orderTable(orders) {
		if (!orders.length) return `<p class="shop-empty">${h(__("No open customer POs."))}</p>`;
		return `<div class="shop-table-scroll"><table class="shop-table">
			<thead><tr><th>${h(__("Customer / PO"))}</th><th>${h(__("Delivery"))}</th><th>${h(__("Order status"))}</th></tr></thead>
			<tbody>${orders.map((order) => `<tr>
				<td>${button(order.customer_name, "order", "shop-text-link", order.name)}
					<small>${h(order.po_no)}</small></td>
				<td>${h(date(order.delivery_date))}<small>${h(order.shipping_address_name)}</small></td>
				<td><span class="shop-badge neutral">${h(__(order.status))}</span></td>
			</tr>`).join("")}</tbody>
		</table></div>`;
	}

	function paymentList(payments, money) {
		if (!payments.length) return `<p class="shop-empty">${h(__("No payments due soon or overdue."))}</p>`;
		const tones = { Overdue: "overdue", "Due today": "today", "Due soon": "soon" };
		return `<ul class="shop-payments">${payments.map((payment) => `<li>
			<div class="shop-payment-info">
				${button(payment.customer, "invoice", "shop-text-link", payment.invoice)}
				<small>${h(payment.po_no || payment.invoice)} · ${h(date(payment.due))}</small>
			</div>
			<div class="shop-payment-amount">
				<strong>${h(money(payment.amount))}</strong>
				<span class="shop-badge ${tones[payment.status]}">${h(__(payment.status))}</span>
			</div>
		</li>`).join("")}</ul>`;
	}

	function render(data) {
		const money = (amount) => new Intl.NumberFormat("en-LK", {
			style: "currency", currency: data.currency || "LKR", currencyDisplay: "code",
			minimumFractionDigits: 2, maximumFractionDigits: 2,
		}).format(amount);

		const navigation = links
			.filter(([, doctype]) => frappe.model.can_read(doctype))
			.map(([label, doctype]) => button(__(label), "list", "shop-nav-link", doctype)).join("");
		const companyOptions = data.companies.map((name) =>
			`<option value="${h(name)}" ${name === company ? "selected" : ""}>${h(name)}</option>`
		).join("");
		const canCreateOrder = frappe.model.can_create("Sales Order");
		const canCreateQuote = frappe.model.can_create("Quotation");
		root.innerHTML = `
			<aside class="shop-sidebar">
				<div class="shop-brand"><div class="shop-mark" aria-hidden="true">↯</div><strong>Lalith Electricals</strong></div>
				<nav class="shop-nav" aria-label="${h(__("Shop navigation"))}">
					<span class="shop-nav-link selected" aria-current="page">${h(__("Overview"))}</span>
					${navigation}
				</nav>
			</aside>
			<div class="shop-content">
				<header class="shop-header">
					<div>
						<p class="shop-date">${h(date(data.date))}</p>
						<h2>${h(__("Shop overview"))}</h2>
					</div>
					<div class="shop-toolbar">
						<select class="shop-company" aria-label="${h(__("Company"))}">${companyOptions}</select>
						${button(__("Refresh"), "refresh", "shop-secondary")}
					</div>
				</header>
				<div class="shop-actions">
					${canCreateOrder ? button(__("Record customer PO"), "new-order", "shop-primary") : ""}
					${canCreateQuote ? button(__("New quotation"), "new-quote", "shop-secondary") : ""}
					${frappe.model.can_create("Payment Entry") ? button(__("Record payment"), "new-payment", "shop-secondary") : ""}
					${frappe.model.can_read("POS Profile") ? button(__("Point of sale"), "pos", "shop-secondary") : ""}
				</div>
				<div class="shop-metrics">
					${metric(__("Overdue"), data.can_view_receivables ? money(data.overdue_amount) : null, __("Past the payment date"), "metric-overdue")}
					${metric(__("Due soon"), data.can_view_receivables ? money(data.due_soon_amount) : null, __("Today through the next {0} days", [data.reminder_lead_days]), "metric-soon")}
					${metric(__("Open customer POs"), data.order_count, __("To deliver or invoice"), "metric-orders")}
					${metric(__("Active quotations"), data.quote_count, __("Open and valid"), "metric-quotes")}
				</div>
				<div class="shop-panels">
					<section class="shop-panel">
						<div class="shop-panel-head">
							<h3>${h(__("Customer purchase orders"))}</h3>
							${data.order_count != null ? button(__("View all"), "list", "shop-text-link", "Sales Order") : ""}
						</div>
						${data.order_count != null ? orderTable(data.orders) : `<p class="shop-empty">${h(__("Sales Order access is required."))}</p>`}
					</section>
					<section class="shop-panel">
						<div class="shop-panel-head">
							<h3>${h(__("Payment reminders"))}</h3>
							${data.can_view_receivables ? button(__("Receivables"), "receivables", "shop-text-link") : ""}
						</div>
						${data.can_view_receivables ? paymentList(data.payments, money) : `<p class="shop-empty">${h(__("Accounts Receivable access is required."))}</p>`}
					</section>
				</div>
				<footer class="shop-footer">
					${frappe.model.can_read("Lalith Shop Settings") ? button(__("Reminder settings"), "settings", "shop-text-link") : ""}
				</footer>
			</div>`;
	}

	async function refresh(showLoading = false) {
		const token = ++request;
		if (showLoading || !root.innerHTML) {
			root.innerHTML = `<p role="status" class="shop-message">${h(__("Loading shop operations…"))}</p>`;
		}
		root.setAttribute("aria-busy", "true");
		try {
			const response = await frappe.call({
				method: "lalith_shop.operations.overview", type: "GET", args: company ? { company } : {},
			});
			if (token !== request) return;
			const data = response.message;
			if (!data.companies.length) {
				root.innerHTML = `<p class="shop-message">${h(__("Complete company setup or ask for access to a company."))}</p>`;
				return;
			}
			company = data.company;
			render(data);
		} catch {
			if (token === request) {
				root.innerHTML = `<div class="shop-message" role="status">${h(__("Could not load shop operations."))}
					${button(__("Try again"), "refresh", "shop-secondary")}</div>`;
			}
		} finally {
			if (token === request) root.setAttribute("aria-busy", "false");
		}
	}

	root.addEventListener("change", (event) => {
		if (!event.target.matches(".shop-company")) return;
		company = event.target.value;
		refresh();
	});

	root.addEventListener("click", (event) => {
		if (root.getAttribute("aria-busy") === "true") return;
		const button = event.target.closest("button[data-action]");
		if (!button) return;
		const { action, code } = button.dataset;
		switch (action) {
			case "new-order": frappe.new_doc("Sales Order", { company }); break;
			case "new-quote": frappe.new_doc("Quotation", { company, quotation_to: "Customer" }); break;
			case "new-payment": frappe.new_doc("Payment Entry", { company, payment_type: "Receive" }); break;
			case "pos": frappe.set_route("point-of-sale"); break;
			case "settings": frappe.set_route("Form", "Lalith Shop Settings", "Lalith Shop Settings"); break;
			case "order": frappe.set_route("Form", "Sales Order", code); break;
			case "invoice": frappe.set_route("Form", "Sales Invoice", code); break;
			case "receivables": frappe.set_route("query-report", "Accounts Receivable", {
				company, based_on_payment_terms: 1, ageing_based_on: "Due Date",
			}); break;
			case "list": {
				const [, doctype, filters] = links.find(([, doctype]) => doctype === code);
				const globalMaster = ["Item", "Supplier", "Lalith Price Change"].includes(doctype);
				frappe.set_route("List", doctype, globalMaster ? {} : { company, ...filters });
				break;
			}
			case "refresh": refresh(true); break;
		}
	});

	wrapper.refresh_shop_operations = refresh;
};

frappe.pages["shop-operations"].on_page_show = function (wrapper) {
	wrapper.refresh_shop_operations?.();
};
