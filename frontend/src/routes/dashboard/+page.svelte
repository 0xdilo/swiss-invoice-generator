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

  function formatCompact(amount) {
    if (amount >= 1000) {
      return (amount / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
    }
    return amount?.toString() || '0';
  }
</script>

<div class="page">
  <header class="page-header">
    <div class="header-content">
      <div class="greeting">
        <h1>Dashboard</h1>
        <p class="subtitle">Business overview</p>
      </div>
      <div class="period-selector">
        {#each [["month", "Month"], ["year", "Year"], ["all", "All Time"]] as [value, label]}
          <button class:active={period === value} onclick={() => changePeriod(value)}>{label}</button>
        {/each}
      </div>
    </div>
  </header>

  {#if stats}
    <div class="metrics-grid">
      <div class="metric-card featured">
        <div class="metric-header">
          <span class="metric-label">Total Revenue</span>
          <div class="metric-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="1" x2="12" y2="23"/>
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
          </div>
        </div>
        <span class="metric-value">{formatCurrency(stats.total_revenue)}</span>
        <div class="metric-badges">
          <span class="badge neutral">{stats.invoice_counts.draft} draft</span>
          <span class="badge warning">{stats.invoice_counts.sent} sent</span>
          <span class="badge success">{stats.invoice_counts.paid} paid</span>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Outstanding</span>
          <div class="metric-icon warning">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
        </div>
        <span class="metric-value warning">{formatCurrency(stats.outstanding)}</span>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Expenses</span>
          <div class="metric-icon danger">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/>
              <polyline points="17 18 23 18 23 12"/>
            </svg>
          </div>
        </div>
        <span class="metric-value">{formatCurrency(stats.total_expenses)}</span>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Net Profit</span>
          <div class="metric-icon" class:success={stats.net_profit > 0} class:danger={stats.net_profit < 0}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
              <polyline points="17 6 23 6 23 12"/>
            </svg>
          </div>
        </div>
        <span class="metric-value" class:success={stats.net_profit > 0} class:danger={stats.net_profit < 0}>
          {formatCurrency(stats.net_profit)}
        </span>
      </div>
    </div>
  {/if}

  <div class="panels-grid">
    <section class="panel">
      <header class="panel-header">
        <h2>Partner Earnings</h2>
      </header>
      <div class="panel-body">
        {#if partnerData.partners.length > 0}
          <div class="partner-list">
            {#each partnerData.partners as partner}
              <div class="partner-row">
                <div class="partner-info">
                  <span class="partner-dot" style="background-color: {partner.color}"></span>
                  <span class="partner-name">{partner.name}</span>
                </div>
                <span class="partner-amount">{formatCurrency(partner.earnings)}</span>
              </div>
            {/each}
          </div>

          {#if expenseBalance && expenseBalance.balance > 0}
            <div class="balance-alert">
              <div class="alert-content">
                <span class="alert-text"><strong>{expenseBalance.owes_from}</strong> owes <strong>{expenseBalance.owes_to}</strong></span>
                <span class="alert-amount">{formatCurrency(expenseBalance.balance)}</span>
              </div>
              <a href="/expenses" class="alert-action">Settle</a>
            </div>
          {/if}
        {:else}
          <div class="empty-panel">
            <p>No earnings data yet</p>
          </div>
        {/if}
      </div>
    </section>

    <section class="panel">
      <header class="panel-header">
        <h2>Upcoming Renewals</h2>
        <div class="header-tabs">
          {#each [[7, "7d"], [14, "14d"], [30, "30d"]] as [days, label]}
            <button class:active={renewalDays === days} onclick={() => changeRenewalDays(days)}>{label}</button>
          {/each}
        </div>
      </header>
      <div class="panel-body">
        {#if renewals.length > 0}
          <div class="renewal-list">
            {#each renewals as renewal}
              <div class="renewal-row" class:critical={renewal.urgency === "critical"} class:warning={renewal.urgency === "warning"}>
                <div class="renewal-info">
                  <span class="renewal-client">{renewal.client_name}</span>
                  <span class="renewal-desc">{renewal.description || "Renewal"}</span>
                </div>
                <div class="renewal-meta">
                  <span class="renewal-days" class:critical={renewal.urgency === "critical"} class:warning={renewal.urgency === "warning"}>
                    {renewal.days_until}d
                  </span>
                  <span class="renewal-amount">{formatCurrency(renewal.amount)}</span>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <div class="empty-panel">
            <p>No renewals in the next {renewalDays} days</p>
          </div>
        {/if}
      </div>
    </section>
  </div>

  <section class="panel full-width">
    <header class="panel-header">
      <h2>Outstanding Invoices</h2>
      {#if outstanding.length > 0}
        <span class="count-badge">{outstanding.length}</span>
      {/if}
    </header>
    {#if outstanding.length > 0}
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Invoice</th>
              <th>Client</th>
              <th>Status</th>
              <th class="text-right">Amount</th>
            </tr>
          </thead>
          <tbody>
            {#each outstanding as invoice, i}
              <tr style="--delay: {i * 0.03}s">
                <td>
                  <span class="invoice-number">#{invoice.invoice_number}</span>
                </td>
                <td>
                  <span class="client-name">{invoice.client_name || "—"}</span>
                </td>
                <td>
                  <span class="status-tag {invoice.status}">{invoice.status}</span>
                </td>
                <td class="text-right">
                  <span class="amount">{formatCurrency(invoice.total_amount)}</span>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {:else}
      <div class="panel-body">
        <div class="empty-panel">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          <p>No outstanding invoices</p>
        </div>
      </div>
    {/if}
  </section>
</div>

<style>
  .page {
    animation: fadeIn 0.4s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .page-header {
    margin-bottom: 2rem;
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .greeting h1 {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    margin-bottom: 0.25rem;
  }

  .subtitle {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 0.9375rem;
  }

  .period-selector {
    display: flex;
    background: var(--color-surface);
    padding: 0.25rem;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }

  .period-selector button {
    padding: 0.5rem 1rem;
    border-radius: 8px;
    background: transparent;
    color: var(--color-text-secondary);
    font-weight: 500;
    font-size: 0.875rem;
    transition: all 0.15s ease;
  }

  .period-selector button:hover {
    color: var(--color-text);
  }

  .period-selector button.active {
    background: var(--color-text);
    color: var(--color-surface);
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .metric-card {
    background: var(--color-surface);
    border-radius: 16px;
    padding: 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .metric-card.featured {
    grid-column: span 1;
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    color: white;
  }

  .metric-card.featured .metric-label {
    color: rgba(255,255,255,0.7);
  }

  .metric-card.featured .metric-icon {
    background: rgba(255,255,255,0.15);
    color: white;
  }

  .metric-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .metric-label {
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  .metric-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: var(--color-bg);
    color: var(--color-text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .metric-icon.warning {
    background: #fef3c7;
    color: #d97706;
  }

  .metric-icon.danger {
    background: #fee2e2;
    color: #dc2626;
  }

  .metric-icon.success {
    background: #dcfce7;
    color: #16a34a;
  }

  .metric-value {
    font-size: 1.625rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--color-text);
  }

  .metric-card.featured .metric-value {
    color: white;
  }

  .metric-value.warning {
    color: #d97706;
  }

  .metric-value.success {
    color: #16a34a;
  }

  .metric-value.danger {
    color: #dc2626;
  }

  .metric-badges {
    display: flex;
    gap: 0.375rem;
    flex-wrap: wrap;
  }

  .badge {
    font-size: 0.6875rem;
    font-weight: 500;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
  }

  .metric-card.featured .badge {
    background: rgba(255,255,255,0.15);
    color: rgba(255,255,255,0.9);
  }

  .badge.neutral {
    background: var(--color-bg);
    color: var(--color-text-secondary);
  }

  .badge.warning {
    background: #fef3c7;
    color: #92400e;
  }

  .badge.success {
    background: #dcfce7;
    color: #166534;
  }

  .panels-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .panel {
    background: var(--color-surface);
    border-radius: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    overflow: hidden;
  }

  .panel.full-width {
    grid-column: span 2;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .panel-header h2 {
    font-size: 0.9375rem;
    font-weight: 600;
    margin: 0;
  }

  .count-badge {
    font-size: 0.75rem;
    font-weight: 600;
    background: var(--color-text);
    color: var(--color-surface);
    padding: 0.25rem 0.625rem;
    border-radius: 10px;
  }

  .header-tabs {
    display: flex;
    gap: 0.25rem;
    background: var(--color-bg);
    padding: 0.125rem;
    border-radius: 6px;
  }

  .header-tabs button {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    background: transparent;
    color: var(--color-text-muted);
    font-size: 0.75rem;
    font-weight: 500;
    transition: all 0.15s ease;
  }

  .header-tabs button:hover {
    color: var(--color-text);
  }

  .header-tabs button.active {
    background: var(--color-surface);
    color: var(--color-text);
    box-shadow: 0 1px 2px rgba(0,0,0,0.06);
  }

  .panel-body {
    padding: 1rem 1.25rem;
  }

  .partner-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .partner-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background: var(--color-bg);
    border-radius: 10px;
  }

  .partner-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .partner-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }

  .partner-name {
    font-weight: 500;
  }

  .partner-amount {
    font-weight: 600;
    color: #16a34a;
  }

  .balance-alert {
    margin-top: 1rem;
    padding: 0.875rem 1rem;
    background: #fef3c7;
    border-radius: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .alert-content {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .alert-text {
    font-size: 0.875rem;
    color: #92400e;
  }

  .alert-amount {
    font-weight: 600;
    color: #b45309;
  }

  .alert-action {
    padding: 0.375rem 0.75rem;
    background: #92400e;
    color: white;
    border-radius: 6px;
    font-size: 0.8125rem;
    font-weight: 500;
    text-decoration: none;
    transition: background 0.15s ease;
  }

  .alert-action:hover {
    background: #78350f;
    text-decoration: none;
    color: white;
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
    padding: 0.75rem 1rem;
    background: var(--color-bg);
    border-radius: 10px;
    border-left: 3px solid var(--color-border);
    transition: all 0.15s ease;
  }

  .renewal-row.critical {
    border-left-color: #dc2626;
    background: #fef2f2;
  }

  .renewal-row.warning {
    border-left-color: #d97706;
    background: #fffbeb;
  }

  .renewal-info {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .renewal-client {
    font-weight: 500;
    font-size: 0.9375rem;
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
    background: var(--color-bg);
    border-radius: 5px;
    color: var(--color-text-secondary);
  }

  .renewal-days.critical {
    background: #fee2e2;
    color: #dc2626;
  }

  .renewal-days.warning {
    background: #fef3c7;
    color: #92400e;
  }

  .renewal-amount {
    font-weight: 600;
    font-size: 0.9375rem;
  }

  .table-wrapper {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  th {
    padding: 0.75rem 1.25rem;
    text-align: left;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-secondary);
    background: var(--color-bg);
    border-bottom: 1px solid var(--color-border-light);
  }

  th.text-right {
    text-align: right;
  }

  td {
    padding: 0.875rem 1.25rem;
    border-bottom: 1px solid var(--color-border-light);
    vertical-align: middle;
  }

  td.text-right {
    text-align: right;
  }

  tr {
    animation: rowFade 0.3s ease backwards;
    animation-delay: var(--delay);
  }

  @keyframes rowFade {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  tbody tr:hover {
    background: var(--color-bg);
  }

  tbody tr:last-child td {
    border-bottom: none;
  }

  .invoice-number {
    font-family: ui-monospace, monospace;
    font-weight: 600;
    font-size: 0.875rem;
    color: var(--color-primary);
  }

  .client-name {
    font-weight: 500;
  }

  .status-tag {
    display: inline-block;
    padding: 0.25rem 0.625rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: capitalize;
  }

  .status-tag.draft {
    background: var(--color-bg);
    color: var(--color-text-secondary);
  }

  .status-tag.sent {
    background: #fef3c7;
    color: #92400e;
  }

  .status-tag.paid {
    background: #dcfce7;
    color: #166534;
  }

  .amount {
    font-weight: 600;
    font-size: 0.9375rem;
  }

  .empty-panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2.5rem 1rem;
    color: var(--color-text-muted);
    text-align: center;
  }

  .empty-panel svg {
    opacity: 0.3;
    margin-bottom: 0.75rem;
  }

  .empty-panel p {
    margin: 0;
    font-size: 0.9375rem;
  }

  @media (max-width: 1200px) {
    .metrics-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 900px) {
    .panels-grid {
      grid-template-columns: 1fr;
    }

    .panel.full-width {
      grid-column: span 1;
    }
  }

  @media (max-width: 640px) {
    .header-content {
      flex-direction: column;
      align-items: stretch;
    }

    .period-selector {
      justify-content: center;
    }

    .metrics-grid {
      grid-template-columns: 1fr 1fr;
    }

    .greeting h1 {
      font-size: 1.5rem;
    }
  }
</style>
