<script>
  import { onMount } from "svelte";
  import { getExpenses, createExpense, updateExpense, deleteExpense, getExpenseBalance, getPartners, createSettlement, getSettlements } from "$lib/api.js";

  let expenses = [];
  let partners = [];
  let balance = null;
  let settlements = [];

  let showForm = false;
  let editingId = null;
  let form = {
    date: new Date().toISOString().slice(0, 10),
    description: "",
    amount: "",
    currency: "CHF",
    category: "other",
    expense_type: "business",
    paid_by: null,
    split_ratio_a: 50,
    split_ratio_b: 50,
    notes: ""
  };

  let filters = {
    category: "",
    expense_type: "",
    status: ""
  };

  let showSettleModal = false;

  const categories = [
    { value: "hosting", label: "Hosting", icon: "server" },
    { value: "domain", label: "Domains", icon: "globe" },
    { value: "tools", label: "Tools & Software", icon: "tool" },
    { value: "equipment", label: "Equipment", icon: "monitor" },
    { value: "office", label: "Office", icon: "briefcase" },
    { value: "travel", label: "Travel", icon: "plane" },
    { value: "other", label: "Other", icon: "folder" }
  ];

  $: stats = {
    total: expenses.length,
    pending: expenses.filter(e => e.status !== 'settled').length,
    settled: expenses.filter(e => e.status === 'settled').length,
    totalAmount: expenses.reduce((sum, e) => sum + (e.amount || 0), 0),
  };

  async function load() {
    [expenses, partners, balance, settlements] = await Promise.all([
      getExpenses(filters),
      getPartners(),
      getExpenseBalance(),
      getSettlements()
    ]);
    if (partners.length > 0 && !form.paid_by) {
      form.paid_by = partners[0].id;
    }
  }

  onMount(load);

  async function applyFilters() {
    expenses = await getExpenses(filters);
  }

  function openAddForm() {
    editingId = null;
    form = {
      date: new Date().toISOString().slice(0, 10),
      description: "",
      amount: "",
      currency: "CHF",
      category: "other",
      expense_type: "business",
      paid_by: partners[0]?.id || null,
      split_ratio_a: partners[0]?.default_share || 50,
      split_ratio_b: partners[1]?.default_share || 50,
      notes: ""
    };
    showForm = true;
  }

  function openEditForm(expense) {
    editingId = expense.id;
    form = {
      date: expense.date,
      description: expense.description,
      amount: expense.amount,
      currency: expense.currency,
      category: expense.category,
      expense_type: expense.expense_type,
      paid_by: expense.paid_by,
      split_ratio_a: expense.split_ratio_a,
      split_ratio_b: expense.split_ratio_b,
      notes: expense.notes || ""
    };
    showForm = true;
  }

  async function submitForm() {
    const data = {
      ...form,
      amount: parseFloat(form.amount)
    };

    if (editingId) {
      await updateExpense(editingId, data);
    } else {
      await createExpense(data);
    }

    showForm = false;
    load();
  }

  async function remove(id) {
    if (confirm("Delete this expense?")) {
      await deleteExpense(id);
      load();
    }
  }

  async function settleBalance() {
    if (!balance || balance.balance <= 0) return;

    await createSettlement({
      from_partner_id: balance.owes_from_id,
      to_partner_id: balance.owes_to_id,
      amount: balance.balance,
      settle_pending: true
    });

    showSettleModal = false;
    load();
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat('de-CH', { style: 'currency', currency: 'CHF' }).format(amount || 0);
  }

  function formatDate(dateStr) {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleDateString('de-CH', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function updateSplitA(value) {
    form.split_ratio_a = parseFloat(value);
    form.split_ratio_b = 100 - parseFloat(value);
  }

  function getCategoryColor(cat) {
    const colors = {
      hosting: '#6366f1',
      domain: '#8b5cf6',
      tools: '#ec4899',
      equipment: '#f59e0b',
      office: '#10b981',
      travel: '#3b82f6',
      other: '#6b7280'
    };
    return colors[cat] || colors.other;
  }
</script>

<div class="max-w-[1000px] mx-auto">
  <header class="flex justify-between items-start mb-6 max-md:flex-col max-md:gap-4">
    <div>
      <h1 class="text-[1.75rem] font-bold m-0 tracking-[-0.03em]">Expenses</h1>
      <p class="mt-1 mb-0 text-text-secondary text-[0.9375rem]">Track and split business expenses</p>
    </div>
    <button class="flex items-center gap-2 px-5 py-2.5 bg-primary text-white border-none rounded-[10px] text-[0.9375rem] font-semibold cursor-pointer transition-all duration-200 hover:bg-primary-hover hover:-translate-y-px hover:shadow-[0_4px_12px_rgba(59,130,246,0.3)] max-md:w-full max-md:justify-center" onclick={openAddForm}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="12" y1="5" x2="12" y2="19"/>
        <line x1="5" y1="12" x2="19" y2="12"/>
      </svg>
      Add Expense
    </button>
  </header>

  <div class="grid grid-cols-4 gap-4 mb-6 max-md:grid-cols-2">
    <div class="card p-5 text-center shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
      <span class="block text-2xl font-bold text-text mb-1">{formatCurrency(stats.totalAmount)}</span>
      <span class="text-xs text-text-secondary uppercase tracking-[0.05em] font-medium">Total Expenses</span>
    </div>
    <div class="card p-5 text-center shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
      <span class="block text-2xl font-bold text-text mb-1">{stats.total}</span>
      <span class="text-xs text-text-secondary uppercase tracking-[0.05em] font-medium">Transactions</span>
    </div>
    <div class="card p-5 text-center shadow-[0_1px_3px_rgba(0,0,0,0.04)] bg-[rgba(245,158,11,0.08)]">
      <span class="block text-2xl font-bold mb-1 text-[#d97706]">{stats.pending}</span>
      <span class="text-xs text-text-secondary uppercase tracking-[0.05em] font-medium">Pending</span>
    </div>
    <div class="card p-5 text-center shadow-[0_1px_3px_rgba(0,0,0,0.04)] bg-[rgba(16,185,129,0.08)]">
      <span class="block text-2xl font-bold mb-1 text-[#059669]">{stats.settled}</span>
      <span class="text-xs text-text-secondary uppercase tracking-[0.05em] font-medium">Settled</span>
    </div>
  </div>

  {#if balance && balance.balance > 0}
    <div class="flex items-center gap-6 px-6 py-5 bg-gradient-to-br from-[#fef3c7] to-[#fde68a] rounded-[14px] mb-6 max-md:flex-col max-md:text-center">
      <div class="flex items-center gap-2 max-md:justify-center">
        <div class="w-10 h-10 rounded-[10px] flex items-center justify-center font-bold text-base text-white bg-[#f59e0b]">{balance.owes_from?.charAt(0)}</div>
        <div class="text-[#92400e] opacity-50">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </div>
        <div class="w-10 h-10 rounded-[10px] flex items-center justify-center font-bold text-base text-white bg-[#059669]">{balance.owes_to?.charAt(0)}</div>
      </div>
      <div class="flex-1">
        <p class="m-0 mb-1 text-[#78350f] text-[0.9375rem]">
          <strong>{balance.owes_from}</strong> owes <strong>{balance.owes_to}</strong>
        </p>
        <span class="text-2xl font-bold text-[#92400e]">{formatCurrency(balance.balance)}</span>
      </div>
      <button class="flex items-center gap-2 px-5 py-2.5 bg-[#92400e] text-white border-none rounded-lg text-sm font-semibold cursor-pointer transition-all duration-200 hover:bg-[#78350f] hover:-translate-y-px" onclick={() => showSettleModal = true}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        Settle Up
      </button>
    </div>
  {/if}

  <div class="flex justify-between items-center gap-4 mb-6 flex-wrap max-md:flex-col max-md:items-stretch">
    <div class="flex gap-1.5 bg-surface px-1.5 py-1.5 rounded-[10px] max-md:justify-center">
      <button class="px-4 py-2 bg-transparent border-none rounded-lg text-sm font-medium cursor-pointer transition-all duration-200 {!filters.status ? 'bg-primary text-white' : 'text-text-secondary hover:text-text'}" onclick={() => { filters.status = ""; applyFilters(); }}>
        All
      </button>
      <button class="px-4 py-2 bg-transparent border-none rounded-lg text-sm font-medium cursor-pointer transition-all duration-200 {filters.status === 'pending' ? 'bg-primary text-white' : 'text-text-secondary hover:text-text'}" onclick={() => { filters.status = "pending"; applyFilters(); }}>
        Pending
      </button>
      <button class="px-4 py-2 bg-transparent border-none rounded-lg text-sm font-medium cursor-pointer transition-all duration-200 {filters.status === 'settled' ? 'bg-primary text-white' : 'text-text-secondary hover:text-text'}" onclick={() => { filters.status = "settled"; applyFilters(); }}>
        Settled
      </button>
    </div>
    <div class="flex gap-3 max-md:justify-center">
      <select bind:value={filters.category} onchange={applyFilters} class="px-3.5 py-2 border border-border rounded-lg text-sm bg-surface cursor-pointer">
        <option value="">All Categories</option>
        {#each categories as cat}
          <option value={cat.value}>{cat.label}</option>
        {/each}
      </select>
      <select bind:value={filters.expense_type} onchange={applyFilters} class="px-3.5 py-2 border border-border rounded-lg text-sm bg-surface cursor-pointer">
        <option value="">All Types</option>
        <option value="business">Business</option>
        <option value="reimbursable">Reimbursable</option>
      </select>
    </div>
  </div>

  <div class="flex flex-col gap-3">
    {#if expenses.length === 0}
      <div class="flex flex-col items-center justify-center py-16 px-8 bg-surface rounded-2xl text-center">
        <div class="w-[100px] h-[100px] rounded-full bg-bg flex items-center justify-center mb-6">
          <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" class="text-text-muted opacity-40">
            <line x1="12" y1="1" x2="12" y2="23"/>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
          </svg>
        </div>
        <p class="text-text-secondary m-0 mb-6 text-base">No expenses found</p>
        <button class="flex items-center gap-2 px-5 py-2.5 bg-primary text-white border-none rounded-[10px] text-[0.9375rem] font-semibold cursor-pointer transition-all duration-200 hover:bg-primary-hover hover:-translate-y-px hover:shadow-[0_4px_12px_rgba(59,130,246,0.3)]" onclick={openAddForm}>Add your first expense</button>
      </div>
    {:else}
      {#each expenses as expense, i}
        <div class="flex bg-surface rounded-[14px] shadow-[0_1px_3px_rgba(0,0,0,0.04)] overflow-hidden transition-all duration-200 hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)] hover:-translate-y-px animate-fade-in max-md:flex-col {expense.status === 'settled' ? 'opacity-60' : ''}" style="animation-delay: {i * 40}ms">
          <div class="w-1 shrink-0 max-md:w-full max-md:h-1" style="background: {getCategoryColor(expense.category)}"></div>
          <div class="flex-1 px-5 py-4 min-w-0">
            <div class="flex justify-between items-start mb-2">
              <div class="flex flex-wrap gap-1.5">
                <span class="px-2.5 py-1 rounded-md text-[0.6875rem] font-semibold uppercase tracking-[0.03em]" style="background: color-mix(in srgb, {getCategoryColor(expense.category)} 15%, transparent); color: {getCategoryColor(expense.category)}">
                  {categories.find(c => c.value === expense.category)?.label || expense.category}
                </span>
                <span class="px-2.5 py-1 rounded-md text-[0.6875rem] font-semibold uppercase tracking-[0.03em] bg-primary/10 text-primary">{expense.expense_type}</span>
                {#if expense.status === "settled"}
                  <span class="px-2.5 py-1 rounded-md text-[0.6875rem] font-semibold uppercase tracking-[0.03em] bg-[rgba(16,185,129,0.1)] text-[#059669]">Settled</span>
                {/if}
              </div>
              <span class="text-xs text-text-muted">{formatDate(expense.date)}</span>
            </div>
            <p class="m-0 mb-2 font-semibold text-base text-text">{expense.description}</p>
            <div class="flex items-center gap-4 text-[0.8125rem] text-text-secondary">
              <span>
                Paid by <strong>{expense.paid_by_name}</strong>
              </span>
              <span class="py-0.5 px-2 bg-bg rounded text-xs font-mono">{expense.split_ratio_a}/{expense.split_ratio_b}</span>
            </div>
          </div>
          <div class="flex flex-col items-end justify-between px-5 py-4 bg-bg max-md:flex-row max-md:w-full">
            <span class="text-xl font-bold tracking-[-0.02em]">{formatCurrency(expense.amount)}</span>
            <div class="flex gap-1">
              <button class="p-1.5 bg-transparent border-none rounded-md text-text-muted cursor-pointer transition-all duration-150 hover:bg-surface hover:text-text" onclick={() => openEditForm(expense)} title="Edit">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
              <button class="p-1.5 bg-transparent border-none rounded-md text-text-muted cursor-pointer transition-all duration-150 hover:bg-[rgba(239,68,68,0.1)] hover:text-[#ef4444]" onclick={() => remove(expense.id)} title="Delete">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      {/each}
    {/if}
  </div>

  {#if settlements.length > 0}
    <div class="mt-8 bg-surface rounded-2xl overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
      <h3 class="px-6 py-5 m-0 text-base font-semibold border-b border-border-light">Settlement History</h3>
      <div class="py-2">
        {#each settlements as s, i}
          <div class="flex items-center gap-4 px-6 py-3.5 animate-fade-in {i < settlements.length - 1 ? 'border-b border-border-light' : ''}" style="animation-delay: {i * 30}ms">
            <div class="w-8 h-8 rounded-full bg-[rgba(16,185,129,0.1)] text-[#059669] flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
            <div class="flex-1 flex flex-col gap-0.5">
              <span class="font-medium">{s.from_partner_name} paid {s.to_partner_name}</span>
              <span class="text-xs text-text-secondary">{formatDate(s.date)}</span>
            </div>
            <span class="font-bold text-[#059669] text-base">{formatCurrency(s.amount)}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

{#if showForm}
  <div class="modal-backdrop animate-fade-in" onclick={() => showForm = false}>
    <div class="modal max-w-[500px] max-h-[90vh] overflow-y-auto" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <div>
          <span class="inline-block bg-primary text-white text-[0.6875rem] font-semibold px-2 py-1 rounded-md uppercase tracking-[0.05em] mb-1.5">{editingId ? "Edit" : "New"}</span>
          <h3 class="m-0 text-xl font-bold">{editingId ? "Edit Expense" : "Add Expense"}</h3>
        </div>
        <button class="p-1.5 bg-transparent border-none text-text-muted rounded-md cursor-pointer transition-all duration-150 hover:bg-bg hover:text-text" onclick={() => showForm = false}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <form onsubmit={(e) => { e.preventDefault(); submitForm(); }} class="px-6 pb-6">
        <div class="grid grid-cols-2 gap-4 mb-4 max-sm:grid-cols-1">
          <div class="mb-4">
            <label class="form-label">Date</label>
            <input type="date" bind:value={form.date} required class="form-input" />
          </div>
          <div class="mb-4">
            <label class="form-label">Amount (CHF)</label>
            <input type="number" step="0.01" bind:value={form.amount} placeholder="0.00" required class="form-input" />
          </div>
        </div>

        <div class="mb-4">
          <label class="form-label">Description</label>
          <input type="text" bind:value={form.description} placeholder="What was this expense for?" required class="form-input" />
        </div>

        <div class="grid grid-cols-2 gap-4 mb-4 max-sm:grid-cols-1">
          <div class="mb-4">
            <label class="form-label">Category</label>
            <select bind:value={form.category} class="form-input cursor-pointer">
              {#each categories as cat}
                <option value={cat.value}>{cat.label}</option>
              {/each}
            </select>
          </div>
          <div class="mb-4">
            <label class="form-label">Type</label>
            <select bind:value={form.expense_type} class="form-input cursor-pointer">
              <option value="business">Business (shared)</option>
              <option value="reimbursable">Reimbursable</option>
            </select>
          </div>
        </div>

        <div class="mb-4">
          <label class="form-label">Paid By</label>
          <div class="flex gap-3 max-sm:flex-col">
            {#each partners as partner}
              <button
                type="button"
                class="flex-1 flex items-center gap-2.5 px-3 py-3 border-2 rounded-[10px] cursor-pointer transition-all duration-200 {form.paid_by === partner.id ? 'border-primary bg-primary/10' : 'bg-bg border-transparent hover:bg-border-light'}"
                onclick={() => form.paid_by = partner.id}
              >
                <span class="w-8 h-8 rounded-lg bg-primary text-white flex items-center justify-center font-semibold text-sm">{partner.name.charAt(0)}</span>
                <span>{partner.name}</span>
              </button>
            {/each}
          </div>
        </div>

        <div class="my-6 px-5 py-5 bg-bg rounded-xl">
          <label class="form-label mb-4">Split Ratio</label>
          <div class="flex items-center gap-4 max-sm:flex-col max-sm:gap-3">
            <div class="flex flex-col items-center min-w-[70px]">
              <span class="text-xs text-text-secondary">{partners[0]?.name || "A"}</span>
              <span class="text-xl font-bold">{form.split_ratio_a}%</span>
            </div>
            <div class="flex-1 relative max-sm:w-full">
              <input type="range" min="0" max="100" value={form.split_ratio_a} oninput={(e) => updateSplitA(e.target.value)} class="w-full h-1.5 opacity-0 relative z-[2] cursor-pointer" />
              <div class="absolute top-1/2 left-0 right-0 h-1.5 bg-border rounded-full -translate-y-1/2">
                <div class="h-full bg-primary rounded-full transition-[width] duration-100" style="width: {form.split_ratio_a}%"></div>
              </div>
            </div>
            <div class="flex flex-col items-center min-w-[70px]">
              <span class="text-xs text-text-secondary">{partners[1]?.name || "B"}</span>
              <span class="text-xl font-bold">{form.split_ratio_b}%</span>
            </div>
          </div>
        </div>

        <div class="mb-4">
          <label class="form-label">Notes (optional)</label>
          <textarea bind:value={form.notes} placeholder="Additional notes..." class="form-input min-h-[80px] resize-y"></textarea>
        </div>

        <div class="modal-footer max-sm:flex-col">
          <button type="button" class="btn-cancel max-sm:w-full" onclick={() => showForm = false}>Cancel</button>
          <button type="submit" class="px-6 py-2.5 bg-primary text-white border-none rounded-lg text-[0.9375rem] font-semibold cursor-pointer transition-all duration-200 hover:bg-primary-hover hover:-translate-y-px max-sm:w-full">{editingId ? "Update" : "Add"} Expense</button>
        </div>
      </form>
    </div>
  </div>
{/if}

{#if showSettleModal}
  <div class="modal-backdrop animate-fade-in" onclick={() => showSettleModal = false}>
    <div class="modal max-w-[400px] p-8 text-center" onclick={(e) => e.stopPropagation()}>
      <div class="w-16 h-16 rounded-full bg-[rgba(16,185,129,0.1)] text-[#059669] flex items-center justify-center mx-auto mb-6">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
      </div>
      <h3 class="m-0 mb-3 text-xl font-bold">Settle Balance</h3>
      <p class="text-text-secondary m-0 mb-4">
        Confirm that <strong>{balance?.owes_from}</strong> has paid <strong>{balance?.owes_to}</strong>
      </p>
      <div class="text-[2rem] font-bold text-[#059669] mb-4">{formatCurrency(balance?.balance)}</div>
      <p class="text-[0.8125rem] text-text-muted mb-6">This will mark all pending expenses as settled.</p>
      <div class="flex justify-center gap-3 max-sm:flex-col">
        <button class="btn-cancel max-sm:w-full" onclick={() => showSettleModal = false}>Cancel</button>
        <button class="px-6 py-2.5 bg-primary text-white border-none rounded-lg text-[0.9375rem] font-semibold cursor-pointer transition-all duration-200 hover:bg-primary-hover hover:-translate-y-px max-sm:w-full" onclick={settleBalance}>Confirm Settlement</button>
      </div>
    </div>
  </div>
{/if}
