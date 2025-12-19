<script>
  import { onMount } from "svelte";
  import {
    getPaymentEvents,
    updatePaymentEvent,
    deletePaymentEvent,
    getClients,
    generateInvoiceFromRecurring,
  } from "$lib/api.js";

  let events = [];
  let allEvents = [];
  let clients = [];
  let selectedClient = "";
  let selectedStatus = "";
  let todayDate = new Date().toISOString().split("T")[0];
  let creatingInvoice = null;

  async function load() {
    clients = await getClients();
    await loadEvents();
  }

  async function loadEvents() {
    const clientId = selectedClient ? parseInt(selectedClient) : null;
    const status = selectedStatus || null;
    allEvents = await getPaymentEvents(clientId, status);
    events = allEvents;
  }

  onMount(load);

  async function markAsSent(eventId) {
    await updatePaymentEvent(eventId, { status: "sent" });
    await loadEvents();
  }

  async function markAsPaid(eventId) {
    await updatePaymentEvent(eventId, { status: "paid" });
    await loadEvents();
  }

  async function markAsNotSent(eventId) {
    await updatePaymentEvent(eventId, { status: "not_sent" });
    await loadEvents();
  }

  async function removeEvent(eventId) {
    if (confirm("Delete this payment event?")) {
      await deletePaymentEvent(eventId);
      await loadEvents();
    }
  }

  async function createInvoiceFromEvent(event) {
    if (!event.recurring_fee_id) {
      alert("This event is not linked to a recurring fee.");
      return;
    }
    creatingInvoice = event.id;
    try {
      const result = await generateInvoiceFromRecurring(event.recurring_fee_id);
      alert(`Invoice #${result.invoice_number} created!`);
      await loadEvents();
    } catch (e) {
      alert("Failed to create invoice.");
    }
    creatingInvoice = null;
  }

  function formatDate(dateStr) {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString("de-CH", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat('de-CH', { style: 'currency', currency: 'CHF' }).format(amount || 0);
  }

  function isOverdue(dueDate, status) {
    if (status === "paid") return false;
    return new Date(dueDate) < new Date(todayDate);
  }

  function isPast(dueDate) {
    return new Date(dueDate) < new Date(todayDate);
  }

  function isFuture(dueDate) {
    return new Date(dueDate) >= new Date(todayDate);
  }

  $: pastEvents = events.filter((e) => isPast(e.due_date));
  $: futureEvents = events.filter((e) => isFuture(e.due_date));
  $: notSentCount = events.filter((e) => e.status === "not_sent").length;
  $: sentCount = events.filter((e) => e.status === "sent").length;
  $: overdueCount = events.filter((e) => isOverdue(e.due_date, e.status)).length;
  $: totalUnpaid = events
    .filter((e) => e.status !== "paid")
    .reduce((sum, e) => sum + parseFloat(e.amount || 0), 0);
</script>

<div class="page-header">
  <div>
    <h1>Payments</h1>
    <p class="subtitle">Track payment events and renewals</p>
  </div>
</div>

<div class="stats-row">
  <div class="stat-card">
    <span class="stat-value danger">{notSentCount}</span>
    <span class="stat-label">Not Sent</span>
  </div>
  <div class="stat-card">
    <span class="stat-value warning">{sentCount}</span>
    <span class="stat-label">Sent</span>
  </div>
  <div class="stat-card">
    <span class="stat-value" class:danger={overdueCount > 0}>{overdueCount}</span>
    <span class="stat-label">Overdue</span>
  </div>
  <div class="stat-card primary">
    <span class="stat-value">{formatCurrency(totalUnpaid)}</span>
    <span class="stat-label">Total Unpaid</span>
  </div>
</div>

<div class="card filter-card">
  <div class="filter-row">
    <div class="filter-group">
      <label>Client</label>
      <select bind:value={selectedClient} onchange={loadEvents}>
        <option value="">All Clients</option>
        {#each clients as client}
          <option value={client.id}>{client.name}</option>
        {/each}
      </select>
    </div>
    <div class="filter-group">
      <label>Status</label>
      <select bind:value={selectedStatus} onchange={loadEvents}>
        <option value="">All</option>
        <option value="not_sent">Not Sent</option>
        <option value="sent">Sent</option>
        <option value="paid">Paid</option>
      </select>
    </div>
  </div>
</div>

<div class="timeline">
  {#if futureEvents.length > 0}
    <div class="timeline-section">
      <div class="section-label upcoming">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
        Upcoming
      </div>
      <div class="events-list">
        {#each futureEvents as event}
          <div class="event-card">
            <div class="event-left">
              <span class="event-date">{formatDate(event.due_date)}</span>
              <div class="event-details">
                <span class="event-client">{event.client_name}</span>
                {#if event.description}
                  <span class="event-desc">{event.description}</span>
                {/if}
              </div>
            </div>
            <div class="event-right">
              <span class="event-amount">{formatCurrency(event.amount)}</span>
              <span class="status-badge {event.status}">{event.status.replace('_', ' ')}</span>
              <div class="event-actions">
                {#if event.status === "not_sent"}
                  <button class="btn-xs sent" onclick={() => markAsSent(event.id)}>Send</button>
                {:else if event.status === "sent"}
                  <button class="btn-xs paid" onclick={() => markAsPaid(event.id)}>Paid</button>
                {/if}
                {#if event.recurring_fee_id && event.status !== "paid" && !event.invoice_id}
                  <button class="btn-xs invoice" onclick={() => createInvoiceFromEvent(event)} disabled={creatingInvoice === event.id}>
                    {creatingInvoice === event.id ? "..." : "Invoice"}
                  </button>
                {/if}
                <button class="btn-icon danger" onclick={() => removeEvent(event.id)} title="Delete">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <div class="today-divider">
    <span>Today</span>
  </div>

  {#if pastEvents.length > 0}
    <div class="timeline-section">
      <div class="section-label past">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 3v5h5"/>
          <path d="M21 12A9 9 0 0 0 6 5.3L3 8"/>
        </svg>
        Past
      </div>
      <div class="events-list">
        {#each pastEvents as event}
          <div class="event-card" class:overdue={isOverdue(event.due_date, event.status)}>
            <div class="event-left">
              <span class="event-date">{formatDate(event.due_date)}</span>
              <div class="event-details">
                <span class="event-client">{event.client_name}</span>
                {#if event.description}
                  <span class="event-desc">{event.description}</span>
                {/if}
              </div>
            </div>
            <div class="event-right">
              <span class="event-amount">{formatCurrency(event.amount)}</span>
              <div class="status-group">
                <span class="status-badge {event.status}">{event.status.replace('_', ' ')}</span>
                {#if isOverdue(event.due_date, event.status)}
                  <span class="overdue-badge">Overdue</span>
                {/if}
              </div>
              <div class="event-actions">
                {#if event.status === "not_sent"}
                  <button class="btn-xs sent" onclick={() => markAsSent(event.id)}>Send</button>
                {:else if event.status === "sent"}
                  <button class="btn-xs paid" onclick={() => markAsPaid(event.id)}>Paid</button>
                {/if}
                {#if event.recurring_fee_id && event.status !== "paid" && !event.invoice_id}
                  <button class="btn-xs invoice" onclick={() => createInvoiceFromEvent(event)} disabled={creatingInvoice === event.id}>
                    {creatingInvoice === event.id ? "..." : "Invoice"}
                  </button>
                {/if}
                <button class="btn-icon danger" onclick={() => removeEvent(event.id)} title="Delete">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  {#if events.length === 0}
    <div class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="12 6 12 12 16 14"/>
      </svg>
      <p>No payment events yet</p>
      <p class="empty-hint">Add recurring fees to clients to generate payment events</p>
    </div>
  {/if}
</div>

<style>
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.5rem;
  }

  h1 { margin-bottom: 0.25rem; }

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

  .stat-value.danger {
    color: var(--color-danger);
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

  .timeline {
    margin-top: 1rem;
  }

  .timeline-section {
    margin-bottom: 1.5rem;
  }

  .section-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid;
  }

  .section-label.upcoming {
    color: var(--color-primary);
    border-color: var(--color-primary);
  }

  .section-label.past {
    color: var(--color-text-muted);
    border-color: var(--color-border);
  }

  .today-divider {
    display: flex;
    align-items: center;
    margin: 1.5rem 0;
  }

  .today-divider::before,
  .today-divider::after {
    content: "";
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, transparent, var(--color-border), transparent);
  }

  .today-divider span {
    padding: 0.375rem 1rem;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-primary);
    background: var(--color-primary-light);
    border-radius: 999px;
  }

  .events-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .event-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    background: var(--color-surface);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
    border-left: 3px solid var(--color-primary);
  }

  .event-card.overdue {
    border-left-color: var(--color-danger);
    background: var(--color-danger-light);
  }

  .event-left {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
  }

  .event-date {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
    min-width: 80px;
  }

  .event-details {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .event-client {
    font-weight: 600;
  }

  .event-desc {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .event-right {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .event-amount {
    font-weight: 600;
    font-size: 1rem;
  }

  .status-group {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.25rem;
  }

  .status-badge {
    display: inline-block;
    padding: 0.25rem 0.625rem;
    border-radius: 999px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .status-badge.not_sent {
    background: var(--color-danger-light);
    color: #991b1b;
  }

  .status-badge.sent {
    background: var(--color-warning-light);
    color: #92400e;
  }

  .status-badge.paid {
    background: var(--color-success-light);
    color: #065f46;
  }

  .overdue-badge {
    font-size: 0.625rem;
    font-weight: 700;
    text-transform: uppercase;
    padding: 0.125rem 0.5rem;
    border-radius: 999px;
    background: var(--color-danger);
    color: white;
  }

  .event-actions {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .btn-xs {
    padding: 0.25rem 0.5rem;
    font-size: 0.6875rem;
    font-weight: 600;
    border-radius: var(--radius-sm);
  }

  .btn-xs.sent {
    background: var(--color-warning-light);
    color: #92400e;
  }

  .btn-xs.sent:hover {
    background: #fde68a;
  }

  .btn-xs.paid {
    background: var(--color-success-light);
    color: #065f46;
  }

  .btn-xs.paid:hover {
    background: #a7f3d0;
  }

  .btn-xs.invoice {
    background: #ddd6fe;
    color: #5b21b6;
  }

  .btn-xs.invoice:hover {
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
    margin-top: 0.5rem;
  }

  @media (max-width: 768px) {
    .filter-row {
      flex-direction: column;
    }

    .filter-group select {
      min-width: 100%;
    }

    .event-card {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .event-right {
      width: 100%;
      justify-content: space-between;
      flex-wrap: wrap;
    }
  }
</style>
