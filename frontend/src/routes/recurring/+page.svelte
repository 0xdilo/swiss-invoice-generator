<script>
  import { onMount } from "svelte";
  import {
    getAllRecurringFees,
    deleteRecurringFee,
    generateInvoiceFromRecurring,
    getRecurringExpenses,
    deleteRecurringExpense,
    generateExpenseFromRecurring,
  } from "$lib/api.js";

  let fees = [];
  let recurringExpenses = [];
  let generatingExpense = null;
  let loading = true;
  let selectedFrequency = "";
  let sortBy = "next_due_date";
  let sortAsc = true;
  let creatingInvoice = null;

  async function load() {
    loading = true;
    [fees, recurringExpenses] = await Promise.all([
      getAllRecurringFees(),
      getRecurringExpenses(),
    ]);
    loading = false;
  }

  async function removeExpense(id) {
    if (confirm("Delete this recurring expense?")) {
      await deleteRecurringExpense(id);
      await load();
    }
  }

  async function generateExpenseNow(id) {
    generatingExpense = id;
    try {
      await generateExpenseFromRecurring(id);
    } catch (e) {
      alert("Failed to generate expense.");
    }
    generatingExpense = null;
    await load();
  }

  onMount(load);

  async function removeFee(feeId) {
    if (confirm("Delete this recurring fee?")) {
      await deleteRecurringFee(feeId);
      await load();
    }
  }

  async function createInvoice(fee) {
    creatingInvoice = fee.id;
    try {
      const result = await generateInvoiceFromRecurring(fee.id);
      window.open(`http://localhost:8000/invoices/${result.invoice_id}/pdf?t=${Date.now()}`, "_blank");
      await load();
    } catch (e) {
      alert("Failed to create invoice.");
    }
    creatingInvoice = null;
  }

  function openInvoice(invoiceId) {
    window.open(`http://localhost:8000/invoices/${invoiceId}/pdf?t=${Date.now()}`, "_blank");
  }

  function formatDate(dateStr) {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString("de-CH", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat("de-CH", {
      style: "currency",
      currency: "CHF",
    }).format(amount || 0);
  }

  function getDaysUntil(dateStr) {
    if (!dateStr) return null;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(dateStr);
    due.setHours(0, 0, 0, 0);
    return Math.ceil((due - today) / (1000 * 60 * 60 * 24));
  }

  function getUrgency(dateStr) {
    const days = getDaysUntil(dateStr);
    if (days === null) return "unknown";
    if (days < 0) return "overdue";
    if (days <= 7) return "critical";
    if (days <= 14) return "warning";
    if (days <= 30) return "soon";
    return "normal";
  }

  function frequencyLabel(freq) {
    if (freq === "monthly") return "Monthly";
    if (freq === "yearly") return "Yearly";
    if (freq === "one-time") return "One-time";
    return freq || "-";
  }

  function toggleSort(col) {
    if (sortBy === col) {
      sortAsc = !sortAsc;
    } else {
      sortBy = col;
      sortAsc = true;
    }
  }

  $: filteredFees = selectedFrequency
    ? fees.filter((f) => f.frequency === selectedFrequency)
    : fees;

  $: sortedFees = [...filteredFees].sort((a, b) => {
    let aVal = a[sortBy];
    let bVal = b[sortBy];
    if (sortBy === "next_due_date" || sortBy === "start_date") {
      aVal = aVal ? new Date(aVal).getTime() : Infinity;
      bVal = bVal ? new Date(bVal).getTime() : Infinity;
    } else if (sortBy === "amount") {
      aVal = parseFloat(aVal) || 0;
      bVal = parseFloat(bVal) || 0;
    } else {
      aVal = (aVal || "").toString().toLowerCase();
      bVal = (bVal || "").toString().toLowerCase();
    }
    if (aVal < bVal) return sortAsc ? -1 : 1;
    if (aVal > bVal) return sortAsc ? 1 : -1;
    return 0;
  });

  $: totalMonthly = fees
    .filter((f) => f.frequency === "monthly")
    .reduce((sum, f) => sum + parseFloat(f.amount || 0), 0);

  $: totalYearly = fees
    .filter((f) => f.frequency === "yearly")
    .reduce((sum, f) => sum + parseFloat(f.amount || 0), 0);

  $: annualizedTotal = totalMonthly * 12 + totalYearly;

  $: dueSoon = fees.filter((f) => {
    const days = getDaysUntil(f.next_due_date);
    return days !== null && days >= 0 && days <= 30;
  }).length;
</script>

<div class="page-header">
  <div>
    <h1>Recurring Payments</h1>
    <p class="subtitle">All recurring fees and their payment schedule</p>
  </div>
</div>

<div class="stats-row">
  <div class="stat-card">
    <span class="stat-value">{fees.length}</span>
    <span class="stat-label">Total Fees</span>
  </div>
  <div class="stat-card">
    <span class="stat-value warning">{dueSoon}</span>
    <span class="stat-label">Due in 30 days</span>
  </div>
  <div class="stat-card">
    <span class="stat-value">{formatCurrency(totalMonthly)}</span>
    <span class="stat-label">Monthly Total</span>
  </div>
  <div class="stat-card primary">
    <span class="stat-value">{formatCurrency(annualizedTotal)}</span>
    <span class="stat-label">Annual Revenue</span>
  </div>
</div>

<div class="card filter-card">
  <div class="filter-row">
    <div class="filter-group">
      <label>Frequency</label>
      <select bind:value={selectedFrequency}>
        <option value="">All</option>
        <option value="monthly">Monthly</option>
        <option value="yearly">Yearly</option>
        <option value="one-time">One-time</option>
      </select>
    </div>
  </div>
</div>

{#if loading}
  <div class="loading">Loading...</div>
{:else if sortedFees.length === 0}
  <div class="empty-state">
    <svg
      width="48"
      height="48"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.5"
    >
      <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <p>No recurring fees found</p>
    <p class="empty-hint">Add recurring fees to clients to track them here</p>
  </div>
{:else}
  <div class="card table-card">
    <table>
      <thead>
        <tr>
          <th class="sortable" onclick={() => toggleSort("client_name")}>
            Client
            {#if sortBy === "client_name"}
              <span class="sort-icon">{sortAsc ? "↑" : "↓"}</span>
            {/if}
          </th>
          <th class="sortable" onclick={() => toggleSort("description")}>
            Description
            {#if sortBy === "description"}
              <span class="sort-icon">{sortAsc ? "↑" : "↓"}</span>
            {/if}
          </th>
          <th class="sortable" onclick={() => toggleSort("frequency")}>
            Frequency
            {#if sortBy === "frequency"}
              <span class="sort-icon">{sortAsc ? "↑" : "↓"}</span>
            {/if}
          </th>
          <th class="sortable text-right" onclick={() => toggleSort("amount")}>
            Amount
            {#if sortBy === "amount"}
              <span class="sort-icon">{sortAsc ? "↑" : "↓"}</span>
            {/if}
          </th>
          <th
            class="sortable"
            onclick={() => toggleSort("next_due_date")}
          >
            Next Due
            {#if sortBy === "next_due_date"}
              <span class="sort-icon">{sortAsc ? "↑" : "↓"}</span>
            {/if}
          </th>
          <th>Status</th>
          <th class="text-right">Actions</th>
        </tr>
      </thead>
      <tbody>
        {#each sortedFees as fee}
          {@const days = getDaysUntil(fee.next_due_date)}
          {@const urgency = getUrgency(fee.next_due_date)}
          <tr class:row-urgent={urgency === "critical" || urgency === "overdue"}>
            <td class="client-cell">
              <span class="client-name">{fee.client_name || "Unknown"}</span>
            </td>
            <td>
              <div class="desc-cell">
                <span>{fee.description || "-"}</span>
                {#if fee.invoices && fee.invoices.length > 0}
                  <div class="invoice-chips">
                    {#each fee.invoices as inv}
                      <button
                        class="invoice-chip {inv.status}"
                        onclick={() => openInvoice(inv.id)}
                        title="Open invoice PDF"
                      >
                        #{inv.invoice_number} · {inv.status}
                      </button>
                    {/each}
                  </div>
                {/if}
              </div>
            </td>
            <td>
              <span class="freq-badge {fee.frequency}">
                {frequencyLabel(fee.frequency)}
              </span>
            </td>
            <td class="text-right amount">{formatCurrency(fee.amount)}</td>
            <td>
              <div class="due-cell">
                <span class="due-date">{formatDate(fee.next_due_date)}</span>
                {#if days !== null}
                  <span class="days-badge {urgency}">
                    {#if days < 0}
                      {Math.abs(days)}d overdue
                    {:else if days === 0}
                      Today
                    {:else}
                      in {days}d
                    {/if}
                  </span>
                {/if}
              </div>
            </td>
            <td>
              <span class="status-indicator {urgency}"></span>
            </td>
            <td class="text-right">
              <div class="actions">
                <button
                  class="btn-sm invoice"
                  onclick={() => createInvoice(fee)}
                  disabled={creatingInvoice === fee.id}
                  title="Generate a new invoice for this recurring fee"
                >
                  {creatingInvoice === fee.id ? "..." : "Generate"}
                </button>
                <button
                  class="btn-icon danger"
                  onclick={() => removeFee(fee.id)}
                  title="Delete"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <polyline points="3 6 5 6 21 6" />
                    <path
                      d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
                    />
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}

{#if recurringExpenses.length > 0}
  <div class="expenses-section">
    <div class="section-heading">
      <h2>Recurring Expenses</h2>
      <span class="section-meta">{recurringExpenses.length} items · {formatCurrency(recurringExpenses.reduce((s, e) => s + (e.frequency === "monthly" ? e.amount * 12 : e.amount), 0))}/year</span>
    </div>
    <div class="card table-card">
      <table>
        <thead>
          <tr>
            <th>Description</th>
            <th>Category</th>
            <th>Frequency</th>
            <th class="text-right">Amount</th>
            <th>Next Due</th>
            <th class="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {#each recurringExpenses as exp}
            {@const days = getDaysUntil(exp.next_due_date)}
            {@const urgency = getUrgency(exp.next_due_date)}
            <tr class:row-urgent={urgency === "critical" || urgency === "overdue"}>
              <td>{exp.description || "-"}</td>
              <td><span class="category-badge">{exp.category}</span></td>
              <td>
                <span class="freq-badge {exp.frequency}">
                  {frequencyLabel(exp.frequency)}
                </span>
              </td>
              <td class="text-right amount">{formatCurrency(exp.amount)}</td>
              <td>
                <div class="due-cell">
                  <span class="due-date">{formatDate(exp.next_due_date)}</span>
                  {#if days !== null}
                    <span class="days-badge {urgency}">
                      {#if days < 0}
                        {Math.abs(days)}d overdue
                      {:else if days === 0}
                        Today
                      {:else}
                        in {days}d
                      {/if}
                    </span>
                  {/if}
                </div>
              </td>
              <td class="text-right">
                <div class="actions">
                  <button
                    class="btn-sm invoice"
                    onclick={() => generateExpenseNow(exp.id)}
                    disabled={generatingExpense === exp.id}
                    title="Generate a new expense entry"
                  >
                    {generatingExpense === exp.id ? "..." : "Generate"}
                  </button>
                  <button
                    class="btn-icon danger"
                    onclick={() => removeExpense(exp.id)}
                    title="Delete"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
{/if}

<style>
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.5rem;
  }

  h1 {
    margin-bottom: 0.25rem;
  }

  .subtitle {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 0.9375rem;
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .stat-card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    padding: 1rem 1.25rem;
    box-shadow: var(--shadow-sm);
    display: flex;
    flex-direction: column;
  }

  .stat-card.primary {
    background: linear-gradient(135deg, var(--color-primary) 0%, #2563eb 100%);
    color: white;
  }

  .stat-card.primary .stat-label {
    color: rgba(255, 255, 255, 0.8);
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    line-height: 1.2;
  }

  .stat-value.warning {
    color: var(--color-warning);
  }

  .stat-label {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
    margin-top: 0.25rem;
  }

  .card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
  }

  .filter-card {
    padding: 1rem 1.25rem;
    margin-bottom: 1.5rem;
  }

  .filter-row {
    display: flex;
    gap: 1rem;
  }

  .filter-group {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .filter-group label {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  .filter-group select {
    min-width: 160px;
  }

  .table-card {
    overflow: hidden;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  th {
    text-align: left;
    padding: 0.875rem 1rem;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-secondary);
    background: var(--color-bg);
    border-bottom: 1px solid var(--color-border);
  }

  th.sortable {
    cursor: pointer;
    user-select: none;
  }

  th.sortable:hover {
    color: var(--color-primary);
  }

  .sort-icon {
    margin-left: 0.25rem;
    color: var(--color-primary);
  }

  th.text-right,
  td.text-right {
    text-align: right;
  }

  td {
    padding: 1rem;
    border-bottom: 1px solid var(--color-border-light);
    vertical-align: middle;
  }

  tr:last-child td {
    border-bottom: none;
  }

  tr:hover {
    background: var(--color-bg);
  }

  tr.row-urgent {
    background: var(--color-danger-light);
  }

  tr.row-urgent:hover {
    background: #fecaca;
  }

  .client-cell {
    min-width: 140px;
  }

  .client-name {
    font-weight: 600;
  }

  .freq-badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 999px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .freq-badge.monthly {
    background: #dbeafe;
    color: #1e40af;
  }

  .freq-badge.yearly {
    background: #ede9fe;
    color: #5b21b6;
  }

  .freq-badge.one-time {
    background: #f3f4f6;
    color: #374151;
  }

  .amount {
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }

  .expenses-section {
    margin-top: 2.5rem;
  }

  .section-heading {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 1rem;
  }

  .section-heading h2 {
    font-size: 1.125rem;
    font-weight: 600;
    margin: 0;
  }

  .section-meta {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .category-badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 999px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    background: var(--color-bg);
    color: var(--color-text-secondary);
  }

  .desc-cell {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .invoice-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }

  .invoice-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.125rem 0.5rem;
    font-size: 0.6875rem;
    font-weight: 600;
    font-family: inherit;
    border: 1px solid var(--color-border);
    border-radius: 999px;
    background: var(--color-bg);
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: all 0.15s;
  }

  .invoice-chip:hover {
    background: var(--color-primary-light);
    color: var(--color-primary);
    border-color: var(--color-primary);
  }

  .invoice-chip.paid {
    background: var(--color-success-light);
    color: #065f46;
    border-color: transparent;
  }

  .invoice-chip.sent {
    background: var(--color-warning-light);
    color: #92400e;
    border-color: transparent;
  }

  .due-cell {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .due-date {
    font-size: 0.875rem;
  }

  .days-badge {
    display: inline-block;
    padding: 0.125rem 0.375rem;
    border-radius: 999px;
    font-size: 0.625rem;
    font-weight: 600;
    width: fit-content;
  }

  .days-badge.normal {
    background: var(--color-success-light);
    color: #065f46;
  }

  .days-badge.soon {
    background: #dbeafe;
    color: #1e40af;
  }

  .days-badge.warning {
    background: var(--color-warning-light);
    color: #92400e;
  }

  .days-badge.critical {
    background: #fecaca;
    color: #991b1b;
  }

  .days-badge.overdue {
    background: var(--color-danger);
    color: white;
  }

  .status-indicator {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }

  .status-indicator.normal {
    background: var(--color-success);
  }

  .status-indicator.soon {
    background: var(--color-primary);
  }

  .status-indicator.warning {
    background: var(--color-warning);
  }

  .status-indicator.critical {
    background: #f87171;
  }

  .status-indicator.overdue {
    background: var(--color-danger);
  }

  .status-indicator.unknown {
    background: var(--color-text-muted);
  }

  .actions {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 0.25rem;
  }

  .btn-sm {
    padding: 0.375rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: var(--radius-sm);
  }

  .btn-sm.invoice {
    background: #ddd6fe;
    color: #5b21b6;
  }

  .btn-sm.invoice:hover {
    background: #c4b5fd;
  }

  .btn-icon {
    background: transparent;
    color: var(--color-text-muted);
    padding: 0.375rem;
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

  .loading {
    padding: 3rem;
    text-align: center;
    color: var(--color-text-muted);
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
    margin: 0;
  }

  .empty-hint {
    font-size: 0.875rem;
    margin-top: 0.5rem !important;
  }

  @media (max-width: 768px) {
    .table-card {
      overflow-x: auto;
    }

    table {
      min-width: 700px;
    }
  }
</style>
