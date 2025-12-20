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

<div class="grid grid-cols-1 md:grid-cols-[400px_1fr] gap-6 min-h-[calc(100vh-6rem)]">
  <div class="flex flex-col bg-surface rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04),0_4px_12px_rgba(0,0,0,0.03)] overflow-hidden transition-all duration-300 {selectedClient ? 'md:block hidden' : ''}">
    <header class="p-6 border-b border-border-light">
      <div class="flex justify-between items-start mb-4">
        <div>
          <h1 class="text-2xl font-bold tracking-tight">Clients</h1>
          <p class="text-[0.8125rem] text-text-secondary mt-1">{clients.length} total</p>
        </div>
        <button
          class="w-10 h-10 rounded-xl border-0 bg-primary text-white cursor-pointer flex items-center justify-center transition-all duration-200 hover:scale-105 hover:shadow-[0_4px_12px_rgba(59,130,246,0.3)]"
          onclick={() => { showForm = !showForm; if (!showForm) cancelForm(); }}
        >
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

      <div class="relative">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          type="text"
          class="w-full py-2.5 px-3.5 pl-10 border border-border rounded-[10px] text-sm bg-bg transition-all duration-200 focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(59,130,246,0.1)] placeholder:text-text-muted"
          placeholder="Search clients..."
          bind:value={searchQuery}
        />
      </div>
    </header>

    {#if showForm}
      <div class="p-6 border-b border-border-light animate-[slideDown_0.3s_ease]" style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);">
        <div class="flex items-center gap-3 mb-5">
          <span class="bg-primary text-white text-[0.6875rem] font-semibold py-1 px-2 rounded-md uppercase tracking-wider">
            {editing !== null ? "Edit" : "New"}
          </span>
          <h3 class="text-base font-semibold m-0">{editing !== null ? "Edit Client" : "Add Client"}</h3>
        </div>
        <form onsubmit={(e) => { e.preventDefault(); submit(); }}>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5 col-span-1 sm:col-span-2">
              <label class="form-label">Company / Name</label>
              <input class="form-input" placeholder="Acme Corporation" bind:value={form.name} required />
            </div>
            <div class="flex flex-col gap-1.5 col-span-1 sm:col-span-2">
              <label class="form-label">Email</label>
              <input class="form-input" type="email" placeholder="contact@acme.com" bind:value={form.email} required />
            </div>
            <div class="flex flex-col gap-1.5 col-span-1 sm:col-span-2">
              <label class="form-label">Street Address</label>
              <input class="form-input" placeholder="Bahnhofstrasse 1" bind:value={form.address} required />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="form-label">Postal Code</label>
              <input class="form-input" placeholder="8001" bind:value={form.cap} required />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="form-label">City</label>
              <input class="form-input" placeholder="Zürich" bind:value={form.city} required />
            </div>
            <div class="flex flex-col gap-1.5 col-span-1 sm:col-span-2">
              <label class="form-label">Country</label>
              <input class="form-input" placeholder="Switzerland" bind:value={form.nation} required />
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-6 pt-5 border-t border-border-light">
            <button type="button" class="btn-cancel" onclick={cancelForm}>Cancel</button>
            <button type="submit" class="btn-primary">{editing !== null ? "Save Changes" : "Add Client"}</button>
          </div>
        </form>
      </div>
    {/if}

    <div class="flex-1 overflow-y-auto p-3">
      {#each filteredClients as client, i}
        <div
          class="flex items-center gap-3.5 w-full py-3.5 px-3.5 border-0 bg-transparent rounded-xl cursor-pointer text-left transition-all duration-200 animate-fade-in hover:bg-bg {selectedClient?.id === client.id ? 'active-client' : ''}"
          onclick={() => selectClient(client)}
          onkeydown={(e) => e.key === 'Enter' && selectClient(client)}
          role="button"
          tabindex="0"
          style="animation-delay: {i * 30}ms; background: {selectedClient?.id === client.id ? 'linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%)' : ''}"
        >
          <div class="w-11 h-11 rounded-xl text-white flex items-center justify-center font-semibold text-sm flex-shrink-0 shadow-[0_2px_8px_rgba(0,0,0,0.15)]" style="background: {getAvatarColor(client.name)}">
            {getInitials(client.name)}
          </div>
          <div class="flex-1 min-w-0 flex flex-col gap-1">
            <span class="font-semibold text-[0.9375rem] text-text whitespace-nowrap overflow-hidden text-ellipsis">{client.name}</span>
            <span class="text-[0.8125rem] text-text-secondary">{client.city}, {client.nation}</span>
          </div>
          <div class="flex gap-1 opacity-0 transition-opacity duration-200 client-actions-hover">
            <button class="flex items-center gap-1.5 py-1.5 px-1.5 border-0 bg-transparent text-text-secondary rounded-md cursor-pointer text-[0.8125rem] transition-all duration-150 hover:bg-surface hover:text-text" onclick={(e) => edit(client, e)} title="Edit">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button class="flex items-center gap-1.5 py-1.5 px-1.5 border-0 bg-transparent text-text-secondary rounded-md cursor-pointer text-[0.8125rem] transition-all duration-150 hover:bg-[rgba(239,68,68,0.1)] hover:text-[#ef4444]" onclick={(e) => remove(client.id, e)} title="Delete">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </div>
        </div>
      {:else}
        <div class="flex flex-col items-center justify-center py-16 px-8 text-center">
          <div class="w-20 h-20 rounded-full bg-bg flex items-center justify-center mb-4">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" class="text-text-muted opacity-50">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </div>
          <p class="text-text-secondary m-0 mb-4">{searchQuery ? "No clients found" : "No clients yet"}</p>
          {#if !searchQuery}
            <button class="py-2 px-4 bg-primary text-white border-0 rounded-lg text-sm font-medium cursor-pointer transition-all duration-200 hover:-translate-y-px hover:shadow-[0_4px_12px_rgba(59,130,246,0.25)]" onclick={() => showForm = true}>Add your first client</button>
          {/if}
        </div>
      {/each}
    </div>
  </div>

  <div class="bg-surface rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04),0_4px_12px_rgba(0,0,0,0.03)] overflow-y-auto flex flex-col {selectedClient ? 'flex' : 'hidden md:flex'}">
    {#if selectedClient}
      <header class="flex justify-between items-center py-4 px-6 border-b border-border-light">
        <button class="hidden md:flex items-center gap-1.5 py-2 px-3 border-0 bg-transparent text-text-secondary rounded-lg cursor-pointer text-sm transition-all duration-150 hover:bg-bg hover:text-text detail-back-btn" onclick={() => { selectedClient = null; clientStats = null; clientInvoices = []; recurringFees = []; }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          <span>Back</span>
        </button>
        <div class="flex gap-2">
          <button class="flex items-center gap-1.5 py-1.5 px-1.5 border-0 bg-transparent text-text-secondary rounded-md cursor-pointer text-[0.8125rem] transition-all duration-150 hover:bg-surface hover:text-text" onclick={(e) => edit(selectedClient, e)}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            Edit
          </button>
        </div>
      </header>

      <div class="py-8 px-6 flex gap-5 items-start" style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);">
        <div class="w-[72px] h-[72px] rounded-2xl text-white flex items-center justify-center font-bold text-2xl flex-shrink-0 shadow-[0_4px_16px_rgba(0,0,0,0.15)]" style="background: {getAvatarColor(selectedClient.name)}">
          {getInitials(selectedClient.name)}
        </div>
        <div class="flex-1">
          <h2 class="m-0 text-2xl font-bold tracking-tight">{selectedClient.name}</h2>
          <p class="mt-1.5 mb-3 text-text-secondary text-[0.9375rem]">{selectedClient.email}</p>
          <div class="flex items-center gap-2 text-[0.8125rem] text-text-secondary">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="opacity-50 flex-shrink-0">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
            {selectedClient.address}, {selectedClient.cap} {selectedClient.city}, {selectedClient.nation}
          </div>
        </div>
      </div>

      {#if clientStats}
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-6">
          <div class="p-4 bg-bg rounded-xl text-center transition-transform duration-200 hover:-translate-y-0.5">
            <span class="block text-lg font-bold text-text mb-1">{formatCurrency(clientStats.total_invoiced)}</span>
            <span class="text-xs text-text-secondary font-medium">Total Invoiced</span>
          </div>
          <div class="p-4 rounded-xl text-center transition-transform duration-200 hover:-translate-y-0.5" style="background: rgba(16, 185, 129, 0.08);">
            <span class="block text-lg font-bold mb-1" style="color: #059669;">{formatCurrency(clientStats.total_paid)}</span>
            <span class="text-xs text-text-secondary font-medium">Paid ({clientStats.paid_invoices})</span>
          </div>
          <div class="p-4 rounded-xl text-center transition-transform duration-200 hover:-translate-y-0.5" style="background: rgba(245, 158, 11, 0.08);">
            <span class="block text-lg font-bold mb-1" style="color: #d97706;">{formatCurrency(clientStats.total_outstanding)}</span>
            <span class="text-xs text-text-secondary font-medium">Outstanding ({clientStats.outstanding_invoices})</span>
          </div>
          <div class="p-4 rounded-xl text-center transition-transform duration-200 hover:-translate-y-0.5" style="background: rgba(99, 102, 241, 0.08);">
            <span class="block text-lg font-bold mb-1" style="color: #6366f1;">{formatCurrency(clientStats.annual_recurring)}</span>
            <span class="text-xs text-text-secondary font-medium">Annual Recurring</span>
          </div>
        </div>
      {/if}

      <section class="p-6 border-t border-border-light">
        <div class="flex justify-between items-center mb-4">
          <h3 class="m-0 text-base font-semibold">Recent Invoices</h3>
          <a href="/invoices?client={selectedClient.id}" class="flex items-center gap-1 text-primary text-[0.8125rem] font-medium no-underline cursor-pointer transition-all duration-200 hover:gap-2">
            View all
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </a>
        </div>
        {#if clientInvoices.length > 0}
          <div class="flex flex-col gap-2">
            {#each clientInvoices.slice(0, 5) as invoice, i}
              <div class="flex flex-wrap items-center gap-4 py-3.5 px-4 bg-bg rounded-[10px] animate-fade-in" style="animation-delay: {i * 50}ms">
                <div class="font-semibold text-sm min-w-[60px]">
                  <span class="text-text-muted font-normal">#</span>{invoice.id}
                </div>
                <div class="flex-1 text-sm text-text-secondary invoice-date-responsive">{formatDate(invoice.created_at)}</div>
                <div class="font-semibold text-[0.9375rem]">{formatCurrency(invoice.total_amount)}</div>
                <span class="py-1 px-2.5 rounded-full text-[0.6875rem] font-semibold uppercase tracking-wide {getStatusColor(invoice.status)}">{invoice.status || "draft"}</span>
              </div>
            {/each}
          </div>
        {:else}
          <div class="text-center text-text-muted text-sm py-8 bg-bg rounded-[10px]">
            <p class="m-0">No invoices yet</p>
          </div>
        {/if}
      </section>

      <section class="p-6 border-t border-border-light">
        <div class="flex justify-between items-center mb-4">
          <h3 class="m-0 text-base font-semibold">Recurring Fees</h3>
          <button class="flex items-center gap-1 text-primary text-[0.8125rem] font-medium cursor-pointer bg-transparent border-0 transition-all duration-200 hover:gap-2" onclick={() => { showFeeForm = !showFeeForm; if (!showFeeForm) cancelFeeForm(); }}>
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
          <form class="p-5 bg-bg rounded-xl mb-4 animate-[slideDown_0.3s_ease]" onsubmit={(e) => { e.preventDefault(); submitFee(); }}>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div class="flex flex-col gap-1.5 col-span-1 sm:col-span-2">
                <label class="form-label">Description</label>
                <input class="form-input" placeholder="Annual maintenance" bind:value={feeForm.description} />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="form-label">Amount</label>
                <input class="form-input" type="number" step="0.01" placeholder="400.00" bind:value={feeForm.amount} required />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="form-label">Currency</label>
                <select class="form-input" bind:value={feeForm.currency}>
                  <option value="CHF">CHF</option>
                  <option value="EUR">EUR</option>
                  <option value="USD">USD</option>
                </select>
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="form-label">Frequency</label>
                <select class="form-input" bind:value={feeForm.frequency}>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                  <option value="one-time">One-time</option>
                </select>
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="form-label">Start Date</label>
                <input class="form-input" type="date" bind:value={feeForm.start_date} required />
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-4 pt-4 border-t border-border-light">
              <button type="button" class="btn-cancel" onclick={cancelFeeForm}>Cancel</button>
              <button type="submit" class="btn-primary">{editingFee !== null ? "Update" : "Add Fee"}</button>
            </div>
          </form>
        {/if}

        {#if recurringFees.length > 0}
          <div class="flex flex-col gap-2">
            {#each recurringFees as fee, i}
              <div class="flex items-center gap-4 py-3.5 px-4 bg-bg rounded-[10px] animate-fade-in" style="animation-delay: {i * 50}ms">
                <div class="flex-1 flex flex-col gap-1">
                  <span class="font-semibold text-sm">{fee.description || "Recurring fee"}</span>
                  <span class="flex items-center gap-2 text-xs text-text-secondary">
                    <span class="py-0.5 px-2 rounded-full text-[0.6875rem] font-semibold uppercase" style="background: var(--color-primary-light); color: var(--color-primary);">{fee.frequency}</span>
                    from {formatDate(fee.start_date)}
                  </span>
                </div>
                <div class="font-bold text-base">{formatCurrency(fee.amount, fee.currency)}</div>
                <div class="flex gap-1">
                  <button class="flex items-center gap-1.5 py-1.5 px-1.5 border-0 bg-transparent text-text-secondary rounded-md cursor-pointer text-[0.8125rem] transition-all duration-150 hover:bg-surface hover:text-text" onclick={() => editFee(fee)}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button class="flex items-center gap-1.5 py-1.5 px-1.5 border-0 bg-transparent text-text-secondary rounded-md cursor-pointer text-[0.8125rem] transition-all duration-150 hover:bg-[rgba(239,68,68,0.1)] hover:text-[#ef4444]" onclick={() => removeFee(fee.id)}>
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
          <div class="text-center text-text-muted text-sm py-8 bg-bg rounded-[10px]">
            <p class="m-0">No recurring fees</p>
          </div>
        {/if}
      </section>
    {:else}
      <div class="flex-1 flex flex-col items-center justify-center text-text-muted">
        <div class="w-[120px] h-[120px] rounded-full bg-bg flex items-center justify-center mb-6">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="0.5" class="opacity-30">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
        </div>
        <p class="text-base m-0">Select a client to view details</p>
      </div>
    {/if}
  </div>
</div>

<style>
  @keyframes slideDown {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .client-actions-hover {
    opacity: 0;
  }

  div:hover > .client-actions-hover {
    opacity: 1;
  }

  @media (max-width: 900px) {
    .detail-back-btn {
      display: flex !important;
    }
  }

  @media (max-width: 640px) {
    .invoice-date-responsive {
      order: 3;
      flex-basis: 100%;
      margin-top: 0.5rem;
    }
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
</style>
