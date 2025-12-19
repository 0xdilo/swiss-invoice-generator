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
  let searchQuery = "";

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

  $: filteredClients = clients.filter(c =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.city.toLowerCase().includes(searchQuery.toLowerCase())
  );

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

  function getInitials(name) {
    return name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
  }

  function getAvatarColor(name) {
    const colors = [
      'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
      'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
      'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
      'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
      'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    ];
    const index = name.charCodeAt(0) % colors.length;
    return colors[index];
  }
</script>

<div class="clients-page">
  <div class="clients-panel" class:collapsed={selectedClient}>
    <header class="panel-header">
      <div class="header-top">
        <div>
          <h1>Clients</h1>
          <p class="client-count">{clients.length} total</p>
        </div>
        <button class="btn-add" onclick={() => { showForm = !showForm; if (!showForm) cancelForm(); }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            {#if showForm}
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            {:else}
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            {/if}
          </svg>
        </button>
      </div>

      <div class="search-wrapper">
        <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          type="text"
          class="search-input"
          placeholder="Search clients..."
          bind:value={searchQuery}
        />
      </div>
    </header>

    {#if showForm}
      <div class="form-card">
        <div class="form-header">
          <span class="form-badge">{editing !== null ? "Edit" : "New"}</span>
          <h3>{editing !== null ? "Edit Client" : "Add Client"}</h3>
        </div>
        <form onsubmit={(e) => { e.preventDefault(); submit(); }}>
          <div class="form-grid">
            <div class="form-field span-2">
              <label>Company / Name</label>
              <input placeholder="Acme Corporation" bind:value={form.name} required />
            </div>
            <div class="form-field span-2">
              <label>Email</label>
              <input type="email" placeholder="contact@acme.com" bind:value={form.email} required />
            </div>
            <div class="form-field span-2">
              <label>Street Address</label>
              <input placeholder="Bahnhofstrasse 1" bind:value={form.address} required />
            </div>
            <div class="form-field">
              <label>Postal Code</label>
              <input placeholder="8001" bind:value={form.cap} required />
            </div>
            <div class="form-field">
              <label>City</label>
              <input placeholder="Zürich" bind:value={form.city} required />
            </div>
            <div class="form-field span-2">
              <label>Country</label>
              <input placeholder="Switzerland" bind:value={form.nation} required />
            </div>
          </div>
          <div class="form-actions">
            <button type="button" class="btn-cancel" onclick={cancelForm}>Cancel</button>
            <button type="submit" class="btn-submit">{editing !== null ? "Save Changes" : "Add Client"}</button>
          </div>
        </form>
      </div>
    {/if}

    <div class="clients-list">
      {#each filteredClients as client, i}
        <div
          class="client-card"
          class:active={selectedClient?.id === client.id}
          onclick={() => selectClient(client)}
          onkeydown={(e) => e.key === 'Enter' && selectClient(client)}
          role="button"
          tabindex="0"
          style="animation-delay: {i * 30}ms"
        >
          <div class="client-avatar" style="background: {getAvatarColor(client.name)}">
            {getInitials(client.name)}
          </div>
          <div class="client-details">
            <span class="client-name">{client.name}</span>
            <span class="client-meta">{client.city}, {client.nation}</span>
          </div>
          <div class="client-actions">
            <button class="action-btn" onclick={(e) => edit(client, e)} title="Edit">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button class="action-btn danger" onclick={(e) => remove(client.id, e)} title="Delete">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </div>
        </div>
      {:else}
        <div class="empty-state">
          <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </div>
          <p>{searchQuery ? "No clients found" : "No clients yet"}</p>
          {#if !searchQuery}
            <button class="btn-add-first" onclick={() => showForm = true}>Add your first client</button>
          {/if}
        </div>
      {/each}
    </div>
  </div>

  <div class="detail-panel" class:visible={selectedClient}>
    {#if selectedClient}
      <header class="detail-header">
        <button class="btn-back" onclick={() => { selectedClient = null; clientStats = null; clientInvoices = []; recurringFees = []; }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          <span>Back</span>
        </button>
        <div class="detail-actions">
          <button class="action-btn" onclick={(e) => edit(selectedClient, e)}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            Edit
          </button>
        </div>
      </header>

      <div class="client-hero">
        <div class="hero-avatar" style="background: {getAvatarColor(selectedClient.name)}">
          {getInitials(selectedClient.name)}
        </div>
        <div class="hero-info">
          <h2>{selectedClient.name}</h2>
          <p class="hero-email">{selectedClient.email}</p>
          <div class="hero-address">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
            {selectedClient.address}, {selectedClient.cap} {selectedClient.city}, {selectedClient.nation}
          </div>
        </div>
      </div>

      {#if clientStats}
        <div class="stats-row">
          <div class="stat-block">
            <span class="stat-value">{formatCurrency(clientStats.total_invoiced)}</span>
            <span class="stat-label">Total Invoiced</span>
          </div>
          <div class="stat-block success">
            <span class="stat-value">{formatCurrency(clientStats.total_paid)}</span>
            <span class="stat-label">Paid ({clientStats.paid_invoices})</span>
          </div>
          <div class="stat-block warning">
            <span class="stat-value">{formatCurrency(clientStats.total_outstanding)}</span>
            <span class="stat-label">Outstanding ({clientStats.outstanding_invoices})</span>
          </div>
          <div class="stat-block accent">
            <span class="stat-value">{formatCurrency(clientStats.annual_recurring)}</span>
            <span class="stat-label">Annual Recurring</span>
          </div>
        </div>
      {/if}

      <section class="detail-section">
        <div class="section-header">
          <h3>Recent Invoices</h3>
          <a href="/invoices?client={selectedClient.id}" class="link-view">
            View all
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </a>
        </div>
        {#if clientInvoices.length > 0}
          <div class="invoice-list">
            {#each clientInvoices.slice(0, 5) as invoice, i}
              <div class="invoice-row" style="animation-delay: {i * 50}ms">
                <div class="invoice-id">
                  <span class="id-hash">#</span>{invoice.id}
                </div>
                <div class="invoice-date">{formatDate(invoice.created_at)}</div>
                <div class="invoice-amount">{formatCurrency(invoice.total_amount)}</div>
                <span class="status-pill {getStatusColor(invoice.status)}">{invoice.status || "draft"}</span>
              </div>
            {/each}
          </div>
        {:else}
          <div class="empty-section">
            <p>No invoices yet</p>
          </div>
        {/if}
      </section>

      <section class="detail-section">
        <div class="section-header">
          <h3>Recurring Fees</h3>
          <button class="link-view" onclick={() => { showFeeForm = !showFeeForm; if (!showFeeForm) cancelFeeForm(); }}>
            {#if showFeeForm}
              Cancel
            {:else}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Add fee
            {/if}
          </button>
        </div>

        {#if showFeeForm}
          <form class="fee-form" onsubmit={(e) => { e.preventDefault(); submitFee(); }}>
            <div class="fee-form-grid">
              <div class="form-field">
                <label>Description</label>
                <input placeholder="Annual maintenance" bind:value={feeForm.description} />
              </div>
              <div class="form-field">
                <label>Amount</label>
                <input type="number" step="0.01" placeholder="400.00" bind:value={feeForm.amount} required />
              </div>
              <div class="form-field">
                <label>Currency</label>
                <select bind:value={feeForm.currency}>
                  <option value="CHF">CHF</option>
                  <option value="EUR">EUR</option>
                  <option value="USD">USD</option>
                </select>
              </div>
              <div class="form-field">
                <label>Frequency</label>
                <select bind:value={feeForm.frequency}>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                  <option value="one-time">One-time</option>
                </select>
              </div>
              <div class="form-field">
                <label>Start Date</label>
                <input type="date" bind:value={feeForm.start_date} required />
              </div>
            </div>
            <div class="form-actions compact">
              <button type="button" class="btn-cancel" onclick={cancelFeeForm}>Cancel</button>
              <button type="submit" class="btn-submit">{editingFee !== null ? "Update" : "Add Fee"}</button>
            </div>
          </form>
        {/if}

        {#if recurringFees.length > 0}
          <div class="fee-list">
            {#each recurringFees as fee, i}
              <div class="fee-row" style="animation-delay: {i * 50}ms">
                <div class="fee-info">
                  <span class="fee-desc">{fee.description || "Recurring fee"}</span>
                  <span class="fee-meta">
                    <span class="freq-badge">{fee.frequency}</span>
                    from {formatDate(fee.start_date)}
                  </span>
                </div>
                <div class="fee-amount">{formatCurrency(fee.amount, fee.currency)}</div>
                <div class="fee-actions">
                  <button class="action-btn" onclick={() => editFee(fee)}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button class="action-btn danger" onclick={() => removeFee(fee.id)}>
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
          <div class="empty-section">
            <p>No recurring fees</p>
          </div>
        {/if}
      </section>
    {:else}
      <div class="no-selection">
        <div class="no-selection-icon">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="0.5">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
        </div>
        <p>Select a client to view details</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .clients-page {
    display: grid;
    grid-template-columns: 400px 1fr;
    gap: 1.5rem;
    min-height: calc(100vh - 6rem);
  }

  .clients-panel {
    display: flex;
    flex-direction: column;
    background: var(--color-surface);
    border-radius: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
    overflow: hidden;
    transition: transform 0.3s ease, opacity 0.3s ease;
  }

  .panel-header {
    padding: 1.5rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .header-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  .panel-header h1 {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.03em;
  }

  .client-count {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
    margin: 0.25rem 0 0;
  }

  .btn-add {
    width: 40px;
    height: 40px;
    border-radius: 12px;
    border: none;
    background: var(--color-primary);
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
  }

  .btn-add:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  }

  .search-wrapper {
    position: relative;
  }

  .search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--color-text-muted);
    pointer-events: none;
  }

  .search-input {
    width: 100%;
    padding: 0.625rem 0.875rem 0.625rem 2.5rem;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    font-size: 0.875rem;
    background: var(--color-bg);
    transition: all 0.2s ease;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .search-input::placeholder {
    color: var(--color-text-muted);
  }

  .form-card {
    padding: 1.5rem;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-bottom: 1px solid var(--color-border-light);
    animation: slideDown 0.3s ease;
  }

  @keyframes slideDown {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .form-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.25rem;
  }

  .form-badge {
    background: var(--color-primary);
    color: white;
    font-size: 0.6875rem;
    font-weight: 600;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .form-header h3 {
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
  }

  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .form-field {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .form-field.span-2 {
    grid-column: span 2;
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
    font-size: 0.875rem;
    background: white;
    transition: all 0.2s ease;
  }

  .form-field input:focus,
  .form-field select:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    margin-top: 1.5rem;
    padding-top: 1.25rem;
    border-top: 1px solid var(--color-border-light);
  }

  .form-actions.compact {
    margin-top: 1rem;
    padding-top: 1rem;
  }

  .btn-cancel {
    padding: 0.5rem 1rem;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: white;
    color: var(--color-text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-cancel:hover {
    background: var(--color-bg);
  }

  .btn-submit {
    padding: 0.5rem 1.25rem;
    border: none;
    border-radius: 8px;
    background: var(--color-primary);
    color: white;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-submit:hover {
    background: var(--color-primary-hover);
    transform: translateY(-1px);
  }

  .clients-list {
    flex: 1;
    overflow-y: auto;
    padding: 0.75rem;
  }

  .client-card {
    display: flex;
    align-items: center;
    gap: 0.875rem;
    width: 100%;
    padding: 0.875rem;
    border: none;
    background: transparent;
    border-radius: 12px;
    cursor: pointer;
    text-align: left;
    transition: all 0.2s ease;
    animation: fadeIn 0.4s ease backwards;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateX(-8px); }
    to { opacity: 1; transform: translateX(0); }
  }

  .client-card:hover {
    background: var(--color-bg);
  }

  .client-card.active {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%);
  }

  .client-avatar {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.875rem;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  }

  .client-details {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .client-name {
    font-weight: 600;
    font-size: 0.9375rem;
    color: var(--color-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .client-meta {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .client-actions {
    display: flex;
    gap: 0.25rem;
    opacity: 0;
    transition: opacity 0.2s ease;
  }

  .client-card:hover .client-actions {
    opacity: 1;
  }

  .action-btn {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.375rem;
    border: none;
    background: transparent;
    color: var(--color-text-secondary);
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.8125rem;
    transition: all 0.15s ease;
  }

  .action-btn:hover {
    background: var(--color-surface);
    color: var(--color-text);
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
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: var(--color-bg);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1rem;
  }

  .empty-icon svg {
    color: var(--color-text-muted);
    opacity: 0.5;
  }

  .empty-state p {
    color: var(--color-text-secondary);
    margin: 0 0 1rem;
  }

  .btn-add-first {
    padding: 0.5rem 1rem;
    background: var(--color-primary);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-add-first:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
  }

  .detail-panel {
    background: var(--color-surface);
    border-radius: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
    overflow-y: auto;
    display: flex;
    flex-direction: column;
  }

  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .btn-back {
    display: none;
    align-items: center;
    gap: 0.375rem;
    padding: 0.5rem 0.75rem;
    border: none;
    background: transparent;
    color: var(--color-text-secondary);
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.15s ease;
  }

  .btn-back:hover {
    background: var(--color-bg);
    color: var(--color-text);
  }

  .detail-actions {
    display: flex;
    gap: 0.5rem;
  }

  .client-hero {
    padding: 2rem 1.5rem;
    display: flex;
    gap: 1.25rem;
    align-items: flex-start;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  }

  .hero-avatar {
    width: 72px;
    height: 72px;
    border-radius: 16px;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1.5rem;
    flex-shrink: 0;
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  }

  .hero-info {
    flex: 1;
  }

  .hero-info h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.02em;
  }

  .hero-email {
    margin: 0.375rem 0 0.75rem;
    color: var(--color-text-secondary);
    font-size: 0.9375rem;
  }

  .hero-address {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .hero-address svg {
    opacity: 0.5;
    flex-shrink: 0;
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    padding: 1.5rem;
  }

  .stat-block {
    padding: 1rem;
    background: var(--color-bg);
    border-radius: 12px;
    text-align: center;
    transition: transform 0.2s ease;
  }

  .stat-block:hover {
    transform: translateY(-2px);
  }

  .stat-block.success { background: rgba(16, 185, 129, 0.08); }
  .stat-block.warning { background: rgba(245, 158, 11, 0.08); }
  .stat-block.accent { background: rgba(99, 102, 241, 0.08); }

  .stat-value {
    display: block;
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--color-text);
    margin-bottom: 0.25rem;
  }

  .stat-block.success .stat-value { color: #059669; }
  .stat-block.warning .stat-value { color: #d97706; }
  .stat-block.accent .stat-value { color: #6366f1; }

  .stat-label {
    font-size: 0.75rem;
    color: var(--color-text-secondary);
    font-weight: 500;
  }

  .detail-section {
    padding: 1.5rem;
    border-top: 1px solid var(--color-border-light);
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .section-header h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
  }

  .link-view {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    color: var(--color-primary);
    font-size: 0.8125rem;
    font-weight: 500;
    text-decoration: none;
    cursor: pointer;
    background: none;
    border: none;
    transition: gap 0.2s ease;
  }

  .link-view:hover {
    gap: 0.5rem;
  }

  .invoice-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .invoice-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.875rem 1rem;
    background: var(--color-bg);
    border-radius: 10px;
    animation: fadeIn 0.4s ease backwards;
  }

  .invoice-id {
    font-weight: 600;
    font-size: 0.875rem;
    min-width: 60px;
  }

  .id-hash {
    color: var(--color-text-muted);
    font-weight: 400;
  }

  .invoice-date {
    flex: 1;
    font-size: 0.875rem;
    color: var(--color-text-secondary);
  }

  .invoice-amount {
    font-weight: 600;
    font-size: 0.9375rem;
  }

  .status-pill {
    padding: 0.25rem 0.625rem;
    border-radius: 999px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .status-draft {
    background: var(--color-bg);
    color: var(--color-text-secondary);
    border: 1px solid var(--color-border);
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
    padding: 1.25rem;
    background: var(--color-bg);
    border-radius: 12px;
    margin-bottom: 1rem;
    animation: slideDown 0.3s ease;
  }

  .fee-form-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
  }

  .fee-form-grid .form-field:first-child {
    grid-column: span 2;
  }

  .fee-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .fee-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.875rem 1rem;
    background: var(--color-bg);
    border-radius: 10px;
    animation: fadeIn 0.4s ease backwards;
  }

  .fee-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .fee-desc {
    font-weight: 600;
    font-size: 0.875rem;
  }

  .fee-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: var(--color-text-secondary);
  }

  .freq-badge {
    background: var(--color-primary-light);
    color: var(--color-primary);
    padding: 0.125rem 0.5rem;
    border-radius: 999px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .fee-amount {
    font-weight: 700;
    font-size: 1rem;
  }

  .fee-actions {
    display: flex;
    gap: 0.25rem;
  }

  .empty-section {
    text-align: center;
    color: var(--color-text-muted);
    font-size: 0.875rem;
    padding: 2rem;
    background: var(--color-bg);
    border-radius: 10px;
  }

  .empty-section p {
    margin: 0;
  }

  .no-selection {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: var(--color-text-muted);
  }

  .no-selection-icon {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: var(--color-bg);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1.5rem;
  }

  .no-selection-icon svg {
    opacity: 0.3;
  }

  .no-selection p {
    font-size: 1rem;
    margin: 0;
  }

  @media (max-width: 1200px) {
    .stats-row {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 900px) {
    .clients-page {
      grid-template-columns: 1fr;
    }

    .clients-panel.collapsed {
      display: none;
    }

    .detail-panel {
      display: none;
    }

    .detail-panel.visible {
      display: flex;
    }

    .btn-back {
      display: flex;
    }

    .no-selection {
      display: none;
    }
  }

  @media (max-width: 640px) {
    .form-grid {
      grid-template-columns: 1fr;
    }

    .form-field.span-2 {
      grid-column: span 1;
    }

    .stats-row {
      grid-template-columns: 1fr;
    }

    .fee-form-grid {
      grid-template-columns: 1fr;
    }

    .fee-form-grid .form-field:first-child {
      grid-column: span 1;
    }

    .invoice-row {
      flex-wrap: wrap;
    }

    .invoice-date {
      order: 3;
      flex-basis: 100%;
      margin-top: 0.5rem;
    }

    .client-hero {
      flex-direction: column;
      align-items: center;
      text-align: center;
    }

    .hero-address {
      justify-content: center;
    }
  }
</style>
