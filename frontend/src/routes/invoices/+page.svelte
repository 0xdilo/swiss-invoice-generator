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

<div class="page-header">
  <div>
    <h1>Invoices</h1>
    <p class="subtitle">Create and manage your invoices</p>
  </div>
  <button class="btn-primary" onclick={() => { showForm = !showForm; if (!showForm) cancelForm(); }}>
    {#if showForm}
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
      Cancel
    {:else}
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="12" y1="5" x2="12" y2="19"/>
        <line x1="5" y1="12" x2="19" y2="12"/>
      </svg>
      New Invoice
    {/if}
  </button>
</div>

{#if showForm}
  <div class="card form-card">
    <div class="card-header">
      <h3>{editing !== null ? "Edit Invoice" : "Create Invoice"}</h3>
    </div>
    <form onsubmit={(e) => { e.preventDefault(); submit(); }}>
      <div class="form-group">
        <label for="invoice-title">Title</label>
        <input
          id="invoice-title"
          placeholder="e.g., Website Maintenance Q4 2024"
          bind:value={invoiceTitle}
          required
        />
      </div>

      <div class="form-group">
        <label for="invoice-description">Description (optional)</label>
        <input
          id="invoice-description"
          placeholder="Brief description of the invoice"
          bind:value={invoiceDescription}
        />
      </div>

      <div class="form-grid">
        <div class="form-group">
          <label for="client-select">Client</label>
          <select id="client-select" bind:value={client_id} required>
            <option value="" disabled selected>Select client</option>
            {#each clients as c}
              <option value={c.id}>{c.name}</option>
            {/each}
          </select>
        </div>

        <div class="form-group">
          <label for="template-select">Template</label>
          <select id="template-select" bind:value={template_id} required>
            <option value="" disabled selected>Select template</option>
            {#each templates as t}
              <option value={t.id}>{t.name}</option>
            {/each}
          </select>
        </div>
      </div>

      {#if showLogoUploadUI}
        <div class="form-group">
          <label for="logoInput">Logo (optional)</label>
          <input
            id="logoInput"
            type="file"
            accept="image/*"
            bind:files={logoUploadFile}
          />
        </div>
      {/if}

      {#if dynamicFields.length > 0}
        <div class="form-grid">
          {#each dynamicFields as field}
            <div class="form-group">
              <label for={`field-${field}`}>{field}</label>
              <input
                id={`field-${field}`}
                placeholder={`Enter ${field}`}
                bind:value={dynamicData[field]}
                type={field.toLowerCase().includes("date") ? "date" : "text"}
                required
              />
            </div>
          {/each}
        </div>
      {/if}

      <div class="items-section">
        <div class="section-header">
          <h4>Line Items</h4>
          <button type="button" class="btn-ghost" onclick={addItem}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Add Item
          </button>
        </div>

        <div class="items-list">
          {#each items as item, i}
            <div class="item-row">
              <div class="item-desc">
                <input
                  placeholder="Description"
                  bind:value={item.desc}
                  required
                />
              </div>
              <div class="item-price">
                <input
                  type="number"
                  placeholder="Price"
                  bind:value={item.price}
                  step="0.01"
                  min="0"
                  required
                />
              </div>
              <div class="item-qty">
                <input
                  type="number"
                  placeholder="Qty"
                  bind:value={item.qty}
                  step="0.1"
                  min="0"
                  required
                />
              </div>
              <div class="item-total">
                {formatCurrency(item.price * item.qty)}
              </div>
              {#if items.length > 1}
                <button type="button" class="btn-icon-danger" onclick={() => removeItem(i)}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              {:else}
                <div style="width: 36px;"></div>
              {/if}
            </div>
          {/each}
        </div>
      </div>

      {#if editing === null}
        <div class="recurring-section">
          <label class="toggle-row">
            <input type="checkbox" bind:checked={isRecurring} />
            <div class="toggle-content">
              <span class="toggle-label">Set as recurring</span>
              <span class="toggle-desc">Create a recurring fee for this invoice</span>
            </div>
          </label>
          {#if isRecurring}
            <div class="recurring-options">
              <div class="form-group">
                <label for="recurring-freq">Frequency</label>
                <select id="recurring-freq" bind:value={recurringFrequency}>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
            </div>
          {/if}
        </div>
      {/if}

      {#if partners.length >= 2}
        <div class="split-section">
          <h4>Revenue Split</h4>
          <div class="split-row">
            <div class="split-partner">
              <span class="split-name">{partners[0].name}</span>
              <span class="split-percent">{partner_a_share}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={partner_a_share}
              oninput={(e) => updateShareA(e.target.value)}
            />
            <div class="split-partner">
              <span class="split-name">{partners[1].name}</span>
              <span class="split-percent">{partner_b_share}%</span>
            </div>
          </div>
        </div>
      {/if}

      <div class="form-actions">
        <button type="button" class="btn-secondary" onclick={cancelForm}>Cancel</button>
        <button type="submit" class="btn-primary">
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

<div class="card">
  <div class="card-header">
    <h3>All Invoices</h3>
    <div class="filter-tabs">
      <button class:active={statusFilter === ""} onclick={() => statusFilter = ""}>All</button>
      <button class:active={statusFilter === "draft"} onclick={() => statusFilter = "draft"}>Draft</button>
      <button class:active={statusFilter === "sent"} onclick={() => statusFilter = "sent"}>Sent</button>
      <button class:active={statusFilter === "paid"} onclick={() => statusFilter = "paid"}>Paid</button>
    </div>
  </div>

  {#if filteredInvoices.length > 0}
    <table>
      <thead>
        <tr>
          <th>Invoice</th>
          <th>Client</th>
          <th>Status</th>
          <th style="text-align: right">Amount</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {#each filteredInvoices as inv}
          <tr>
            <td>
              <div class="invoice-cell">
                <span class="invoice-title">{inv.title || `Invoice #${inv.invoice_number || inv.id}`}</span>
                {#if inv.description}
                  <span class="invoice-desc">{inv.description}</span>
                {/if}
                <span class="invoice-id">#{inv.invoice_number || inv.id}</span>
              </div>
            </td>
            <td>
              <span class="client-name">{getClientName(inv.client_id)}</span>
            </td>
            <td>
              <span class="status-badge {inv.status || 'draft'}">{inv.status || 'draft'}</span>
            </td>
            <td style="text-align: right">
              <span class="amount">{formatCurrency(inv.total_amount)}</span>
            </td>
            <td>
              <div class="row-actions">
                {#if inv.status === "draft" || !inv.status}
                  <button class="btn-xs sent" onclick={() => markAsSent(inv)}>Send</button>
                {:else if inv.status === "sent"}
                  <button class="btn-xs paid" onclick={() => markAsPaid(inv)}>Paid</button>
                {:else if inv.status === "paid"}
                  <button class="btn-xs draft" onclick={() => markAsSent(inv)}>Unsend</button>
                {/if}
                <button class="btn-icon" onclick={() => edit(inv)} title="Edit">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </button>
                <a href={`http://localhost:8000/invoices/${inv.id}/pdf?t=${Date.now()}`} target="_blank" class="btn-icon" title="PDF">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                </a>
                <button class="btn-icon danger" onclick={() => remove(inv.id)} title="Delete">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  {:else}
    <div class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
      <p>No invoices found</p>
      <button class="btn-primary" onclick={() => showForm = true}>Create your first invoice</button>
    </div>
  {/if}
</div>

<style>
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.5rem;
    gap: 1rem;
    flex-wrap: wrap;
  }

  h1 { margin-bottom: 0.25rem; }

  .subtitle {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 0.9375rem;
  }

  .btn-primary {
    background: var(--color-primary);
    color: white;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }

  .btn-primary:hover {
    background: var(--color-primary-hover);
  }

  .btn-secondary {
    background: var(--color-surface);
    color: var(--color-text);
    border: 1px solid var(--color-border);
  }

  .btn-secondary:hover {
    background: var(--color-bg);
  }

  .btn-ghost {
    background: transparent;
    color: var(--color-primary);
    padding: 0.5rem 0.75rem;
  }

  .btn-ghost:hover {
    background: var(--color-primary-light);
  }

  .btn-icon {
    background: transparent;
    color: var(--color-text-secondary);
    padding: 0.5rem;
    border-radius: var(--radius-sm);
  }

  .btn-icon:hover {
    background: var(--color-bg);
    color: var(--color-text);
  }

  .btn-icon.danger:hover {
    background: var(--color-danger-light);
    color: var(--color-danger);
  }

  .btn-icon-danger {
    background: transparent;
    color: var(--color-danger);
    padding: 0.5rem;
    border-radius: var(--radius-sm);
  }

  .btn-icon-danger:hover {
    background: var(--color-danger-light);
  }

  .btn-xs {
    padding: 0.25rem 0.625rem;
    font-size: 0.75rem;
    border-radius: var(--radius-sm);
  }

  .btn-xs.sent {
    background: var(--color-warning-light);
    color: #92400e;
  }

  .btn-xs.sent:hover {
    background: #fde68a;
  }

  .btn-xs.paid {
    background: var(--color-success-light);
    color: #065f46;
  }

  .btn-xs.paid:hover {
    background: #a7f3d0;
  }

  .btn-xs.draft {
    background: var(--color-border-light);
    color: var(--color-text-secondary);
  }

  .btn-xs.draft:hover {
    background: var(--color-border);
  }

  .card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    overflow: hidden;
    margin-bottom: 1.5rem;
  }

  .form-card {
    padding: 0;
  }

  .form-card form {
    padding: 1.5rem;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .card-header h3 {
    margin: 0;
    font-size: 1rem;
  }

  .form-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .form-group {
    margin-bottom: 1rem;
  }

  .form-group label {
    display: block;
    margin-bottom: 0.375rem;
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  .items-section {
    margin: 1.5rem 0;
    padding: 1rem;
    background: var(--color-bg);
    border-radius: var(--radius-md);
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .section-header h4 {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .items-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .item-row {
    display: grid;
    grid-template-columns: 3fr 1fr 80px 100px 36px;
    gap: 0.75rem;
    align-items: center;
  }

  .item-total {
    font-weight: 600;
    font-size: 0.875rem;
    text-align: right;
    color: var(--color-text-secondary);
  }

  .recurring-section {
    margin: 1.5rem 0;
    padding: 1rem;
    background: var(--color-bg);
    border-radius: var(--radius-md);
  }

  .toggle-row {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    cursor: pointer;
  }

  .toggle-row input[type="checkbox"] {
    width: 18px;
    height: 18px;
    margin-top: 0.125rem;
    accent-color: var(--color-primary);
  }

  .toggle-content {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .toggle-label {
    font-weight: 500;
    font-size: 0.9375rem;
  }

  .toggle-desc {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .recurring-options {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--color-border-light);
    max-width: 200px;
  }

  .recurring-options .form-group {
    margin-bottom: 0;
  }

  .split-section {
    margin: 1.5rem 0;
    padding: 1rem;
    background: var(--color-bg);
    border-radius: var(--radius-md);
  }

  .split-section h4 {
    margin: 0 0 1rem 0;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .split-row {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .split-row input[type="range"] {
    flex: 1;
    padding: 0;
    height: 6px;
  }

  .split-partner {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 80px;
  }

  .split-name {
    font-size: 0.75rem;
    color: var(--color-text-secondary);
  }

  .split-percent {
    font-size: 1.125rem;
    font-weight: 600;
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--color-border-light);
  }

  .download-banner {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.875rem;
    margin-bottom: 1.5rem;
    background: var(--color-success-light);
    color: #065f46;
    border-radius: var(--radius-md);
    font-weight: 500;
    text-decoration: none;
    transition: background 0.15s ease;
  }

  .download-banner:hover {
    background: #a7f3d0;
    text-decoration: none;
    color: #065f46;
  }

  .filter-tabs {
    display: flex;
    gap: 0.25rem;
  }

  .filter-tabs button {
    background: transparent;
    color: var(--color-text-muted);
    padding: 0.375rem 0.75rem;
    font-size: 0.8125rem;
    border-radius: var(--radius-sm);
  }

  .filter-tabs button:hover {
    background: var(--color-bg);
    color: var(--color-text);
  }

  .filter-tabs button.active {
    background: var(--color-primary);
    color: white;
  }

  .invoice-cell {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .invoice-title {
    font-weight: 500;
    color: var(--color-text);
  }

  .invoice-desc {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
    max-width: 280px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .invoice-id {
    font-family: ui-monospace, monospace;
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }

  .client-name {
    font-weight: 500;
  }

  .status-badge {
    display: inline-block;
    padding: 0.25rem 0.625rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: capitalize;
  }

  .status-badge.draft {
    background: var(--color-border-light);
    color: var(--color-text-secondary);
  }

  .status-badge.sent {
    background: var(--color-warning-light);
    color: #92400e;
  }

  .status-badge.paid {
    background: var(--color-success-light);
    color: #065f46;
  }

  .split-info {
    font-size: 0.8125rem;
    color: var(--color-text-muted);
    font-family: ui-monospace, monospace;
  }

  .amount {
    font-weight: 600;
  }

  .row-actions {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    justify-content: flex-end;
  }

  .row-actions a {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    color: var(--color-text-muted);
  }

  .empty-state svg {
    margin-bottom: 1rem;
    opacity: 0.4;
  }

  .empty-state p {
    margin-bottom: 1rem;
  }

  @media (max-width: 900px) {
    .form-grid {
      grid-template-columns: 1fr;
    }

    .item-row {
      grid-template-columns: 1fr;
      gap: 0.5rem;
      padding: 0.75rem;
      background: var(--color-surface);
      border-radius: var(--radius-md);
      position: relative;
    }

    .item-total {
      text-align: left;
    }

    .item-row button {
      position: absolute;
      top: 0.5rem;
      right: 0.5rem;
    }

    .split-row {
      flex-direction: column;
      gap: 0.75rem;
    }

    .split-row input[type="range"] {
      width: 100%;
    }

    table {
      display: block;
      overflow-x: auto;
    }
  }

  @media (max-width: 640px) {
    .page-header {
      flex-direction: column;
      align-items: stretch;
    }

    .page-header button {
      width: 100%;
      justify-content: center;
    }

    .form-actions {
      flex-direction: column;
    }

    .form-actions button {
      width: 100%;
    }
  }
</style>
