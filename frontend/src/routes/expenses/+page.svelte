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

<div class="expenses-page">
  <header class="page-header">
    <div class="header-content">
      <h1>Expenses</h1>
      <p class="subtitle">Track and split business expenses</p>
    </div>
    <button class="btn-add" onclick={openAddForm}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="12" y1="5" x2="12" y2="19"/>
        <line x1="5" y1="12" x2="19" y2="12"/>
      </svg>
      Add Expense
    </button>
  </header>

  <div class="stats-row">
    <div class="stat-card">
      <span class="stat-value">{formatCurrency(stats.totalAmount)}</span>
      <span class="stat-label">Total Expenses</span>
    </div>
    <div class="stat-card">
      <span class="stat-value">{stats.total}</span>
      <span class="stat-label">Transactions</span>
    </div>
    <div class="stat-card pending">
      <span class="stat-value">{stats.pending}</span>
      <span class="stat-label">Pending</span>
    </div>
    <div class="stat-card success">
      <span class="stat-value">{stats.settled}</span>
      <span class="stat-label">Settled</span>
    </div>
  </div>

  {#if balance && balance.balance > 0}
    <div class="balance-card">
      <div class="balance-visual">
        <div class="balance-avatar from">{balance.owes_from?.charAt(0)}</div>
        <div class="balance-arrow">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </div>
        <div class="balance-avatar to">{balance.owes_to?.charAt(0)}</div>
      </div>
      <div class="balance-content">
        <p class="balance-text">
          <strong>{balance.owes_from}</strong> owes <strong>{balance.owes_to}</strong>
        </p>
        <span class="balance-amount">{formatCurrency(balance.balance)}</span>
      </div>
      <button class="btn-settle" onclick={() => showSettleModal = true}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        Settle Up
      </button>
    </div>
  {/if}

  <div class="filter-section">
    <div class="filter-pills">
      <button class:active={!filters.status} onclick={() => { filters.status = ""; applyFilters(); }}>
        All
      </button>
      <button class:active={filters.status === "pending"} onclick={() => { filters.status = "pending"; applyFilters(); }}>
        Pending
      </button>
      <button class:active={filters.status === "settled"} onclick={() => { filters.status = "settled"; applyFilters(); }}>
        Settled
      </button>
    </div>
    <div class="filter-dropdowns">
      <select bind:value={filters.category} onchange={applyFilters}>
        <option value="">All Categories</option>
        {#each categories as cat}
          <option value={cat.value}>{cat.label}</option>
        {/each}
      </select>
      <select bind:value={filters.expense_type} onchange={applyFilters}>
        <option value="">All Types</option>
        <option value="business">Business</option>
        <option value="reimbursable">Reimbursable</option>
      </select>
    </div>
  </div>

  <div class="expenses-list">
    {#if expenses.length === 0}
      <div class="empty-state">
        <div class="empty-icon">
          <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
            <line x1="12" y1="1" x2="12" y2="23"/>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
          </svg>
        </div>
        <p>No expenses found</p>
        <button class="btn-add" onclick={openAddForm}>Add your first expense</button>
      </div>
    {:else}
      {#each expenses as expense, i}
        <div class="expense-card" class:settled={expense.status === "settled"} style="animation-delay: {i * 40}ms">
          <div class="expense-category-indicator" style="background: {getCategoryColor(expense.category)}"></div>
          <div class="expense-content">
            <div class="expense-header">
              <div class="expense-badges">
                <span class="badge category" style="--badge-color: {getCategoryColor(expense.category)}">
                  {categories.find(c => c.value === expense.category)?.label || expense.category}
                </span>
                <span class="badge type">{expense.expense_type}</span>
                {#if expense.status === "settled"}
                  <span class="badge settled">Settled</span>
                {/if}
              </div>
              <span class="expense-date">{formatDate(expense.date)}</span>
            </div>
            <p class="expense-desc">{expense.description}</p>
            <div class="expense-footer">
              <span class="expense-payer">
                Paid by <strong>{expense.paid_by_name}</strong>
              </span>
              <span class="expense-split">{expense.split_ratio_a}/{expense.split_ratio_b}</span>
            </div>
          </div>
          <div class="expense-right">
            <span class="expense-amount">{formatCurrency(expense.amount)}</span>
            <div class="expense-actions">
              <button class="action-btn" onclick={() => openEditForm(expense)} title="Edit">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
              <button class="action-btn danger" onclick={() => remove(expense.id)} title="Delete">
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
    <div class="settlements-section">
      <h3>Settlement History</h3>
      <div class="settlements-list">
        {#each settlements as s, i}
          <div class="settlement-row" style="animation-delay: {i * 30}ms">
            <div class="settlement-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
            <div class="settlement-info">
              <span class="settlement-parties">{s.from_partner_name} paid {s.to_partner_name}</span>
              <span class="settlement-date">{formatDate(s.date)}</span>
            </div>
            <span class="settlement-amount">{formatCurrency(s.amount)}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

{#if showForm}
  <div class="modal-overlay" onclick={() => showForm = false}>
    <div class="modal" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <div>
          <span class="modal-badge">{editingId ? "Edit" : "New"}</span>
          <h3>{editingId ? "Edit Expense" : "Add Expense"}</h3>
        </div>
        <button class="btn-close" onclick={() => showForm = false}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <form onsubmit={(e) => { e.preventDefault(); submitForm(); }}>
        <div class="form-row">
          <div class="form-field">
            <label>Date</label>
            <input type="date" bind:value={form.date} required />
          </div>
          <div class="form-field">
            <label>Amount (CHF)</label>
            <input type="number" step="0.01" bind:value={form.amount} placeholder="0.00" required />
          </div>
        </div>

        <div class="form-field">
          <label>Description</label>
          <input type="text" bind:value={form.description} placeholder="What was this expense for?" required />
        </div>

        <div class="form-row">
          <div class="form-field">
            <label>Category</label>
            <select bind:value={form.category}>
              {#each categories as cat}
                <option value={cat.value}>{cat.label}</option>
              {/each}
            </select>
          </div>
          <div class="form-field">
            <label>Type</label>
            <select bind:value={form.expense_type}>
              <option value="business">Business (shared)</option>
              <option value="reimbursable">Reimbursable</option>
            </select>
          </div>
        </div>

        <div class="form-field">
          <label>Paid By</label>
          <div class="partner-select">
            {#each partners as partner}
              <button
                type="button"
                class="partner-option"
                class:active={form.paid_by === partner.id}
                onclick={() => form.paid_by = partner.id}
              >
                <span class="partner-avatar">{partner.name.charAt(0)}</span>
                <span>{partner.name}</span>
              </button>
            {/each}
          </div>
        </div>

        <div class="split-section">
          <label>Split Ratio</label>
          <div class="split-control">
            <div class="split-partner">
              <span class="partner-name">{partners[0]?.name || "A"}</span>
              <span class="partner-share">{form.split_ratio_a}%</span>
            </div>
            <div class="split-slider">
              <input type="range" min="0" max="100" value={form.split_ratio_a} oninput={(e) => updateSplitA(e.target.value)} />
              <div class="slider-track">
                <div class="slider-fill" style="width: {form.split_ratio_a}%"></div>
              </div>
            </div>
            <div class="split-partner">
              <span class="partner-name">{partners[1]?.name || "B"}</span>
              <span class="partner-share">{form.split_ratio_b}%</span>
            </div>
          </div>
        </div>

        <div class="form-field">
          <label>Notes (optional)</label>
          <textarea bind:value={form.notes} placeholder="Additional notes..."></textarea>
        </div>

        <div class="form-actions">
          <button type="button" class="btn-cancel" onclick={() => showForm = false}>Cancel</button>
          <button type="submit" class="btn-submit">{editingId ? "Update" : "Add"} Expense</button>
        </div>
      </form>
    </div>
  </div>
{/if}

{#if showSettleModal}
  <div class="modal-overlay" onclick={() => showSettleModal = false}>
    <div class="modal settle-modal" onclick={(e) => e.stopPropagation()}>
      <div class="settle-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
      </div>
      <h3>Settle Balance</h3>
      <p class="settle-desc">
        Confirm that <strong>{balance?.owes_from}</strong> has paid <strong>{balance?.owes_to}</strong>
      </p>
      <div class="settle-amount">{formatCurrency(balance?.balance)}</div>
      <p class="settle-note">This will mark all pending expenses as settled.</p>
      <div class="form-actions">
        <button class="btn-cancel" onclick={() => showSettleModal = false}>Cancel</button>
        <button class="btn-submit" onclick={settleBalance}>Confirm Settlement</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .expenses-page {
    max-width: 1000px;
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

  .btn-add {
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

  .btn-add:hover {
    background: var(--color-primary-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .stat-card {
    background: var(--color-surface);
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }

  .stat-card.pending { background: rgba(245, 158, 11, 0.08); }
  .stat-card.success { background: rgba(16, 185, 129, 0.08); }

  .stat-value {
    display: block;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--color-text);
    margin-bottom: 0.25rem;
  }

  .stat-card.pending .stat-value { color: #d97706; }
  .stat-card.success .stat-value { color: #059669; }

  .stat-label {
    font-size: 0.75rem;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 500;
  }

  .balance-card {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 1.25rem 1.5rem;
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border-radius: 14px;
    margin-bottom: 1.5rem;
  }

  .balance-visual {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .balance-avatar {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1rem;
    color: white;
  }

  .balance-avatar.from { background: #f59e0b; }
  .balance-avatar.to { background: #059669; }

  .balance-arrow {
    color: #92400e;
    opacity: 0.5;
  }

  .balance-content {
    flex: 1;
  }

  .balance-text {
    margin: 0 0 0.25rem;
    color: #78350f;
    font-size: 0.9375rem;
  }

  .balance-amount {
    font-size: 1.5rem;
    font-weight: 700;
    color: #92400e;
  }

  .btn-settle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    background: #92400e;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-settle:hover {
    background: #78350f;
    transform: translateY(-1px);
  }

  .filter-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
  }

  .filter-pills {
    display: flex;
    gap: 0.375rem;
    background: var(--color-surface);
    padding: 0.375rem;
    border-radius: 10px;
  }

  .filter-pills button {
    padding: 0.5rem 1rem;
    background: transparent;
    color: var(--color-text-secondary);
    border: none;
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .filter-pills button:hover {
    color: var(--color-text);
  }

  .filter-pills button.active {
    background: var(--color-primary);
    color: white;
  }

  .filter-dropdowns {
    display: flex;
    gap: 0.75rem;
  }

  .filter-dropdowns select {
    padding: 0.5rem 0.875rem;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    font-size: 0.875rem;
    background: var(--color-surface);
    cursor: pointer;
  }

  .expenses-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .expense-card {
    display: flex;
    background: var(--color-surface);
    border-radius: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    overflow: hidden;
    transition: all 0.2s ease;
    animation: fadeIn 0.4s ease backwards;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .expense-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    transform: translateY(-1px);
  }

  .expense-card.settled {
    opacity: 0.6;
  }

  .expense-category-indicator {
    width: 4px;
    flex-shrink: 0;
  }

  .expense-content {
    flex: 1;
    padding: 1rem 1.25rem;
    min-width: 0;
  }

  .expense-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }

  .expense-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 0.375rem;
  }

  .badge {
    padding: 0.25rem 0.625rem;
    border-radius: 6px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .badge.category {
    background: color-mix(in srgb, var(--badge-color) 15%, transparent);
    color: var(--badge-color);
  }

  .badge.type {
    background: var(--color-primary-light);
    color: var(--color-primary);
  }

  .badge.settled {
    background: rgba(16, 185, 129, 0.1);
    color: #059669;
  }

  .expense-date {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }

  .expense-desc {
    margin: 0 0 0.5rem;
    font-weight: 600;
    font-size: 1rem;
    color: var(--color-text);
  }

  .expense-footer {
    display: flex;
    align-items: center;
    gap: 1rem;
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .expense-split {
    padding: 0.125rem 0.5rem;
    background: var(--color-bg);
    border-radius: 4px;
    font-family: ui-monospace, monospace;
    font-size: 0.75rem;
  }

  .expense-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    background: var(--color-bg);
  }

  .expense-amount {
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: -0.02em;
  }

  .expense-actions {
    display: flex;
    gap: 0.25rem;
  }

  .action-btn {
    padding: 0.375rem;
    background: transparent;
    border: none;
    border-radius: 6px;
    color: var(--color-text-muted);
    cursor: pointer;
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
    background: var(--color-surface);
    border-radius: 16px;
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

  .settlements-section {
    margin-top: 2rem;
    background: var(--color-surface);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }

  .settlements-section h3 {
    padding: 1.25rem 1.5rem;
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    border-bottom: 1px solid var(--color-border-light);
  }

  .settlements-list {
    padding: 0.5rem 0;
  }

  .settlement-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.875rem 1.5rem;
    animation: fadeIn 0.4s ease backwards;
  }

  .settlement-row:not(:last-child) {
    border-bottom: 1px solid var(--color-border-light);
  }

  .settlement-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: rgba(16, 185, 129, 0.1);
    color: #059669;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .settlement-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .settlement-parties {
    font-weight: 500;
  }

  .settlement-date {
    font-size: 0.75rem;
    color: var(--color-text-secondary);
  }

  .settlement-amount {
    font-weight: 700;
    color: #059669;
    font-size: 1rem;
  }

  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 1rem;
    animation: fadeIn 0.2s ease;
  }

  .modal {
    background: var(--color-surface);
    border-radius: 20px;
    max-width: 500px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
    animation: slideUp 0.3s ease;
  }

  @keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 1.5rem 1.5rem 1rem;
  }

  .modal-badge {
    display: inline-block;
    background: var(--color-primary);
    color: white;
    font-size: 0.6875rem;
    font-weight: 600;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.375rem;
  }

  .modal-header h3 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
  }

  .btn-close {
    padding: 0.375rem;
    background: transparent;
    border: none;
    color: var(--color-text-muted);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-close:hover {
    background: var(--color-bg);
    color: var(--color-text);
  }

  .modal form {
    padding: 0 1.5rem 1.5rem;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .form-field {
    margin-bottom: 1rem;
  }

  .form-field label {
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.375rem;
  }

  .form-field input,
  .form-field select,
  .form-field textarea {
    width: 100%;
    padding: 0.625rem 0.875rem;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    font-size: 0.9375rem;
    background: white;
    transition: all 0.2s ease;
  }

  .form-field input:focus,
  .form-field select:focus,
  .form-field textarea:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .form-field textarea {
    min-height: 80px;
    resize: vertical;
  }

  .partner-select {
    display: flex;
    gap: 0.75rem;
  }

  .partner-option {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.625rem;
    padding: 0.75rem;
    background: var(--color-bg);
    border: 2px solid transparent;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .partner-option:hover {
    background: var(--color-border-light);
  }

  .partner-option.active {
    border-color: var(--color-primary);
    background: var(--color-primary-light);
  }

  .partner-avatar {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: var(--color-primary);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.875rem;
  }

  .split-section {
    margin: 1.5rem 0;
    padding: 1.25rem;
    background: var(--color-bg);
    border-radius: 12px;
  }

  .split-section > label {
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 1rem;
  }

  .split-control {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .split-partner {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 70px;
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
    padding-top: 1rem;
    border-top: 1px solid var(--color-border-light);
    margin-top: 1rem;
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

  .settle-modal {
    max-width: 400px;
    padding: 2rem;
    text-align: center;
  }

  .settle-icon {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: rgba(16, 185, 129, 0.1);
    color: #059669;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1.5rem;
  }

  .settle-modal h3 {
    margin: 0 0 0.75rem;
    font-size: 1.25rem;
    font-weight: 700;
  }

  .settle-desc {
    color: var(--color-text-secondary);
    margin: 0 0 1rem;
  }

  .settle-amount {
    font-size: 2rem;
    font-weight: 700;
    color: #059669;
    margin-bottom: 1rem;
  }

  .settle-note {
    font-size: 0.8125rem;
    color: var(--color-text-muted);
    margin-bottom: 1.5rem;
  }

  .settle-modal .form-actions {
    justify-content: center;
    border-top: none;
    padding-top: 0;
    margin-top: 0;
  }

  @media (max-width: 768px) {
    .stats-row {
      grid-template-columns: repeat(2, 1fr);
    }

    .balance-card {
      flex-direction: column;
      text-align: center;
    }

    .balance-visual {
      justify-content: center;
    }

    .filter-section {
      flex-direction: column;
      align-items: stretch;
    }

    .filter-pills {
      justify-content: center;
    }

    .filter-dropdowns {
      justify-content: center;
    }

    .expense-card {
      flex-direction: column;
    }

    .expense-category-indicator {
      width: 100%;
      height: 4px;
    }

    .expense-right {
      flex-direction: row;
      justify-content: space-between;
      width: 100%;
    }
  }

  @media (max-width: 640px) {
    .page-header {
      flex-direction: column;
      gap: 1rem;
    }

    .btn-add {
      width: 100%;
      justify-content: center;
    }

    .form-row {
      grid-template-columns: 1fr;
    }

    .partner-select {
      flex-direction: column;
    }

    .form-actions {
      flex-direction: column;
    }

    .form-actions button {
      width: 100%;
    }

    .split-control {
      flex-direction: column;
      gap: 0.75rem;
    }

    .split-slider {
      width: 100%;
    }
  }
</style>
