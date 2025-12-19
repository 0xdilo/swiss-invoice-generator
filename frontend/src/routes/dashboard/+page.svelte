<script>
  import { onMount } from "svelte";
  import { getDashboardStats, getDashboardRenewals, getDashboardOutstanding, getPartnerEarnings, getExpenseBalance } from "$lib/api.js";

  let stats = null;
  let renewals = [];
  let outstanding = [];
  let partnerData = { partners: [] };
  let expenseBalance = null;
  let period = "all";
  let renewalDays = 30;

  async function load() {
    [stats, renewals, outstanding, partnerData, expenseBalance] = await Promise.all([
      getDashboardStats(period),
      getDashboardRenewals(renewalDays),
      getDashboardOutstanding(),
      getPartnerEarnings(period),
      getExpenseBalance()
    ]);
  }

  onMount(load);

  async function changePeriod(newPeriod) {
    period = newPeriod;
    stats = await getDashboardStats(period);
    partnerData = await getPartnerEarnings(period);
  }

  async function changeRenewalDays(days) {
    renewalDays = days;
    renewals = await getDashboardRenewals(days);
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat('de-CH', { style: 'currency', currency: 'CHF' }).format(amount || 0);
  }
</script>

<div class="page-header">
  <div>
    <h1>Dashboard</h1>
    <p class="subtitle">Overview of your business performance</p>
  </div>
  <div class="period-tabs">
    <button class:active={period === "month"} onclick={() => changePeriod("month")}>Month</button>
    <button class:active={period === "year"} onclick={() => changePeriod("year")}>Year</button>
    <button class:active={period === "all"} onclick={() => changePeriod("all")}>All Time</button>
  </div>
</div>

{#if stats}
  <div class="stats-row">
    <div class="stat-card primary">
      <div class="stat-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="1" x2="12" y2="23"/>
          <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
        </svg>
      </div>
      <div class="stat-content">
        <span class="stat-value">{formatCurrency(stats.total_revenue)}</span>
        <span class="stat-label">Total Revenue</span>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-icon warning">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
      </div>
      <div class="stat-content">
        <span class="stat-value">{formatCurrency(stats.outstanding)}</span>
        <span class="stat-label">Outstanding</span>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-icon danger">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>
        </svg>
      </div>
      <div class="stat-content">
        <span class="stat-value">{formatCurrency(stats.total_expenses)}</span>
        <span class="stat-label">Expenses</span>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-icon" class:success={stats.net_profit > 0} class:danger={stats.net_profit < 0}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
          <polyline points="17 6 23 6 23 12"/>
        </svg>
      </div>
      <div class="stat-content">
        <span class="stat-value" class:positive={stats.net_profit > 0} class:negative={stats.net_profit < 0}>
          {formatCurrency(stats.net_profit)}
        </span>
        <span class="stat-label">Net Profit</span>
      </div>
    </div>
  </div>

  <div class="invoice-summary">
    <span class="badge draft">{stats.invoice_counts.draft} Draft</span>
    <span class="badge sent">{stats.invoice_counts.sent} Sent</span>
    <span class="badge paid">{stats.invoice_counts.paid} Paid</span>
  </div>
{/if}

<div class="grid-2">
  <div class="card">
    <div class="card-header">
      <h3>Partner Earnings</h3>
    </div>
    <div class="card-body">
      {#if partnerData.partners.length > 0}
        <div class="partner-list">
          {#each partnerData.partners as partner}
            <div class="partner-row">
              <div class="partner-info">
                <span class="partner-dot" style="background-color: {partner.color}"></span>
                <span class="partner-name">{partner.name}</span>
              </div>
              <span class="partner-earnings">{formatCurrency(partner.earnings)}</span>
            </div>
          {/each}
        </div>
      {:else}
        <p class="empty-state">No earnings data yet</p>
      {/if}

      {#if expenseBalance && expenseBalance.balance > 0}
        <div class="balance-card">
          <span class="balance-text">
            <strong>{expenseBalance.owes_from}</strong> owes <strong>{expenseBalance.owes_to}</strong>
          </span>
          <span class="balance-amount">{formatCurrency(expenseBalance.balance)}</span>
        </div>
      {/if}
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <h3>Upcoming Renewals</h3>
      <div class="header-tabs">
        <button class:active={renewalDays === 7} onclick={() => changeRenewalDays(7)}>7d</button>
        <button class:active={renewalDays === 14} onclick={() => changeRenewalDays(14)}>14d</button>
        <button class:active={renewalDays === 30} onclick={() => changeRenewalDays(30)}>30d</button>
      </div>
    </div>
    <div class="card-body">
      {#if renewals.length > 0}
        <div class="renewal-list">
          {#each renewals as renewal}
            <div class="renewal-row" class:critical={renewal.urgency === "critical"} class:warning={renewal.urgency === "warning"}>
              <div class="renewal-info">
                <span class="renewal-client">{renewal.client_name}</span>
                <span class="renewal-desc">{renewal.description || "Renewal"}</span>
              </div>
              <div class="renewal-meta">
                <span class="renewal-days">{renewal.days_until}d</span>
                <span class="renewal-amount">{formatCurrency(renewal.amount)}</span>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <p class="empty-state">No renewals in the next {renewalDays} days</p>
      {/if}
    </div>
  </div>
</div>

<div class="card">
  <div class="card-header">
    <h3>Outstanding Invoices</h3>
  </div>
  <div class="card-body">
    {#if outstanding.length > 0}
      <table>
        <thead>
          <tr>
            <th>Invoice</th>
            <th>Client</th>
            <th>Status</th>
            <th style="text-align: right">Amount</th>
          </tr>
        </thead>
        <tbody>
          {#each outstanding as invoice}
            <tr>
              <td><span class="invoice-id">#{invoice.invoice_number}</span></td>
              <td>{invoice.client_name || "—"}</td>
              <td><span class="badge {invoice.status}">{invoice.status}</span></td>
              <td style="text-align: right; font-weight: 600">{formatCurrency(invoice.total_amount)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {:else}
      <p class="empty-state">No outstanding invoices</p>
    {/if}
  </div>
</div>

<style>
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 2rem;
    gap: 1rem;
    flex-wrap: wrap;
  }

  h1 {
    margin-bottom: 0.25rem;
  }

  .subtitle {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 0.9375rem;
  }

  .period-tabs {
    display: flex;
    background: var(--color-surface);
    border-radius: var(--radius-md);
    padding: 0.25rem;
    box-shadow: var(--shadow-sm);
  }

  .period-tabs button {
    background: transparent;
    color: var(--color-text-secondary);
    padding: 0.5rem 1rem;
    border-radius: var(--radius-sm);
  }

  .period-tabs button:hover {
    color: var(--color-text);
  }

  .period-tabs button.active {
    background: var(--color-primary);
    color: white;
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .stat-card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    padding: 1.25rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    box-shadow: var(--shadow-sm);
  }

  .stat-card.primary {
    background: linear-gradient(135deg, var(--color-primary) 0%, #2563eb 100%);
    color: white;
  }

  .stat-card.primary .stat-label {
    color: rgba(255, 255, 255, 0.8);
  }

  .stat-card.primary .stat-icon {
    background: rgba(255, 255, 255, 0.2);
    color: white;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-md);
    background: var(--color-primary-light);
    color: var(--color-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .stat-icon.warning {
    background: var(--color-warning-light);
    color: var(--color-warning);
  }

  .stat-icon.danger {
    background: var(--color-danger-light);
    color: var(--color-danger);
  }

  .stat-icon.success {
    background: var(--color-success-light);
    color: var(--color-success);
  }

  .stat-content {
    display: flex;
    flex-direction: column;
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    line-height: 1.2;
  }

  .stat-value.positive {
    color: var(--color-success);
  }

  .stat-value.negative {
    color: var(--color-danger);
  }

  .stat-label {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
    margin-top: 0.125rem;
  }

  .invoice-summary {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    padding: 0.375rem 0.75rem;
    border-radius: 999px;
    font-size: 0.8125rem;
    font-weight: 500;
  }

  .badge.draft {
    background: var(--color-border-light);
    color: var(--color-text-secondary);
  }

  .badge.sent {
    background: var(--color-warning-light);
    color: #92400e;
  }

  .badge.paid {
    background: var(--color-success-light);
    color: #065f46;
  }

  .grid-2 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    overflow: hidden;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .card-header h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
  }

  .header-tabs {
    display: flex;
    gap: 0.25rem;
  }

  .header-tabs button {
    background: transparent;
    color: var(--color-text-muted);
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    border-radius: var(--radius-sm);
  }

  .header-tabs button:hover {
    color: var(--color-text);
    background: var(--color-bg);
  }

  .header-tabs button.active {
    background: var(--color-primary);
    color: white;
  }

  .card-body {
    padding: 1.25rem;
  }

  .partner-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .partner-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: var(--color-bg);
    border-radius: var(--radius-md);
  }

  .partner-info {
    display: flex;
    align-items: center;
    gap: 0.625rem;
  }

  .partner-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }

  .partner-name {
    font-weight: 500;
  }

  .partner-earnings {
    font-weight: 600;
    color: var(--color-success);
  }

  .balance-card {
    margin-top: 1rem;
    padding: 0.875rem;
    background: var(--color-warning-light);
    border-radius: var(--radius-md);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .balance-text {
    font-size: 0.875rem;
  }

  .balance-amount {
    font-weight: 600;
    color: #b45309;
  }

  .renewal-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .renewal-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: var(--color-bg);
    border-radius: var(--radius-md);
    border-left: 3px solid var(--color-primary);
  }

  .renewal-row.critical {
    border-left-color: var(--color-danger);
    background: var(--color-danger-light);
  }

  .renewal-row.warning {
    border-left-color: var(--color-warning);
    background: var(--color-warning-light);
  }

  .renewal-info {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .renewal-client {
    font-weight: 500;
  }

  .renewal-desc {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .renewal-meta {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .renewal-days {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.25rem 0.5rem;
    background: rgba(0, 0, 0, 0.06);
    border-radius: var(--radius-sm);
  }

  .renewal-amount {
    font-weight: 600;
  }

  .invoice-id {
    font-family: ui-monospace, monospace;
    font-size: 0.875rem;
    color: var(--color-primary);
    font-weight: 600;
  }

  .empty-state {
    text-align: center;
    color: var(--color-text-muted);
    padding: 2rem 1rem;
    margin: 0;
  }

  @media (max-width: 900px) {
    .grid-2 {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 640px) {
    .page-header {
      flex-direction: column;
      align-items: stretch;
    }

    .period-tabs {
      justify-content: center;
    }

    .stats-row {
      grid-template-columns: 1fr 1fr;
    }
  }
</style>
