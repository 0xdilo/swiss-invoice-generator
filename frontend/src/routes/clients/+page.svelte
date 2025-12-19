<script>
  import { onMount } from "svelte";
  import {
    getClients,
    addClient,
    updateClient,
    deleteClient,
    getRecurringFees,
    addRecurringFee,
    updateRecurringFee,
    deleteRecurringFee,
    getInvoices,
    getClientStats,
  } from "$lib/api.js";

  let clients = [];
  let selectedClient = null;
  let clientStats = null;
  let clientInvoices = [];
  let recurringFees = [];

  let form = {
    name: "",
    address: "",
    cap: "",
    city: "",
    nation: "",
    email: "",
  };
  let editing = null;
  let showForm = false;

  let feeForm = {
    amount: "",
    currency: "CHF",
    frequency: "yearly",
    start_date: "",
    description: "",
  };
  let editingFee = null;
  let showFeeForm = false;

  async function load() {
    clients = await getClients();
  }
  onMount(load);

  async function selectClient(client) {
    if (selectedClient?.id === client.id) {
      selectedClient = null;
      clientStats = null;
      clientInvoices = [];
      recurringFees = [];
      return;
    }
    selectedClient = client;
    await loadClientData(client.id);
  }

  async function loadClientData(clientId) {
    [clientStats, clientInvoices, recurringFees] = await Promise.all([
      getClientStats(clientId),
      getInvoices(clientId),
      getRecurringFees(clientId),
    ]);
  }

  async function submit() {
    if (editing !== null) {
      await updateClient(editing, form);
      editing = null;
    } else {
      await addClient(form);
    }
    form = { name: "", address: "", cap: "", city: "", nation: "", email: "" };
    showForm = false;
    await load();
  }

  function edit(client, e) {
    e.stopPropagation();
    editing = client.id;
    form = { ...client };
    showForm = true;
  }

  async function remove(id, e) {
    e.stopPropagation();
    if (confirm("Delete this client?")) {
      await deleteClient(id);
      if (selectedClient?.id === id) {
        selectedClient = null;
        clientStats = null;
        clientInvoices = [];
        recurringFees = [];
      }
      await load();
    }
  }

  function cancelForm() {
    editing = null;
    form = { name: "", address: "", cap: "", city: "", nation: "", email: "" };
    showForm = false;
  }

  async function submitFee() {
    if (editingFee !== null) {
      await updateRecurringFee(editingFee, feeForm);
      editingFee = null;
    } else {
      await addRecurringFee(selectedClient.id, feeForm);
    }
    feeForm = {
      amount: "",
      currency: "CHF",
      frequency: "yearly",
      start_date: "",
      description: "",
    };
    showFeeForm = false;
    await loadClientData(selectedClient.id);
  }

  function editFee(fee) {
    editingFee = fee.id;
    feeForm = { ...fee };
    showFeeForm = true;
  }

  async function removeFee(feeId) {
    if (confirm("Delete this recurring fee?")) {
      await deleteRecurringFee(feeId);
      await loadClientData(selectedClient.id);
    }
  }

  function cancelFeeForm() {
    editingFee = null;
    feeForm = {
      amount: "",
      currency: "CHF",
      frequency: "yearly",
      start_date: "",
      description: "",
    };
    showFeeForm = false;
  }

  function formatCurrency(amount, currency = "CHF") {
    return new Intl.NumberFormat("de-CH", {
      style: "currency",
      currency: currency,
    }).format(amount || 0);
  }

  function formatDate(dateStr) {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("de-CH");
  }

  function getStatusColor(status) {
    switch (status) {
      case "paid": return "status-paid";
      case "sent": return "status-sent";
      default: return "status-draft";
    }
  }
</script>

<div class="clients-layout" class:has-selection={selectedClient}>
  <div class="clients-panel">
    <div class="panel-header">
      <div>
        <h1>Clients</h1>
        <p class="subtitle">{clients.length} client{clients.length !== 1 ? "s" : ""}</p>
      </div>
      <button class="btn-primary" onclick={() => { showForm = !showForm; if (!showForm) cancelForm(); }}>
        {#if showForm}
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        {:else}
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        {/if}
      </button>
    </div>

    {#if showForm}
      <div class="client-form-card">
        <h3>{editing !== null ? "Edit Client" : "New Client"}</h3>
        <form onsubmit={(e) => { e.preventDefault(); submit(); }}>
          <div class="form-row">
            <div class="form-group">
              <label for="client-name">Name</label>
              <input id="client-name" placeholder="Client name" bind:value={form.name} required />
            </div>
            <div class="form-group">
              <label for="client-email">Email</label>
              <input id="client-email" type="email" placeholder="email@example.com" bind:value={form.email} required />
            </div>
          </div>
          <div class="form-group">
            <label for="client-address">Address</label>
            <input id="client-address" placeholder="Street address" bind:value={form.address} required />
          </div>
          <div class="form-row-3">
            <div class="form-group">
              <label for="client-cap">Postal</label>
              <input id="client-cap" placeholder="12345" bind:value={form.cap} required />
            </div>
            <div class="form-group">
              <label for="client-city">City</label>
              <input id="client-city" placeholder="City" bind:value={form.city} required />
            </div>
            <div class="form-group">
              <label for="client-nation">Country</label>
              <input id="client-nation" placeholder="CH" bind:value={form.nation} required />
            </div>
          </div>
          <div class="form-actions">
            <button type="button" class="btn-secondary" onclick={cancelForm}>Cancel</button>
            <button type="submit" class="btn-primary">{editing !== null ? "Update" : "Add"}</button>
          </div>
        </form>
      </div>
    {/if}

    <div class="clients-list">
      {#each clients as client}
        <div
          class="client-item"
          class:selected={selectedClient?.id === client.id}
          role="button"
          tabindex="0"
          onclick={() => selectClient(client)}
          onkeydown={(e) => e.key === 'Enter' && selectClient(client)}
        >
          <div class="client-avatar">{client.name.charAt(0).toUpperCase()}</div>
          <div class="client-info">
            <span class="client-name">{client.name}</span>
            <span class="client-location">{client.city}, {client.nation}</span>
          </div>
          <div class="client-actions">
            <button class="btn-icon" onclick={(e) => edit(client, e)} title="Edit">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button class="btn-icon danger" onclick={(e) => remove(client.id, e)} title="Delete">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </div>
        </div>
      {:else}
        <div class="empty-list">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          <p>No clients yet</p>
          <button class="btn-primary btn-sm" onclick={() => showForm = true}>Add your first client</button>
        </div>
      {/each}
    </div>
  </div>

  {#if selectedClient}
    <div class="detail-panel">
      <div class="detail-header">
        <div class="detail-avatar">{selectedClient.name.charAt(0).toUpperCase()}</div>
        <div class="detail-title">
          <h2>{selectedClient.name}</h2>
          <p>{selectedClient.email}</p>
        </div>
        <button class="btn-icon close-detail" onclick={() => { selectedClient = null; clientStats = null; clientInvoices = []; recurringFees = []; }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="client-address">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
          <circle cx="12" cy="10" r="3"/>
        </svg>
        <span>{selectedClient.address}, {selectedClient.cap} {selectedClient.city}, {selectedClient.nation}</span>
      </div>

      {#if clientStats}
        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-value">{formatCurrency(clientStats.total_invoiced)}</span>
            <span class="stat-label">Total Invoiced</span>
          </div>
          <div class="stat-card success">
            <span class="stat-value">{formatCurrency(clientStats.total_paid)}</span>
            <span class="stat-label">Paid ({clientStats.paid_invoices})</span>
          </div>
          <div class="stat-card warning">
            <span class="stat-value">{formatCurrency(clientStats.total_outstanding)}</span>
            <span class="stat-label">Outstanding ({clientStats.outstanding_invoices})</span>
          </div>
          <div class="stat-card info">
            <span class="stat-value">{formatCurrency(clientStats.annual_recurring)}/yr</span>
            <span class="stat-label">Recurring ({clientStats.recurring_fees})</span>
          </div>
        </div>
      {/if}

      <div class="detail-section">
        <div class="section-header">
          <h3>Invoices</h3>
          <a href="/invoices?client={selectedClient.id}" class="btn-link">
            View All
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </a>
        </div>
        {#if clientInvoices.length > 0}
          <div class="invoices-list">
            {#each clientInvoices.slice(0, 5) as invoice}
              <div class="invoice-item">
                <div class="invoice-info">
                  <span class="invoice-number">#{invoice.id}</span>
                  <span class="invoice-date">{formatDate(invoice.created_at)}</span>
                </div>
                <div class="invoice-amount">{formatCurrency(invoice.total_amount)}</div>
                <span class="status-badge {getStatusColor(invoice.status)}">{invoice.status || "draft"}</span>
              </div>
            {/each}
          </div>
        {:else}
          <p class="empty-section">No invoices yet</p>
        {/if}
      </div>

      <div class="detail-section">
        <div class="section-header">
          <h3>Recurring Fees</h3>
          <button class="btn-link" onclick={() => { showFeeForm = !showFeeForm; if (!showFeeForm) cancelFeeForm(); }}>
            {#if showFeeForm}
              Cancel
            {:else}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Add
            {/if}
          </button>
        </div>

        {#if showFeeForm}
          <form class="fee-form" onsubmit={(e) => { e.preventDefault(); submitFee(); }}>
            <div class="form-row">
              <div class="form-group flex-2">
                <label>Description</label>
                <input placeholder="Annual maintenance" bind:value={feeForm.description} />
              </div>
              <div class="form-group">
                <label>Amount</label>
                <input type="number" step="0.01" placeholder="400.00" bind:value={feeForm.amount} required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Currency</label>
                <select bind:value={feeForm.currency}>
                  <option value="CHF">CHF</option>
                  <option value="EUR">EUR</option>
                  <option value="USD">USD</option>
                </select>
              </div>
              <div class="form-group">
                <label>Frequency</label>
                <select bind:value={feeForm.frequency}>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                  <option value="one-time">One-time</option>
                </select>
              </div>
              <div class="form-group">
                <label>Start Date</label>
                <input type="date" bind:value={feeForm.start_date} required />
              </div>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-secondary btn-sm" onclick={cancelFeeForm}>Cancel</button>
              <button type="submit" class="btn-primary btn-sm">{editingFee !== null ? "Update" : "Add"}</button>
            </div>
          </form>
        {/if}

        {#if recurringFees.length > 0}
          <div class="fees-list">
            {#each recurringFees as fee}
              <div class="fee-item">
                <div class="fee-info">
                  <span class="fee-desc">{fee.description || "Recurring fee"}</span>
                  <span class="fee-meta">
                    <span class="fee-badge">{fee.frequency}</span>
                    <span>from {formatDate(fee.start_date)}</span>
                  </span>
                </div>
                <div class="fee-amount">{formatCurrency(fee.amount, fee.currency)}</div>
                <div class="fee-actions">
                  <button class="btn-icon" onclick={() => editFee(fee)} title="Edit">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button class="btn-icon danger" onclick={() => removeFee(fee.id)} title="Delete">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6"/>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                  </button>
                </div>
              </div>
            {/each}
          </div>
        {:else if !showFeeForm}
          <p class="empty-section">No recurring fees</p>
        {/if}
      </div>
    </div>
  {:else}
    <div class="no-selection">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
      <p>Select a client to view details</p>
    </div>
  {/if}
</div>

<style>
  .clients-layout {
    display: grid;
    grid-template-columns: 380px 1fr;
    gap: 1.5rem;
    min-height: calc(100vh - 6rem);
  }

  .clients-panel {
    display: flex;
    flex-direction: column;
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    overflow: hidden;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .panel-header h1 {
    font-size: 1.25rem;
    margin: 0;
  }

  .subtitle {
    margin: 0;
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .client-form-card {
    padding: 1.25rem;
    border-bottom: 1px solid var(--color-border-light);
    background: var(--color-bg);
  }

  .client-form-card h3 {
    margin: 0 0 1rem;
    font-size: 0.9375rem;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .form-row-3 {
    display: grid;
    grid-template-columns: 80px 1fr 80px;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .form-group.flex-2 {
    flex: 2;
  }

  .form-group label {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-top: 1rem;
  }

  .clients-list {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
  }

  .client-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    padding: 0.75rem;
    border: none;
    background: transparent;
    border-radius: var(--radius-md);
    cursor: pointer;
    text-align: left;
    transition: background 0.15s;
  }

  .client-item:hover {
    background: var(--color-bg);
  }

  .client-item.selected {
    background: var(--color-primary-light);
  }

  .client-avatar {
    width: 40px;
    height: 40px;
    border-radius: var(--radius-md);
    background: linear-gradient(135deg, var(--color-primary) 0%, #2563eb 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 1rem;
    flex-shrink: 0;
  }

  .client-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .client-name {
    font-weight: 500;
    color: var(--color-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .client-location {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .client-actions {
    display: flex;
    gap: 0.25rem;
    opacity: 0;
    transition: opacity 0.15s;
  }

  .client-item:hover .client-actions {
    opacity: 1;
  }

  .btn-primary {
    background: var(--color-primary);
    color: white;
    border: none;
    padding: 0.5rem 0.75rem;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
  }

  .btn-primary:hover {
    background: var(--color-primary-hover);
  }

  .btn-secondary {
    background: var(--color-surface);
    color: var(--color-text);
    border: 1px solid var(--color-border);
    padding: 0.5rem 0.75rem;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
  }

  .btn-secondary:hover {
    background: var(--color-bg);
  }

  .btn-sm {
    padding: 0.375rem 0.625rem;
    font-size: 0.8125rem;
  }

  .btn-icon {
    background: transparent;
    border: none;
    color: var(--color-text-secondary);
    padding: 0.375rem;
    border-radius: var(--radius-sm);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .btn-icon:hover {
    background: var(--color-bg);
    color: var(--color-text);
  }

  .btn-icon.danger:hover {
    background: var(--color-danger-light);
    color: var(--color-danger);
  }

  .btn-link {
    background: none;
    border: none;
    color: var(--color-primary);
    font-size: 0.8125rem;
    font-weight: 500;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    text-decoration: none;
  }

  .btn-link:hover {
    text-decoration: underline;
  }

  .empty-list {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 1rem;
    color: var(--color-text-muted);
    text-align: center;
  }

  .empty-list svg {
    opacity: 0.3;
    margin-bottom: 0.75rem;
  }

  .empty-list p {
    margin-bottom: 1rem;
    font-size: 0.9375rem;
  }

  .detail-panel {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    padding: 1.5rem;
    overflow-y: auto;
  }

  .detail-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .detail-avatar {
    width: 56px;
    height: 56px;
    border-radius: var(--radius-lg);
    background: linear-gradient(135deg, var(--color-primary) 0%, #2563eb 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 1.5rem;
    flex-shrink: 0;
  }

  .detail-title {
    flex: 1;
  }

  .detail-title h2 {
    margin: 0;
    font-size: 1.375rem;
  }

  .detail-title p {
    margin: 0.25rem 0 0;
    color: var(--color-text-secondary);
    font-size: 0.9375rem;
  }

  .close-detail {
    align-self: flex-start;
  }

  .client-address {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: var(--color-bg);
    border-radius: var(--radius-md);
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    margin-bottom: 1.5rem;
  }

  .client-address svg {
    flex-shrink: 0;
    opacity: 0.5;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .stat-card {
    padding: 1rem;
    background: var(--color-bg);
    border-radius: var(--radius-md);
    text-align: center;
  }

  .stat-card.success {
    background: rgba(16, 185, 129, 0.08);
  }

  .stat-card.warning {
    background: rgba(245, 158, 11, 0.08);
  }

  .stat-card.info {
    background: rgba(59, 130, 246, 0.08);
  }

  .stat-value {
    display: block;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--color-text);
    margin-bottom: 0.25rem;
  }

  .stat-card.success .stat-value {
    color: #059669;
  }

  .stat-card.warning .stat-value {
    color: #d97706;
  }

  .stat-card.info .stat-value {
    color: #2563eb;
  }

  .stat-label {
    font-size: 0.75rem;
    color: var(--color-text-secondary);
  }

  .detail-section {
    margin-bottom: 1.5rem;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .section-header h3 {
    margin: 0;
    font-size: 0.9375rem;
    font-weight: 600;
  }

  .invoices-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .invoice-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1rem;
    background: var(--color-bg);
    border-radius: var(--radius-md);
  }

  .invoice-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .invoice-number {
    font-weight: 500;
    font-size: 0.875rem;
  }

  .invoice-date {
    font-size: 0.75rem;
    color: var(--color-text-secondary);
  }

  .invoice-amount {
    font-weight: 600;
    font-size: 0.9375rem;
  }

  .status-badge {
    padding: 0.25rem 0.625rem;
    border-radius: 999px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }

  .status-draft {
    background: var(--color-bg);
    color: var(--color-text-secondary);
  }

  .status-sent {
    background: rgba(59, 130, 246, 0.1);
    color: #2563eb;
  }

  .status-paid {
    background: rgba(16, 185, 129, 0.1);
    color: #059669;
  }

  .fee-form {
    padding: 1rem;
    background: var(--color-bg);
    border-radius: var(--radius-md);
    margin-bottom: 0.75rem;
  }

  .fees-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .fee-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1rem;
    background: var(--color-bg);
    border-radius: var(--radius-md);
  }

  .fee-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .fee-desc {
    font-weight: 500;
    font-size: 0.875rem;
  }

  .fee-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: var(--color-text-secondary);
  }

  .fee-badge {
    background: var(--color-primary-light);
    color: var(--color-primary);
    padding: 0.125rem 0.5rem;
    border-radius: 999px;
    font-size: 0.6875rem;
    font-weight: 500;
  }

  .fee-amount {
    font-weight: 600;
    font-size: 0.9375rem;
  }

  .fee-actions {
    display: flex;
    gap: 0.25rem;
  }

  .empty-section {
    text-align: center;
    color: var(--color-text-muted);
    font-size: 0.875rem;
    padding: 1.5rem;
    background: var(--color-bg);
    border-radius: var(--radius-md);
  }

  .no-selection {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    color: var(--color-text-muted);
  }

  .no-selection svg {
    opacity: 0.15;
    margin-bottom: 1rem;
  }

  .no-selection p {
    font-size: 0.9375rem;
  }

  @media (max-width: 1200px) {
    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 900px) {
    .clients-layout {
      grid-template-columns: 1fr;
    }

    .clients-layout.has-selection .clients-panel {
      display: none;
    }

    .no-selection {
      display: none;
    }

    .detail-panel {
      min-height: calc(100vh - 6rem);
    }
  }

  @media (max-width: 640px) {
    .form-row,
    .form-row-3 {
      grid-template-columns: 1fr;
    }

    .stats-grid {
      grid-template-columns: 1fr 1fr;
    }

    .invoice-item,
    .fee-item {
      flex-wrap: wrap;
    }
  }
</style>
