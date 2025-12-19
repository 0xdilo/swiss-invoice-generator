<script>
  import {
    getClients,
    getTemplates,
    getTemplateFields,
    createInvoice,
    getInvoices,
    updateInvoice,
    deleteInvoice,
    updateInvoiceStatus,
    getPartners,
    addRecurringFee,
  } from "$lib/api.js";
  import { onMount } from "svelte";
  let clients = [],
    templates = [],
    invoices = [],
    partners = [];
  let client_id = "",
    template_id = "";
  let dynamicFields = [];
  let dynamicData = {};
  let items = [{ desc: "", price: 0, qty: 1 }];
  let invoiceUrl = "";
  let editing = null;
  let logoUploadFile = null;
  let showLogoUploadUI = false;
  let partner_a_share = 50;
  let partner_b_share = 50;
  let statusFilter = "";
  let showForm = false;
  let isRecurring = false;
  let recurringFrequency = "yearly";
  let invoiceTitle = "";
  let invoiceDescription = "";

  const AUTO_FIELDS = [
    "client",
    "customer",
    "items",
    "subtotal",
    "net_total",
    "total",
    "qr_image",
    "invoice_number",
    "date",
    "logo",
  ];

  async function load() {
    [clients, templates, invoices, partners] = await Promise.all([
      getClients(),
      getTemplates(),
      getInvoices(),
      getPartners()
    ]);
    if (partners.length >= 2) {
      partner_a_share = partners[0].default_share;
      partner_b_share = partners[1].default_share;
    }
  }
  onMount(load);

  $: filteredInvoices = statusFilter
    ? invoices.filter(inv => inv.status === statusFilter)
    : invoices;

  $: stats = {
    total: invoices.length,
    draft: invoices.filter(i => !i.status || i.status === 'draft').length,
    sent: invoices.filter(i => i.status === 'sent').length,
    paid: invoices.filter(i => i.status === 'paid').length,
    totalAmount: invoices.reduce((sum, i) => sum + (i.total_amount || 0), 0),
    paidAmount: invoices.filter(i => i.status === 'paid').reduce((sum, i) => sum + (i.total_amount || 0), 0),
  };

  $: if (template_id) {
    getTemplateFields(template_id).then((res) => {
      const allFields = res.fields || [];
      dynamicFields = allFields.filter((f) => {
        if (AUTO_FIELDS.includes(f)) return false;
        if (f.startsWith("client.")) return false;
        if (f.startsWith("customer.")) return false;
        if (f.startsWith("item.")) return false;
        if (f.startsWith("items")) return false;
        if (f.startsWith("loop.")) return false;
        return true;
      });
      showLogoUploadUI = allFields.includes("logo");
    });
  } else {
    dynamicFields = [];
    showLogoUploadUI = false;
  }

  $: itemsTotal = items.reduce((sum, item) => sum + (item.price * item.qty), 0);

  function addItem() {
    items = [...items, { desc: "", price: 0, qty: 1 }];
  }

  function removeItem(index) {
    if (items.length > 1) {
      items = items.filter((_, i) => i !== index);
    }
  }

  async function submit() {
    const isoDate = dynamicData.date || new Date().toISOString().split("T")[0];
    const data = { ...dynamicData, items, date: isoDate };
    const totalAmount = items.reduce((sum, item) => sum + (item.price * item.qty), 0);

    if (editing !== null) {
      const res = await updateInvoice(
        editing,
        client_id,
        template_id,
        data,
        logoUploadFile ? logoUploadFile[0] : null,
        partner_a_share,
        partner_b_share,
        invoiceTitle,
        invoiceDescription
      );
      invoiceUrl = `http://localhost:8000/invoices/${res.id}/pdf?t=${Date.now()}`;

      if (isRecurring && client_id) {
        const description = items.length > 0 ? items[0].desc : "Recurring service";
        await addRecurringFee(client_id, {
          amount: totalAmount,
          currency: "CHF",
          frequency: recurringFrequency,
          start_date: isoDate,
          description: description,
        });
      }

      editing = null;
    } else {
      const res = await createInvoice(
        client_id,
        template_id,
        data,
        logoUploadFile ? logoUploadFile[0] : null,
        partner_a_share,
        partner_b_share,
        invoiceTitle,
        invoiceDescription
      );
      invoiceUrl = `http://localhost:8000/invoices/${res.id}/pdf?t=${Date.now()}`;

      if (isRecurring && client_id) {
        const description = items.length > 0 ? items[0].desc : "Recurring service";
        await addRecurringFee(client_id, {
          amount: totalAmount,
          currency: "CHF",
          frequency: recurringFrequency,
          start_date: isoDate,
          description: description,
        });
      }
    }
    resetForm();
    showForm = false;
    await load();
  }

  function resetForm() {
    dynamicData = {};
    items = [{ desc: "", price: 0, qty: 1 }];
    client_id = "";
    template_id = "";
    logoUploadFile = null;
    isRecurring = false;
    recurringFrequency = "yearly";
    invoiceTitle = "";
    invoiceDescription = "";
    if (partners.length >= 2) {
      partner_a_share = partners[0].default_share;
      partner_b_share = partners[1].default_share;
    }
  }

  function edit(inv) {
    editing = inv.id;
    client_id = inv.client_id;
    template_id = inv.template_id;
    partner_a_share = inv.partner_a_share || 50;
    partner_b_share = inv.partner_b_share || 50;
    invoiceTitle = inv.title || "";
    invoiceDescription = inv.description || "";
    const d = JSON.parse(inv.data);
    dynamicData = {};
    items = d.items || [];
    for (const k in d) if (k !== "items") dynamicData[k] = d[k];
    showForm = true;
  }

  async function remove(id) {
    if (confirm("Delete this invoice?")) {
      await deleteInvoice(id);
      await load();
    }
  }

  async function markAsSent(inv) {
    await updateInvoiceStatus(inv.id, "sent");
    await load();
  }

  async function markAsPaid(inv) {
    const paidDate = prompt("Payment date (YYYY-MM-DD):", new Date().toISOString().slice(0, 10));
    if (paidDate) {
      await updateInvoiceStatus(inv.id, "paid", paidDate);
      await load();
    }
  }

  async function markAsDraft(inv) {
    await updateInvoiceStatus(inv.id, "draft");
    await load();
  }

  function getClientName(id) {
    const c = clients.find(c => c.id === id);
    return c ? c.name : "Unknown";
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat('de-CH', { style: 'currency', currency: 'CHF' }).format(amount || 0);
  }

  function formatDate(dateStr) {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("de-CH", { day: "numeric", month: "short", year: "numeric" });
  }

  function updateShareA(value) {
    partner_a_share = parseFloat(value);
    partner_b_share = 100 - parseFloat(value);
  }

  function cancelForm() {
    editing = null;
    resetForm();
    showForm = false;
  }
</script>

<div class="invoices-page">
  <header class="page-header">
    <div class="header-content">
      <h1>Invoices</h1>
      <p class="subtitle">Manage your billing and payments</p>
    </div>
    <button class="btn-create" onclick={() => { showForm = !showForm; if (!showForm) cancelForm(); }}>
      {#if showForm}
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
        <span>Cancel</span>
      {:else}
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        <span>New Invoice</span>
      {/if}
    </button>
  </header>

  <div class="stats-bar">
    <div class="stat-item">
      <span class="stat-label">Total</span>
      <span class="stat-value">{stats.total}</span>
    </div>
    <div class="stat-divider"></div>
    <div class="stat-item">
      <span class="stat-label">Draft</span>
      <span class="stat-value muted">{stats.draft}</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">Sent</span>
      <span class="stat-value warning">{stats.sent}</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">Paid</span>
      <span class="stat-value success">{stats.paid}</span>
    </div>
    <div class="stat-divider"></div>
    <div class="stat-item featured">
      <span class="stat-label">Revenue</span>
      <span class="stat-value">{formatCurrency(stats.paidAmount)}</span>
    </div>
  </div>

  {#if showForm}
    <div class="form-container">
      <div class="form-badge">{editing !== null ? "Edit" : "New"}</div>
      <form onsubmit={(e) => { e.preventDefault(); submit(); }}>
        <div class="form-section">
          <h3>Invoice Details</h3>
          <div class="form-row">
            <div class="form-field flex-2">
              <label>Title</label>
              <input placeholder="e.g., Website Maintenance Q4 2024" bind:value={invoiceTitle} required />
            </div>
          </div>
          <div class="form-row">
            <div class="form-field flex-2">
              <label>Description</label>
              <input placeholder="Brief description (optional)" bind:value={invoiceDescription} />
            </div>
          </div>
          <div class="form-row">
            <div class="form-field">
              <label>Client</label>
              <select bind:value={client_id} required>
                <option value="" disabled>Select client</option>
                {#each clients as c}
                  <option value={c.id}>{c.name}</option>
                {/each}
              </select>
            </div>
            <div class="form-field">
              <label>Template</label>
              <select bind:value={template_id} required>
                <option value="" disabled>Select template</option>
                {#each templates as t}
                  <option value={t.id}>{t.name}</option>
                {/each}
              </select>
            </div>
          </div>

          {#if showLogoUploadUI}
            <div class="form-row">
              <div class="form-field">
                <label>Logo</label>
                <input type="file" accept="image/*" bind:files={logoUploadFile} />
              </div>
            </div>
          {/if}

          {#if dynamicFields.length > 0}
            <div class="form-row">
              {#each dynamicFields as field}
                <div class="form-field">
                  <label>{field}</label>
                  <input
                    placeholder="Enter {field}"
                    bind:value={dynamicData[field]}
                    type={field.toLowerCase().includes("date") ? "date" : "text"}
                    required
                  />
                </div>
              {/each}
            </div>
          {/if}
        </div>

        <div class="form-section">
          <div class="section-header">
            <h3>Line Items</h3>
            <button type="button" class="btn-add-item" onclick={addItem}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Add Item
            </button>
          </div>

          <div class="items-table">
            <div class="items-header">
              <span class="col-desc">Description</span>
              <span class="col-price">Price</span>
              <span class="col-qty">Qty</span>
              <span class="col-total">Total</span>
              <span class="col-action"></span>
            </div>
            {#each items as item, i}
              <div class="item-row" style="animation-delay: {i * 50}ms">
                <div class="col-desc">
                  <input placeholder="Service description" bind:value={item.desc} required />
                </div>
                <div class="col-price">
                  <input type="number" placeholder="0.00" bind:value={item.price} step="0.01" min="0" required />
                </div>
                <div class="col-qty">
                  <input type="number" placeholder="1" bind:value={item.qty} step="0.1" min="0" required />
                </div>
                <div class="col-total">
                  <span>{formatCurrency(item.price * item.qty)}</span>
                </div>
                <div class="col-action">
                  {#if items.length > 1}
                    <button type="button" class="btn-remove" onclick={() => removeItem(i)}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  {/if}
                </div>
              </div>
            {/each}
            <div class="items-footer">
              <span class="items-total-label">Subtotal</span>
              <span class="items-total-value">{formatCurrency(itemsTotal)}</span>
            </div>
          </div>
        </div>

        <div class="form-section compact">
          <label class="toggle-control">
            <input type="checkbox" bind:checked={isRecurring} />
            <div class="toggle-switch"></div>
            <div class="toggle-text">
              <span class="toggle-title">Set as recurring</span>
              <span class="toggle-desc">Create a recurring fee for this client</span>
            </div>
          </label>
          {#if isRecurring}
            <div class="recurring-select">
              <select bind:value={recurringFrequency}>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
              </select>
            </div>
          {/if}
        </div>

        {#if partners.length >= 2}
          <div class="form-section compact">
            <h3>Revenue Split</h3>
            <div class="split-control">
              <div class="split-partner">
                <span class="partner-name">{partners[0].name}</span>
                <span class="partner-share">{partner_a_share}%</span>
              </div>
              <div class="split-slider">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={partner_a_share}
                  oninput={(e) => updateShareA(e.target.value)}
                />
                <div class="slider-track">
                  <div class="slider-fill" style="width: {partner_a_share}%"></div>
                </div>
              </div>
              <div class="split-partner">
                <span class="partner-name">{partners[1].name}</span>
                <span class="partner-share">{partner_b_share}%</span>
              </div>
            </div>
          </div>
        {/if}

        <div class="form-actions">
          <button type="button" class="btn-cancel" onclick={cancelForm}>Cancel</button>
          <button type="submit" class="btn-submit">
            {editing !== null ? "Update Invoice" : "Create Invoice"}
          </button>
        </div>
      </form>
    </div>
  {/if}

  {#if invoiceUrl}
    <a href={invoiceUrl} target="_blank" class="download-banner">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
      Download PDF
    </a>
  {/if}

  <div class="invoices-list-container">
    <div class="list-header">
      <h2>All Invoices</h2>
      <div class="filter-pills">
        <button class:active={statusFilter === ""} onclick={() => statusFilter = ""}>
          All
          <span class="pill-count">{invoices.length}</span>
        </button>
        <button class:active={statusFilter === "draft"} onclick={() => statusFilter = "draft"}>
          Draft
          <span class="pill-count">{stats.draft}</span>
        </button>
        <button class:active={statusFilter === "sent"} onclick={() => statusFilter = "sent"}>
          Sent
          <span class="pill-count">{stats.sent}</span>
        </button>
        <button class:active={statusFilter === "paid"} onclick={() => statusFilter = "paid"}>
          Paid
          <span class="pill-count">{stats.paid}</span>
        </button>
      </div>
    </div>

    {#if filteredInvoices.length > 0}
      <div class="invoice-cards">
        {#each filteredInvoices as inv, i}
          <div class="invoice-card" style="animation-delay: {i * 40}ms">
            <div class="card-main">
              <div class="card-left">
                <span class="invoice-number">#{inv.invoice_number || inv.id}</span>
                <h4 class="invoice-title">{inv.title || `Invoice #${inv.invoice_number || inv.id}`}</h4>
                {#if inv.description}
                  <p class="invoice-desc">{inv.description}</p>
                {/if}
                <div class="invoice-meta">
                  <span class="meta-client">{getClientName(inv.client_id)}</span>
                  <span class="meta-dot"></span>
                  <span class="meta-date">{formatDate(inv.created_at)}</span>
                </div>
              </div>
              <div class="card-right">
                <span class="invoice-amount">{formatCurrency(inv.total_amount)}</span>
                <span class="status-badge {inv.status || 'draft'}">{inv.status || 'draft'}</span>
              </div>
            </div>
            <div class="card-actions">
              {#if inv.status === "draft" || !inv.status}
                <button class="action-btn send" onclick={() => markAsSent(inv)}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="22" y1="2" x2="11" y2="13"/>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                  </svg>
                  Send
                </button>
              {:else if inv.status === "sent"}
                <button class="action-btn paid" onclick={() => markAsPaid(inv)}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  Mark Paid
                </button>
              {:else if inv.status === "paid"}
                <button class="action-btn unsend" onclick={() => markAsSent(inv)}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="1 4 1 10 7 10"/>
                    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
                  </svg>
                  Revert
                </button>
              {/if}
              <button class="action-btn" onclick={() => edit(inv)} title="Edit">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
              <a href={`http://localhost:8000/invoices/${inv.id}/pdf?t=${Date.now()}`} target="_blank" class="action-btn" title="Download PDF">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </a>
              <button class="action-btn danger" onclick={() => remove(inv.id)} title="Delete">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <div class="empty-state">
        <div class="empty-icon">
          <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
        </div>
        <p>No invoices found</p>
        <button class="btn-submit" onclick={() => showForm = true}>Create your first invoice</button>
      </div>
    {/if}
  </div>
</div>

<style>
  .invoices-page {
    max-width: 1200px;
    margin: 0 auto;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.5rem;
  }

  .page-header h1 {
    font-size: 1.75rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.03em;
  }

  .subtitle {
    margin: 0.25rem 0 0;
    color: var(--color-text-secondary);
    font-size: 0.9375rem;
  }

  .btn-create {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    background: var(--color-primary);
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 0.9375rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-create:hover {
    background: var(--color-primary-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  }

  .stats-bar {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 1rem 1.5rem;
    background: var(--color-surface);
    border-radius: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    margin-bottom: 1.5rem;
  }

  .stat-item {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .stat-item.featured {
    margin-left: auto;
  }

  .stat-label {
    font-size: 0.75rem;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 500;
  }

  .stat-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--color-text);
  }

  .stat-value.muted { color: var(--color-text-secondary); }
  .stat-value.warning { color: #d97706; }
  .stat-value.success { color: #059669; }

  .stat-divider {
    width: 1px;
    height: 32px;
    background: var(--color-border-light);
  }

  .form-container {
    background: var(--color-surface);
    border-radius: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
    margin-bottom: 1.5rem;
    overflow: hidden;
    animation: slideDown 0.3s ease;
    position: relative;
  }

  @keyframes slideDown {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .form-badge {
    position: absolute;
    top: 1.25rem;
    right: 1.5rem;
    background: var(--color-primary);
    color: white;
    font-size: 0.6875rem;
    font-weight: 600;
    padding: 0.25rem 0.625rem;
    border-radius: 6px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .form-container form {
    padding: 1.5rem;
  }

  .form-section {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .form-section:last-of-type {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
  }

  .form-section.compact {
    padding: 1.25rem;
    background: var(--color-bg);
    border-radius: 12px;
    border-bottom: none;
    margin-bottom: 1rem;
  }

  .form-section h3 {
    font-size: 0.9375rem;
    font-weight: 600;
    margin: 0 0 1rem;
    color: var(--color-text);
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .section-header h3 {
    margin: 0;
  }

  .form-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .form-row:last-child {
    margin-bottom: 0;
  }

  .form-field {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .form-field.flex-2 {
    flex: 2;
  }

  .form-field label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .form-field input,
  .form-field select {
    padding: 0.625rem 0.875rem;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    font-size: 0.9375rem;
    background: white;
    transition: all 0.2s ease;
  }

  .form-field input:focus,
  .form-field select:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .btn-add-item {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.5rem 0.875rem;
    background: transparent;
    color: var(--color-primary);
    border: 1px dashed var(--color-primary);
    border-radius: 8px;
    font-size: 0.8125rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-add-item:hover {
    background: var(--color-primary-light);
  }

  .items-table {
    background: var(--color-bg);
    border-radius: 10px;
    overflow: hidden;
  }

  .items-header {
    display: grid;
    grid-template-columns: 3fr 120px 80px 120px 40px;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border-light);
    font-size: 0.6875rem;
    font-weight: 600;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .item-row {
    display: grid;
    grid-template-columns: 3fr 120px 80px 120px 40px;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    align-items: center;
    border-bottom: 1px solid var(--color-border-light);
    animation: fadeIn 0.3s ease backwards;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .item-row:last-child {
    border-bottom: none;
  }

  .item-row input {
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--color-border-light);
    border-radius: 6px;
    font-size: 0.875rem;
    background: white;
  }

  .item-row input:focus {
    outline: none;
    border-color: var(--color-primary);
  }

  .col-total span {
    font-weight: 600;
    color: var(--color-text-secondary);
  }

  .btn-remove {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    border-radius: 6px;
    color: var(--color-text-muted);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-remove:hover {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }

  .items-footer {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 2rem;
    padding: 1rem;
    background: var(--color-surface);
    border-top: 1px solid var(--color-border-light);
  }

  .items-total-label {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    font-weight: 500;
  }

  .items-total-value {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--color-text);
  }

  .toggle-control {
    display: flex;
    align-items: flex-start;
    gap: 0.875rem;
    cursor: pointer;
  }

  .toggle-control input {
    display: none;
  }

  .toggle-switch {
    width: 44px;
    height: 24px;
    background: var(--color-border);
    border-radius: 12px;
    position: relative;
    transition: all 0.2s ease;
    flex-shrink: 0;
  }

  .toggle-switch::after {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    width: 20px;
    height: 20px;
    background: white;
    border-radius: 50%;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  }

  .toggle-control input:checked + .toggle-switch {
    background: var(--color-primary);
  }

  .toggle-control input:checked + .toggle-switch::after {
    left: 22px;
  }

  .toggle-text {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .toggle-title {
    font-weight: 600;
    font-size: 0.9375rem;
  }

  .toggle-desc {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .recurring-select {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--color-border-light);
    max-width: 160px;
  }

  .recurring-select select {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--color-border);
    border-radius: 6px;
    font-size: 0.875rem;
  }

  .split-control {
    display: flex;
    align-items: center;
    gap: 1.5rem;
  }

  .split-partner {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 80px;
  }

  .partner-name {
    font-size: 0.75rem;
    color: var(--color-text-secondary);
  }

  .partner-share {
    font-size: 1.25rem;
    font-weight: 700;
  }

  .split-slider {
    flex: 1;
    position: relative;
  }

  .split-slider input {
    width: 100%;
    height: 6px;
    opacity: 0;
    position: relative;
    z-index: 2;
    cursor: pointer;
  }

  .slider-track {
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    height: 6px;
    background: var(--color-border);
    border-radius: 3px;
    transform: translateY(-50%);
  }

  .slider-fill {
    height: 100%;
    background: var(--color-primary);
    border-radius: 3px;
    transition: width 0.1s ease;
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--color-border-light);
    margin-top: 0.5rem;
  }

  .btn-cancel {
    padding: 0.625rem 1.25rem;
    background: white;
    color: var(--color-text-secondary);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    font-size: 0.9375rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-cancel:hover {
    background: var(--color-bg);
  }

  .btn-submit {
    padding: 0.625rem 1.5rem;
    background: var(--color-primary);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 0.9375rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-submit:hover {
    background: var(--color-primary-hover);
    transform: translateY(-1px);
  }

  .download-banner {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.625rem;
    padding: 1rem;
    margin-bottom: 1.5rem;
    background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    color: white;
    border-radius: 12px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s ease;
    animation: pulse 2s ease infinite;
  }

  @keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
    50% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
  }

  .download-banner:hover {
    transform: translateY(-2px);
    text-decoration: none;
    color: white;
  }

  .invoices-list-container {
    background: var(--color-surface);
    border-radius: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
    overflow: hidden;
  }

  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .list-header h2 {
    font-size: 1.125rem;
    font-weight: 600;
    margin: 0;
  }

  .filter-pills {
    display: flex;
    gap: 0.375rem;
  }

  .filter-pills button {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.5rem 0.875rem;
    background: var(--color-bg);
    color: var(--color-text-secondary);
    border: none;
    border-radius: 8px;
    font-size: 0.8125rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .filter-pills button:hover {
    background: var(--color-border-light);
  }

  .filter-pills button.active {
    background: var(--color-primary);
    color: white;
  }

  .pill-count {
    background: rgba(255,255,255,0.2);
    padding: 0.125rem 0.375rem;
    border-radius: 4px;
    font-size: 0.6875rem;
  }

  .filter-pills button:not(.active) .pill-count {
    background: var(--color-surface);
  }

  .invoice-cards {
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .invoice-card {
    background: var(--color-bg);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    transition: all 0.2s ease;
    animation: fadeIn 0.4s ease backwards;
  }

  .invoice-card:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transform: translateY(-1px);
  }

  .card-main {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.75rem;
  }

  .card-left {
    flex: 1;
    min-width: 0;
  }

  .invoice-number {
    font-family: ui-monospace, monospace;
    font-size: 0.6875rem;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .invoice-title {
    font-size: 1rem;
    font-weight: 600;
    margin: 0.25rem 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .invoice-desc {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
    margin: 0 0 0.5rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 400px;
  }

  .invoice-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .meta-dot {
    width: 3px;
    height: 3px;
    background: var(--color-text-muted);
    border-radius: 50%;
  }

  .card-right {
    text-align: right;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.5rem;
  }

  .invoice-amount {
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: -0.02em;
  }

  .status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .status-badge.draft {
    background: var(--color-bg);
    color: var(--color-text-secondary);
    border: 1px solid var(--color-border);
  }

  .status-badge.sent {
    background: rgba(245, 158, 11, 0.1);
    color: #d97706;
  }

  .status-badge.paid {
    background: rgba(16, 185, 129, 0.1);
    color: #059669;
  }

  .card-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--color-border-light);
  }

  .action-btn {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.375rem 0.625rem;
    background: transparent;
    border: none;
    border-radius: 6px;
    color: var(--color-text-secondary);
    font-size: 0.8125rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
    text-decoration: none;
  }

  .action-btn:hover {
    background: var(--color-surface);
    color: var(--color-text);
  }

  .action-btn.send {
    background: rgba(245, 158, 11, 0.1);
    color: #d97706;
  }

  .action-btn.send:hover {
    background: rgba(245, 158, 11, 0.2);
  }

  .action-btn.paid {
    background: rgba(16, 185, 129, 0.1);
    color: #059669;
  }

  .action-btn.paid:hover {
    background: rgba(16, 185, 129, 0.2);
  }

  .action-btn.unsend {
    background: var(--color-bg);
    color: var(--color-text-secondary);
  }

  .action-btn.danger:hover {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
  }

  .empty-icon {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background: var(--color-bg);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1.5rem;
  }

  .empty-icon svg {
    color: var(--color-text-muted);
    opacity: 0.4;
  }

  .empty-state p {
    color: var(--color-text-secondary);
    margin: 0 0 1.5rem;
    font-size: 1rem;
  }

  @media (max-width: 900px) {
    .stats-bar {
      flex-wrap: wrap;
      gap: 1rem;
    }

    .stat-divider {
      display: none;
    }

    .stat-item.featured {
      margin-left: 0;
      width: 100%;
      padding-top: 0.75rem;
      border-top: 1px solid var(--color-border-light);
    }

    .form-row {
      flex-direction: column;
    }

    .items-header {
      display: none;
    }

    .item-row {
      grid-template-columns: 1fr;
      gap: 0.5rem;
      padding: 1rem;
    }

    .col-total {
      text-align: left;
      padding-top: 0.5rem;
      border-top: 1px solid var(--color-border-light);
    }

    .col-action {
      position: absolute;
      top: 0.5rem;
      right: 0.5rem;
    }

    .item-row {
      position: relative;
    }

    .list-header {
      flex-direction: column;
      gap: 1rem;
      align-items: flex-start;
    }

    .filter-pills {
      width: 100%;
      overflow-x: auto;
    }

    .card-main {
      flex-direction: column;
      gap: 0.75rem;
    }

    .card-right {
      flex-direction: row;
      align-items: center;
      gap: 1rem;
      width: 100%;
      justify-content: space-between;
    }

    .split-control {
      flex-direction: column;
      gap: 1rem;
    }

    .split-slider {
      width: 100%;
    }
  }

  @media (max-width: 640px) {
    .page-header {
      flex-direction: column;
      gap: 1rem;
    }

    .btn-create {
      width: 100%;
      justify-content: center;
    }

    .form-actions {
      flex-direction: column;
    }

    .form-actions button {
      width: 100%;
    }

    .card-actions {
      flex-wrap: wrap;
    }
  }
</style>
