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

<div class="animate-fade-in">
  <header class="mb-8">
    <div class="flex justify-between items-start gap-4 flex-wrap max-sm:flex-col max-sm:items-stretch">
      <div>
        <h1 class="text-3xl font-bold tracking-tight mb-1">Dashboard</h1>
        <p class="text-text-secondary text-[15px] m-0">Business overview</p>
      </div>
      <div class="flex bg-surface p-1 rounded-xl shadow-sm max-sm:justify-center">
        {#each [["month", "Month"], ["year", "Year"], ["all", "All Time"]] as [value, label]}
          <button
            class="px-4 py-2 rounded-lg font-medium text-sm transition-all duration-150
                   {period === value ? 'bg-text text-surface' : 'bg-transparent text-text-secondary hover:text-text'}"
            onclick={() => changePeriod(value)}
          >
            {label}
          </button>
        {/each}
      </div>
    </div>
  </header>

  {#if stats}
    <div class="grid grid-cols-4 gap-4 mb-6 max-lg:grid-cols-2">
      <div class="card p-5 flex flex-col gap-3 bg-gradient-to-br from-slate-800 to-slate-600 text-white">
        <div class="flex justify-between items-start">
          <span class="text-sm font-medium text-white/70">Total Revenue</span>
          <div class="w-9 h-9 rounded-xl bg-white/15 text-white flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="1" x2="12" y2="23"/>
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
          </div>
        </div>
        <span class="text-2xl font-bold tracking-tight">{formatCurrency(stats.total_revenue)}</span>
        <div class="flex gap-1.5 flex-wrap">
          <span class="text-[11px] font-medium px-2 py-1 rounded-md bg-white/15 text-white/90">{stats.invoice_counts.draft} draft</span>
          <span class="text-[11px] font-medium px-2 py-1 rounded-md bg-white/15 text-white/90">{stats.invoice_counts.sent} sent</span>
          <span class="text-[11px] font-medium px-2 py-1 rounded-md bg-white/15 text-white/90">{stats.invoice_counts.paid} paid</span>
        </div>
      </div>

      <div class="card p-5 flex flex-col gap-3">
        <div class="flex justify-between items-start">
          <span class="text-sm font-medium text-text-secondary">Outstanding</span>
          <div class="w-9 h-9 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
        </div>
        <span class="text-2xl font-bold tracking-tight text-amber-600">{formatCurrency(stats.outstanding)}</span>
      </div>

      <div class="card p-5 flex flex-col gap-3">
        <div class="flex justify-between items-start">
          <span class="text-sm font-medium text-text-secondary">Expenses</span>
          <div class="w-9 h-9 rounded-xl bg-red-100 text-red-600 flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/>
              <polyline points="17 18 23 18 23 12"/>
            </svg>
          </div>
        </div>
        <span class="text-2xl font-bold tracking-tight">{formatCurrency(stats.total_expenses)}</span>
      </div>

      <div class="card p-5 flex flex-col gap-3">
        <div class="flex justify-between items-start">
          <span class="text-sm font-medium text-text-secondary">Net Profit</span>
          <div class="w-9 h-9 rounded-xl flex items-center justify-center
                      {stats.net_profit > 0 ? 'bg-green-100 text-green-600' : stats.net_profit < 0 ? 'bg-red-100 text-red-600' : 'bg-bg text-text-secondary'}">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
              <polyline points="17 6 23 6 23 12"/>
            </svg>
          </div>
        </div>
        <span class="text-2xl font-bold tracking-tight
                     {stats.net_profit > 0 ? 'text-green-600' : stats.net_profit < 0 ? 'text-red-600' : ''}">
          {formatCurrency(stats.net_profit)}
        </span>
      </div>
    </div>
  {/if}

  <div class="grid grid-cols-2 gap-6 mb-6 max-lg:grid-cols-1">
    <section class="card overflow-hidden">
      <header class="flex justify-between items-center px-5 py-4 border-b border-border-light">
        <h2 class="text-[15px] font-semibold m-0">Partner Earnings</h2>
      </header>
      <div class="p-5">
        {#if partnerData.partners.length > 0}
          <div class="flex flex-col gap-2">
            {#each partnerData.partners as partner}
              <div class="flex justify-between items-center px-4 py-3 bg-bg rounded-xl">
                <div class="flex items-center gap-3">
                  <span class="w-2.5 h-2.5 rounded-full" style="background-color: {partner.color}"></span>
                  <span class="font-medium">{partner.name}</span>
                </div>
                <span class="font-semibold text-green-600">{formatCurrency(partner.earnings)}</span>
              </div>
            {/each}
          </div>

          {#if expenseBalance && expenseBalance.balance > 0}
            <div class="mt-4 p-4 bg-amber-100 rounded-xl flex justify-between items-center">
              <div class="flex flex-col gap-0.5">
                <span class="text-sm text-amber-800"><strong>{expenseBalance.owes_from}</strong> owes <strong>{expenseBalance.owes_to}</strong></span>
                <span class="font-semibold text-amber-700">{formatCurrency(expenseBalance.balance)}</span>
              </div>
              <a href="/expenses" class="px-3 py-1.5 bg-amber-800 text-white rounded-md text-sm font-medium hover:bg-amber-900 transition-colors no-underline">
                Settle
              </a>
            </div>
          {/if}
        {:else}
          <div class="flex flex-col items-center justify-center py-10 text-text-muted text-center">
            <p class="m-0 text-[15px]">No earnings data yet</p>
          </div>
        {/if}
      </div>
    </section>

    <section class="card overflow-hidden">
      <header class="flex justify-between items-center px-5 py-4 border-b border-border-light">
        <h2 class="text-[15px] font-semibold m-0">Upcoming Renewals</h2>
        <div class="flex gap-1 bg-bg p-0.5 rounded-md">
          {#each [[7, "7d"], [14, "14d"], [30, "30d"]] as [days, label]}
            <button
              class="px-2 py-1 rounded text-xs font-medium transition-all duration-150
                     {renewalDays === days ? 'bg-surface text-text shadow-sm' : 'bg-transparent text-text-muted hover:text-text'}"
              onclick={() => changeRenewalDays(days)}
            >
              {label}
            </button>
          {/each}
        </div>
      </header>
      <div class="p-5">
        {#if renewals.length > 0}
          <div class="flex flex-col gap-2">
            {#each renewals as renewal}
              <div class="flex justify-between items-center px-4 py-3 bg-bg rounded-xl border-l-[3px] transition-all
                          {renewal.urgency === 'critical' ? 'border-l-red-600 bg-red-50' :
                           renewal.urgency === 'warning' ? 'border-l-amber-600 bg-amber-50' : 'border-l-border'}">
                <div class="flex flex-col gap-0.5">
                  <span class="font-medium text-[15px]">{renewal.client_name}</span>
                  <span class="text-sm text-text-secondary">{renewal.description || "Renewal"}</span>
                </div>
                <div class="flex items-center gap-3">
                  <span class="text-xs font-semibold px-2 py-1 rounded
                              {renewal.urgency === 'critical' ? 'bg-red-100 text-red-600' :
                               renewal.urgency === 'warning' ? 'bg-amber-100 text-amber-700' : 'bg-bg text-text-secondary'}">
                    {renewal.days_until}d
                  </span>
                  <span class="font-semibold text-[15px]">{formatCurrency(renewal.amount)}</span>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <div class="flex flex-col items-center justify-center py-10 text-text-muted text-center">
            <p class="m-0 text-[15px]">No renewals in the next {renewalDays} days</p>
          </div>
        {/if}
      </div>
    </section>
  </div>

  <section class="card overflow-hidden">
    <header class="flex justify-between items-center px-5 py-4 border-b border-border-light">
      <h2 class="text-[15px] font-semibold m-0">Outstanding Invoices</h2>
      {#if outstanding.length > 0}
        <span class="text-xs font-semibold bg-text text-surface px-2.5 py-1 rounded-full">{outstanding.length}</span>
      {/if}
    </header>
    {#if outstanding.length > 0}
      <div class="overflow-x-auto">
        <table class="w-full border-collapse">
          <thead>
            <tr>
              <th class="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-secondary bg-bg border-b border-border-light">Invoice</th>
              <th class="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-secondary bg-bg border-b border-border-light">Client</th>
              <th class="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-secondary bg-bg border-b border-border-light">Status</th>
              <th class="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-text-secondary bg-bg border-b border-border-light">Amount</th>
            </tr>
          </thead>
          <tbody>
            {#each outstanding as invoice, i}
              <tr class="hover:bg-bg transition-colors" style="animation: fadeIn 0.3s ease backwards; animation-delay: {i * 0.03}s">
                <td class="px-5 py-4 border-b border-border-light">
                  <span class="font-mono font-semibold text-sm text-primary">#{invoice.invoice_number}</span>
                </td>
                <td class="px-5 py-4 border-b border-border-light">
                  <span class="font-medium">{invoice.client_name || "—"}</span>
                </td>
                <td class="px-5 py-4 border-b border-border-light">
                  <span class="inline-block px-2.5 py-1 rounded-md text-xs font-medium capitalize
                              {invoice.status === 'paid' ? 'bg-green-100 text-green-700' :
                               invoice.status === 'sent' ? 'bg-amber-100 text-amber-700' : 'bg-bg text-text-secondary'}">
                    {invoice.status}
                  </span>
                </td>
                <td class="px-5 py-4 border-b border-border-light text-right">
                  <span class="font-semibold text-[15px]">{formatCurrency(invoice.total_amount)}</span>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {:else}
      <div class="p-5">
        <div class="flex flex-col items-center justify-center py-10 text-text-muted text-center">
          <svg class="opacity-30 mb-3" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          <p class="m-0 text-[15px]">No outstanding invoices</p>
        </div>
      </div>
    {/if}
  </section>
</div>
