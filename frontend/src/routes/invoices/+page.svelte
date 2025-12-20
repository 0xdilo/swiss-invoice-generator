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

<div class="max-w-screen-xl mx-auto">
  <header class="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6">
    <div>
      <h1 class="text-[1.75rem] font-bold m-0 tracking-tight">Invoices</h1>
      <p class="mt-1 mb-0 text-text-secondary text-[0.9375rem]">Manage your billing and payments</p>
    </div>
    <button class="flex items-center gap-2 px-5 py-2.5 bg-primary text-white border-none rounded-[10px] text-[0.9375rem] font-semibold cursor-pointer transition-all duration-200 hover:bg-primary-hover hover:-translate-y-px hover:shadow-[0_4px_12px_rgba(59,130,246,0.3)] w-full sm:w-auto justify-center" onclick={() => { showForm = !showForm; if (!showForm) cancelForm(); }}>
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

  <div class="flex flex-wrap items-center gap-6 px-6 py-4 bg-surface rounded-[14px] shadow-[0_1px_3px_rgba(0,0,0,0.04)] mb-6">
    <div class="flex flex-col gap-0.5">
      <span class="text-xs text-text-muted uppercase tracking-wide font-medium">Total</span>
      <span class="text-xl font-bold text-text">{stats.total}</span>
    </div>
    <div class="w-px h-8 bg-border-light hidden sm:block"></div>
    <div class="flex flex-col gap-0.5">
      <span class="text-xs text-text-muted uppercase tracking-wide font-medium">Draft</span>
      <span class="text-xl font-bold text-text-secondary">{stats.draft}</span>
    </div>
    <div class="flex flex-col gap-0.5">
      <span class="text-xs text-text-muted uppercase tracking-wide font-medium">Sent</span>
      <span class="text-xl font-bold text-[#d97706]">{stats.sent}</span>
    </div>
    <div class="flex flex-col gap-0.5">
      <span class="text-xs text-text-muted uppercase tracking-wide font-medium">Paid</span>
      <span class="text-xl font-bold text-[#059669]">{stats.paid}</span>
    </div>
    <div class="w-px h-8 bg-border-light hidden sm:block"></div>
    <div class="flex flex-col gap-0.5 sm:ml-auto w-full sm:w-auto sm:pt-0 pt-3 sm:border-t-0 border-t border-border-light">
      <span class="text-xs text-text-muted uppercase tracking-wide font-medium">Revenue</span>
      <span class="text-xl font-bold text-text">{formatCurrency(stats.paidAmount)}</span>
    </div>
  </div>

  {#if showForm}
    <div class="card mb-6 overflow-hidden animate-slide-down relative">
      <div class="absolute top-5 right-6 bg-primary text-white text-[0.6875rem] font-semibold px-2.5 py-1 rounded-md uppercase tracking-wide">{editing !== null ? "Edit" : "New"}</div>
      <form class="p-6" onsubmit={(e) => { e.preventDefault(); submit(); }}>
        <div class="mb-6 pb-6 border-b border-border-light">
          <h3 class="text-[0.9375rem] font-semibold m-0 mb-4 text-text">Invoice Details</h3>
          <div class="flex flex-col sm:flex-row gap-4 mb-4">
            <div class="flex flex-col gap-1.5 flex-[2]">
              <label class="form-label">Title</label>
              <input class="form-input" placeholder="e.g., Website Maintenance Q4 2024" bind:value={invoiceTitle} required />
            </div>
          </div>
          <div class="flex flex-col sm:flex-row gap-4 mb-4">
            <div class="flex flex-col gap-1.5 flex-[2]">
              <label class="form-label">Description</label>
              <input class="form-input" placeholder="Brief description (optional)" bind:value={invoiceDescription} />
            </div>
          </div>
          <div class="flex flex-col sm:flex-row gap-4 mb-4">
            <div class="flex flex-col gap-1.5 flex-1">
              <label class="form-label">Client</label>
              <select class="form-input" bind:value={client_id} required>
                <option value="" disabled>Select client</option>
                {#each clients as c}
                  <option value={c.id}>{c.name}</option>
                {/each}
              </select>
            </div>
            <div class="flex flex-col gap-1.5 flex-1">
              <label class="form-label">Template</label>
              <select class="form-input" bind:value={template_id} required>
                <option value="" disabled>Select template</option>
                {#each templates as t}
                  <option value={t.id}>{t.name}</option>
                {/each}
              </select>
            </div>
          </div>

          {#if showLogoUploadUI}
            <div class="flex flex-col sm:flex-row gap-4 mb-4">
              <div class="flex flex-col gap-1.5 flex-1">
                <label class="form-label">Logo</label>
                <input class="form-input" type="file" accept="image/*" bind:files={logoUploadFile} />
              </div>
            </div>
          {/if}

          {#if dynamicFields.length > 0}
            <div class="flex flex-col sm:flex-row gap-4">
              {#each dynamicFields as field}
                <div class="flex flex-col gap-1.5 flex-1">
                  <label class="form-label">{field}</label>
                  <input
                    class="form-input"
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

        <div class="mb-6 pb-6 border-b border-border-light">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-[0.9375rem] font-semibold m-0 text-text">Line Items</h3>
            <button type="button" class="flex items-center gap-1.5 px-3.5 py-2 bg-transparent text-primary border border-dashed border-primary rounded-lg text-[0.8125rem] font-medium cursor-pointer transition-all duration-200 hover:bg-primary/10" onclick={addItem}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Add Item
            </button>
          </div>

          <div class="bg-bg rounded-[10px] overflow-hidden">
            <div class="hidden sm:grid grid-cols-[3fr_120px_80px_120px_40px] gap-3 px-4 py-3 bg-surface border-b border-border-light text-[0.6875rem] font-semibold text-text-muted uppercase tracking-wide">
              <span>Description</span>
              <span>Price</span>
              <span>Qty</span>
              <span>Total</span>
              <span></span>
            </div>
            {#each items as item, i}
              <div class="grid grid-cols-1 sm:grid-cols-[3fr_120px_80px_120px_40px] gap-2 sm:gap-3 px-4 py-3 sm:items-center border-b border-border-light last:border-b-0 animate-fade-in relative" style="animation-delay: {i * 50}ms">
                <div>
                  <input class="px-3 py-2 border border-border-light rounded-md text-sm bg-white w-full focus:outline-none focus:border-primary" placeholder="Service description" bind:value={item.desc} required />
                </div>
                <div>
                  <input class="px-3 py-2 border border-border-light rounded-md text-sm bg-white w-full focus:outline-none focus:border-primary" type="number" placeholder="0.00" bind:value={item.price} step="0.01" min="0" required />
                </div>
                <div>
                  <input class="px-3 py-2 border border-border-light rounded-md text-sm bg-white w-full focus:outline-none focus:border-primary" type="number" placeholder="1" bind:value={item.qty} step="0.1" min="0" required />
                </div>
                <div class="sm:pt-0 pt-2 sm:border-t-0 border-t border-border-light sm:text-left">
                  <span class="font-semibold text-text-secondary">{formatCurrency(item.price * item.qty)}</span>
                </div>
                <div class="sm:static absolute top-2 right-2">
                  {#if items.length > 1}
                    <button type="button" class="w-8 h-8 flex items-center justify-center bg-transparent border-none rounded-md text-text-muted cursor-pointer transition-all duration-150 hover:bg-red-50 hover:text-red-500" onclick={() => removeItem(i)}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  {/if}
                </div>
              </div>
            {/each}
            <div class="flex justify-end items-center gap-8 px-4 py-4 bg-surface border-t border-border-light">
              <span class="text-sm text-text-secondary font-medium">Subtotal</span>
              <span class="text-lg font-bold text-text">{formatCurrency(itemsTotal)}</span>
            </div>
          </div>
        </div>

        <div class="mb-4 px-5 py-5 bg-bg rounded-xl">
          <label class="flex items-start gap-3.5 cursor-pointer">
            <input type="checkbox" class="hidden" bind:checked={isRecurring} />
            <div class="w-11 h-6 bg-border rounded-xl relative flex-shrink-0 transition-all duration-200 {isRecurring ? 'bg-primary' : ''}">
              <div class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-all duration-200 {isRecurring ? 'translate-x-5' : ''}"></div>
            </div>
            <div class="flex flex-col gap-0.5">
              <span class="font-semibold text-[0.9375rem]">Set as recurring</span>
              <span class="text-[0.8125rem] text-text-secondary">Create a recurring fee for this client</span>
            </div>
          </label>
          {#if isRecurring}
            <div class="mt-4 pt-4 border-t border-border-light max-w-[160px]">
              <select class="w-full px-3 py-2 border border-border rounded-md text-sm" bind:value={recurringFrequency}>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
              </select>
            </div>
          {/if}
        </div>

        {#if partners.length >= 2}
          <div class="mb-4 px-5 py-5 bg-bg rounded-xl">
            <h3 class="text-[0.9375rem] font-semibold m-0 mb-4 text-text">Revenue Split</h3>
            <div class="flex flex-col sm:flex-row items-center gap-6">
              <div class="flex flex-col items-center min-w-[80px]">
                <span class="text-xs text-text-secondary">{partners[0].name}</span>
                <span class="text-xl font-bold">{partner_a_share}%</span>
              </div>
              <div class="flex-1 relative w-full sm:w-auto">
                <input
                  type="range"
                  class="w-full h-1.5 opacity-0 relative z-10 cursor-pointer"
                  min="0"
                  max="100"
                  value={partner_a_share}
                  oninput={(e) => updateShareA(e.target.value)}
                />
                <div class="absolute top-1/2 left-0 right-0 h-1.5 bg-border rounded-sm -translate-y-1/2">
                  <div class="h-full bg-primary rounded-sm transition-all duration-100" style="width: {partner_a_share}%"></div>
                </div>
              </div>
              <div class="flex flex-col items-center min-w-[80px]">
                <span class="text-xs text-text-secondary">{partners[1].name}</span>
                <span class="text-xl font-bold">{partner_b_share}%</span>
              </div>
            </div>
          </div>
        {/if}

        <div class="flex flex-col sm:flex-row justify-end gap-3 pt-6 border-t border-border-light mt-2">
          <button type="button" class="btn-cancel w-full sm:w-auto" onclick={cancelForm}>Cancel</button>
          <button type="submit" class="px-6 py-2.5 bg-primary text-white border-none rounded-lg text-[0.9375rem] font-semibold cursor-pointer transition-all duration-200 hover:bg-primary-hover hover:-translate-y-px w-full sm:w-auto">
            {editing !== null ? "Update Invoice" : "Create Invoice"}
          </button>
        </div>
      </form>
    </div>
  {/if}

  {#if invoiceUrl}
    <a href={invoiceUrl} target="_blank" class="flex items-center justify-center gap-2.5 px-4 py-4 mb-6 bg-gradient-to-br from-[#059669] to-[#10b981] text-white rounded-xl font-semibold no-underline transition-all duration-200 hover:-translate-y-0.5 hover:text-white animate-pulse-shadow">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
      Download PDF
    </a>
  {/if}

  <div class="card overflow-hidden">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center px-6 py-5 border-b border-border-light gap-4">
      <h2 class="text-lg font-semibold m-0">All Invoices</h2>
      <div class="flex gap-1.5 w-full sm:w-auto overflow-x-auto">
        <button class="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-[0.8125rem] font-medium cursor-pointer border-none transition-all duration-200 {statusFilter === '' ? 'bg-primary text-white' : 'bg-bg text-text-secondary hover:bg-border-light'}" onclick={() => statusFilter = ""}>
          All
          <span class="px-1.5 py-0.5 rounded text-[0.6875rem] {statusFilter === '' ? 'bg-white/20' : 'bg-surface'}">{invoices.length}</span>
        </button>
        <button class="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-[0.8125rem] font-medium cursor-pointer border-none transition-all duration-200 {statusFilter === 'draft' ? 'bg-primary text-white' : 'bg-bg text-text-secondary hover:bg-border-light'}" onclick={() => statusFilter = "draft"}>
          Draft
          <span class="px-1.5 py-0.5 rounded text-[0.6875rem] {statusFilter === 'draft' ? 'bg-white/20' : 'bg-surface'}">{stats.draft}</span>
        </button>
        <button class="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-[0.8125rem] font-medium cursor-pointer border-none transition-all duration-200 {statusFilter === 'sent' ? 'bg-primary text-white' : 'bg-bg text-text-secondary hover:bg-border-light'}" onclick={() => statusFilter = "sent"}>
          Sent
          <span class="px-1.5 py-0.5 rounded text-[0.6875rem] {statusFilter === 'sent' ? 'bg-white/20' : 'bg-surface'}">{stats.sent}</span>
        </button>
        <button class="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-[0.8125rem] font-medium cursor-pointer border-none transition-all duration-200 {statusFilter === 'paid' ? 'bg-primary text-white' : 'bg-bg text-text-secondary hover:bg-border-light'}" onclick={() => statusFilter = "paid"}>
          Paid
          <span class="px-1.5 py-0.5 rounded text-[0.6875rem] {statusFilter === 'paid' ? 'bg-white/20' : 'bg-surface'}">{stats.paid}</span>
        </button>
      </div>
    </div>

    {#if filteredInvoices.length > 0}
      <div class="p-4 flex flex-col gap-3">
        {#each filteredInvoices as inv, i}
          <div class="bg-bg rounded-xl px-5 py-4 transition-all duration-200 hover:shadow-md hover:-translate-y-px animate-fade-in" style="animation-delay: {i * 40}ms">
            <div class="flex flex-col sm:flex-row justify-between items-start mb-3 gap-3">
              <div class="flex-1 min-w-0">
                <span class="font-mono text-[0.6875rem] text-text-muted uppercase tracking-wide">#{inv.invoice_number || inv.id}</span>
                <h4 class="text-base font-semibold my-1 whitespace-nowrap overflow-hidden text-ellipsis">{inv.title || `Invoice #${inv.invoice_number || inv.id}`}</h4>
                {#if inv.description}
                  <p class="text-[0.8125rem] text-text-secondary m-0 mb-2 whitespace-nowrap overflow-hidden text-ellipsis max-w-[400px]">{inv.description}</p>
                {/if}
                <div class="flex items-center gap-2 text-[0.8125rem] text-text-secondary">
                  <span>{getClientName(inv.client_id)}</span>
                  <span class="w-0.5 h-0.5 bg-text-muted rounded-full"></span>
                  <span>{formatDate(inv.created_at)}</span>
                </div>
              </div>
              <div class="flex sm:flex-col flex-row items-end sm:items-end gap-2 sm:gap-2 w-full sm:w-auto justify-between sm:justify-start text-right">
                <span class="text-xl font-bold tracking-tight">{formatCurrency(inv.total_amount)}</span>
                <span class="inline-block px-3 py-1 rounded-full text-[0.6875rem] font-semibold uppercase tracking-wide {(!inv.status || inv.status === 'draft') ? 'bg-bg text-text-secondary border border-border' : inv.status === 'sent' ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'}">{inv.status || 'draft'}</span>
              </div>
            </div>
            <div class="flex flex-wrap items-center gap-2 pt-3 border-t border-border-light">
              {#if inv.status === "draft" || !inv.status}
                <button class="flex items-center gap-1.5 px-2.5 py-1.5 bg-amber-50 text-amber-700 border-none rounded-md text-[0.8125rem] font-medium cursor-pointer transition-all duration-150 hover:bg-amber-100" onclick={() => markAsSent(inv)}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="22" y1="2" x2="11" y2="13"/>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                  </svg>
                  Send
                </button>
              {:else if inv.status === "sent"}
                <button class="flex items-center gap-1.5 px-2.5 py-1.5 bg-emerald-50 text-emerald-700 border-none rounded-md text-[0.8125rem] font-medium cursor-pointer transition-all duration-150 hover:bg-emerald-100" onclick={() => markAsPaid(inv)}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  Mark Paid
                </button>
              {:else if inv.status === "paid"}
                <button class="flex items-center gap-1.5 px-2.5 py-1.5 bg-bg text-text-secondary border-none rounded-md text-[0.8125rem] font-medium cursor-pointer transition-all duration-150 hover:bg-surface" onclick={() => markAsSent(inv)}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="1 4 1 10 7 10"/>
                    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
                  </svg>
                  Revert
                </button>
              {/if}
              <button class="flex items-center gap-1.5 px-2.5 py-1.5 bg-transparent text-text-secondary border-none rounded-md text-[0.8125rem] font-medium cursor-pointer transition-all duration-150 hover:bg-surface hover:text-text" onclick={() => edit(inv)} title="Edit">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
              <a href={`http://localhost:8000/invoices/${inv.id}/pdf?t=${Date.now()}`} target="_blank" class="flex items-center gap-1.5 px-2.5 py-1.5 bg-transparent text-text-secondary border-none rounded-md text-[0.8125rem] font-medium cursor-pointer transition-all duration-150 hover:bg-surface hover:text-text no-underline" title="Download PDF">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </a>
              <button class="flex items-center gap-1.5 px-2.5 py-1.5 bg-transparent text-text-secondary border-none rounded-md text-[0.8125rem] font-medium cursor-pointer transition-all duration-150 hover:bg-red-50 hover:text-red-500" onclick={() => remove(inv.id)} title="Delete">
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
      <div class="flex flex-col items-center justify-center py-16 px-8 text-center">
        <div class="w-24 h-24 rounded-full bg-bg flex items-center justify-center mb-6">
          <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" class="text-text-muted opacity-40">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
        </div>
        <p class="text-text-secondary m-0 mb-6 text-base">No invoices found</p>
        <button class="px-6 py-2.5 bg-primary text-white border-none rounded-lg text-[0.9375rem] font-semibold cursor-pointer transition-all duration-200 hover:bg-primary-hover hover:-translate-y-px" onclick={() => showForm = true}>Create your first invoice</button>
      </div>
    {/if}
  </div>
</div>
