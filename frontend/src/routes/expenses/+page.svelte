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
    { value: "hosting", label: "Hosting" },
    { value: "domain", label: "Domains" },
    { value: "tools", label: "Tools & Software" },
    { value: "equipment", label: "Equipment" },
    { value: "office", label: "Office" },
    { value: "travel", label: "Travel" },
    { value: "other", label: "Other" }
  ];

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
    return new Date(dateStr).toLocaleDateString('de-CH');
  }

  function updateSplitA(value) {
    form.split_ratio_a = parseFloat(value);
    form.split_ratio_b = 100 - parseFloat(value);
  }
</script>

<div class="page-header">
  <div>
    <h1>Expenses</h1>
    <p class="subtitle">Track business expenses and reimbursements</p>
  </div>
  <button class="btn-primary" onclick={openAddForm}>
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <line x1="12" y1="5" x2="12" y2="19"/>
      <line x1="5" y1="12" x2="19" y2="12"/>
    </svg>
    Add Expense
  </button>
</div>

{#if balance && balance.balance > 0}
  <div class="balance-banner">
    <div class="balance-info">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <span><strong>{balance.owes_from}</strong> owes <strong>{balance.owes_to}</strong></span>
    </div>
    <div class="balance-actions">
      <span class="balance-amount">{formatCurrency(balance.balance)}</span>
      <button class="btn-settle" onclick={() => showSettleModal = true}>Settle</button>
    </div>
  </div>
{/if}

<div class="card filter-bar">
  <div class="filter-row">
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
    <select bind:value={filters.status} onchange={applyFilters}>
      <option value="">All Status</option>
      <option value="pending">Pending</option>
      <option value="settled">Settled</option>
    </select>
  </div>
</div>

{#if showForm}
  <div class="modal-overlay" onclick={() => showForm = false}>
    <div class="modal" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <h3>{editingId ? "Edit Expense" : "Add Expense"}</h3>
        <button class="btn-close" onclick={() => showForm = false}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <form onsubmit={(e) => { e.preventDefault(); submitForm(); }}>
        <div class="form-grid">
          <div class="form-group">
            <label>Date</label>
            <input type="date" bind:value={form.date} required />
          </div>
          <div class="form-group">
            <label>Amount (CHF)</label>
            <input type="number" step="0.01" bind:value={form.amount} placeholder="0.00" required />
          </div>
        </div>

        <div class="form-group">
          <label>Description</label>
          <input type="text" bind:value={form.description} placeholder="What was this expense for?" required />
        </div>

        <div class="form-grid">
          <div class="form-group">
            <label>Category</label>
            <select bind:value={form.category}>
              {#each categories as cat}
                <option value={cat.value}>{cat.label}</option>
              {/each}
            </select>
          </div>
          <div class="form-group">
            <label>Type</label>
            <select bind:value={form.expense_type}>
              <option value="business">Business (shared)</option>
              <option value="reimbursable">Reimbursable</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>Paid By</label>
          <select bind:value={form.paid_by}>
            {#each partners as partner}
              <option value={partner.id}>{partner.name}</option>
            {/each}
          </select>
        </div>

        <div class="split-section">
          <label>Split Ratio</label>
          <div class="split-row">
            <div class="split-partner">
              <span class="split-name">{partners[0]?.name || "A"}</span>
              <span class="split-percent">{form.split_ratio_a}%</span>
            </div>
            <input type="range" min="0" max="100" value={form.split_ratio_a} oninput={(e) => updateSplitA(e.target.value)} />
            <div class="split-partner">
              <span class="split-name">{partners[1]?.name || "B"}</span>
              <span class="split-percent">{form.split_ratio_b}%</span>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>Notes (optional)</label>
          <textarea bind:value={form.notes} placeholder="Additional notes..."></textarea>
        </div>

        <div class="form-actions">
          <button type="button" class="btn-secondary" onclick={() => showForm = false}>Cancel</button>
          <button type="submit" class="btn-primary">{editingId ? "Update" : "Add"} Expense</button>
        </div>
      </form>
    </div>
  </div>
{/if}

{#if showSettleModal}
  <div class="modal-overlay" onclick={() => showSettleModal = false}>
    <div class="modal settle-modal" onclick={(e) => e.stopPropagation()}>
      <h3>Settle Balance</h3>
      <p>
        Confirm that <strong>{balance.owes_from}</strong> has paid <strong>{balance.owes_to}</strong> the amount of <strong>{formatCurrency(balance.balance)}</strong>.
      </p>
      <p class="settle-note">This will mark all pending expenses as settled.</p>
      <div class="form-actions">
        <button class="btn-secondary" onclick={() => showSettleModal = false}>Cancel</button>
        <button class="btn-primary" onclick={settleBalance}>Confirm Settlement</button>
      </div>
    </div>
  </div>
{/if}

<div class="expenses-list">
  {#if expenses.length === 0}
    <div class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <line x1="12" y1="1" x2="12" y2="23"/>
        <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
      </svg>
      <p>No expenses found</p>
      <button class="btn-primary" onclick={openAddForm}>Add your first expense</button>
    </div>
  {:else}
    {#each expenses as expense}
      <div class="expense-card" class:settled={expense.status === "settled"}>
        <div class="expense-main">
          <div class="expense-meta">
            <span class="expense-date">{formatDate(expense.date)}</span>
            <span class="expense-category">{categories.find(c => c.value === expense.category)?.label || expense.category}</span>
            <span class="expense-type">{expense.expense_type}</span>
            {#if expense.status === "settled"}
              <span class="expense-settled">Settled</span>
            {/if}
          </div>
          <p class="expense-desc">{expense.description}</p>
          <div class="expense-payer">
            Paid by <strong>{expense.paid_by_name}</strong> · Split {expense.split_ratio_a}/{expense.split_ratio_b}
          </div>
        </div>
        <div class="expense-right">
          <span class="expense-amount">{formatCurrency(expense.amount)}</span>
          <div class="expense-actions">
            <button class="btn-icon" onclick={() => openEditForm(expense)} title="Edit">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button class="btn-icon danger" onclick={() => remove(expense.id)} title="Delete">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
  <div class="card settlements-card">
    <div class="card-header">
      <h3>Settlement History</h3>
    </div>
    <div class="settlements-list">
      {#each settlements as s}
        <div class="settlement-row">
          <span class="settlement-date">{formatDate(s.date)}</span>
          <span class="settlement-parties">{s.from_partner_name} paid {s.to_partner_name}</span>
          <span class="settlement-amount">{formatCurrency(s.amount)}</span>
        </div>
      {/each}
    </div>
  </div>
{/if}

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

  .balance-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    background: var(--color-warning-light);
    border-radius: var(--radius-lg);
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .balance-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: #92400e;
  }

  .balance-actions {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .balance-amount {
    font-size: 1.25rem;
    font-weight: 700;
    color: #92400e;
  }

  .btn-settle {
    padding: 0.5rem 1rem;
    border-radius: var(--radius-md);
    border: none;
    font-weight: 500;
    background: #92400e;
    color: white;
    cursor: pointer;
  }

  .btn-settle:hover {
    background: #78350f;
  }

  .card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
  }

  .filter-bar {
    padding: 1rem 1.25rem;
    margin-bottom: 1.5rem;
  }

  .filter-row {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .filter-row select {
    min-width: 140px;
  }

  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 1rem;
  }

  .modal {
    background: var(--color-surface);
    border-radius: var(--radius-xl);
    padding: 0;
    max-width: 480px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .modal-header h3 {
    margin: 0;
  }

  .btn-close {
    background: transparent;
    color: var(--color-text-muted);
    padding: 0.375rem;
    border-radius: var(--radius-sm);
  }

  .btn-close:hover {
    background: var(--color-bg);
    color: var(--color-text);
  }

  .modal form {
    padding: 1.5rem;
  }

  .settle-modal {
    max-width: 400px;
    padding: 1.5rem;
  }

  .settle-modal h3 {
    margin: 0 0 1rem 0;
  }

  .settle-note {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    margin-top: 0.5rem;
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

  .form-group textarea {
    min-height: 80px;
    resize: vertical;
  }

  .split-section {
    margin: 1.5rem 0;
    padding: 1rem;
    background: var(--color-bg);
    border-radius: var(--radius-md);
  }

  .split-section label {
    display: block;
    margin-bottom: 0.75rem;
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--color-text-secondary);
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
    min-width: 70px;
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
  }

  .expenses-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .expense-card {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 1rem 1.25rem;
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    gap: 1rem;
  }

  .expense-card.settled {
    opacity: 0.7;
  }

  .expense-main {
    flex: 1;
  }

  .expense-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    align-items: center;
  }

  .expense-date {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .expense-category {
    font-size: 0.75rem;
    font-weight: 500;
    padding: 0.125rem 0.5rem;
    background: var(--color-border-light);
    border-radius: var(--radius-sm);
  }

  .expense-type {
    font-size: 0.75rem;
    font-weight: 500;
    padding: 0.125rem 0.5rem;
    background: var(--color-primary-light);
    color: var(--color-primary);
    border-radius: var(--radius-sm);
    text-transform: capitalize;
  }

  .expense-settled {
    font-size: 0.75rem;
    font-weight: 500;
    padding: 0.125rem 0.5rem;
    background: var(--color-success-light);
    color: #065f46;
    border-radius: var(--radius-sm);
  }

  .expense-desc {
    margin: 0 0 0.375rem 0;
    font-weight: 500;
  }

  .expense-payer {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .expense-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.5rem;
  }

  .expense-amount {
    font-size: 1.125rem;
    font-weight: 600;
  }

  .expense-actions {
    display: flex;
    gap: 0.25rem;
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

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    color: var(--color-text-muted);
    background: var(--color-surface);
    border-radius: var(--radius-lg);
  }

  .empty-state svg {
    margin-bottom: 1rem;
    opacity: 0.4;
  }

  .empty-state p {
    margin-bottom: 1rem;
  }

  .settlements-card {
    margin-top: 2rem;
  }

  .card-header {
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .card-header h3 {
    margin: 0;
    font-size: 1rem;
  }

  .settlements-list {
    padding: 0.5rem 0;
  }

  .settlement-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1.25rem;
  }

  .settlement-row:not(:last-child) {
    border-bottom: 1px solid var(--color-border-light);
  }

  .settlement-date {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
    min-width: 80px;
  }

  .settlement-parties {
    flex: 1;
    font-size: 0.9375rem;
  }

  .settlement-amount {
    font-weight: 600;
    color: var(--color-success);
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

    .form-grid {
      grid-template-columns: 1fr;
    }

    .expense-card {
      flex-direction: column;
    }

    .expense-right {
      flex-direction: row;
      width: 100%;
      justify-content: space-between;
    }

    .form-actions {
      flex-direction: column;
    }

    .form-actions button {
      width: 100%;
    }
  }
</style>
