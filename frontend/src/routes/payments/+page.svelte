<script>
  import { onMount } from "svelte";
  import {
    getPaymentEvents,
    updatePaymentEvent,
    deletePaymentEvent,
    getClients,
  } from "$lib/api.js";

  let events = [];
  let allEvents = [];
  let clients = [];
  let selectedClient = "";
  let selectedStatus = "";
  let todayDate = new Date().toISOString().split("T")[0];

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
    if (confirm("Are you sure you want to delete this payment event?")) {
      await deletePaymentEvent(eventId);
      await loadEvents();
    }
  }

  function formatDate(dateStr) {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString("de-CH", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
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
  $: overdueCount = events.filter((e) =>
    isOverdue(e.due_date, e.status)
  ).length;
  $: totalUnpaid = events
    .filter((e) => e.status !== "paid")
    .reduce((sum, e) => sum + parseFloat(e.amount || 0), 0);
</script>

<h2>Payment Events Timeline</h2>

<div class="stats">
  <div class="stat-card">
    <div class="stat-value">{notSentCount}</div>
    <div class="stat-label">Not Sent</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{sentCount}</div>
    <div class="stat-label">Sent</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{overdueCount}</div>
    <div class="stat-label">Overdue</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{totalUnpaid.toFixed(2)} CHF</div>
    <div class="stat-label">Total Unpaid</div>
  </div>
</div>

<div class="filters">
  <div class="filter-group">
    <label for="filter-client">Filter by Client:</label>
    <select
      id="filter-client"
      bind:value={selectedClient}
      on:change={loadEvents}
    >
      <option value="">All Clients</option>
      {#each clients as client}
        <option value={client.id}>{client.name}</option>
      {/each}
    </select>
  </div>

  <div class="filter-group">
    <label for="filter-status">Filter by Status:</label>
    <select
      id="filter-status"
      bind:value={selectedStatus}
      on:change={loadEvents}
    >
      <option value="">All Statuses</option>
      <option value="not_sent">Not Sent</option>
      <option value="sent">Sent</option>
      <option value="paid">Paid</option>
    </select>
  </div>
</div>

<div class="timeline">
  {#if futureEvents.length > 0}
    <div class="timeline-section">
      <h3 class="section-title future">Upcoming Payments</h3>
      {#each futureEvents as event}
        <div class="event-card future">
          <div class="event-header">
            <div class="event-info">
              <span class="client-name">{event.client_name}</span>
              <span class="event-amount"
                >{event.amount} {event.currency}</span
              >
            </div>
            <div class="event-meta">
              <span class="event-date">{formatDate(event.due_date)}</span>
              <span class="status-badge {event.status}">{event.status}</span>
            </div>
          </div>
          {#if event.description}
            <div class="event-description">{event.description}</div>
          {/if}
          <div class="event-actions">
            {#if event.status === "not_sent"}
              <button class="mark-sent-btn" on:click={() => markAsSent(event.id)}
                >Mark as Sent</button
              >
            {:else if event.status === "sent"}
              <button class="mark-paid-btn" on:click={() => markAsPaid(event.id)}
                >Mark as Paid</button
              >
              <button
                class="mark-not-sent-btn"
                on:click={() => markAsNotSent(event.id)}>Back to Not Sent</button
              >
            {:else if event.status === "paid"}
              <button
                class="mark-sent-btn"
                on:click={() => markAsSent(event.id)}>Back to Sent</button
              >
            {/if}
            {#if event.invoice_id}
              <a href="/invoices" class="invoice-link">View Invoice</a>
            {/if}
            <button class="delete-btn" on:click={() => removeEvent(event.id)}
              >Delete</button
            >
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <div class="today-marker">
    <div class="today-line"></div>
    <span class="today-label">Today</span>
    <div class="today-line"></div>
  </div>

  {#if pastEvents.length > 0}
    <div class="timeline-section">
      <h3 class="section-title past">Past Payments</h3>
      {#each pastEvents as event}
        <div
          class="event-card past {isOverdue(event.due_date, event.status)
            ? 'overdue'
            : ''}"
        >
          <div class="event-header">
            <div class="event-info">
              <span class="client-name">{event.client_name}</span>
              <span class="event-amount"
                >{event.amount} {event.currency}</span
              >
            </div>
            <div class="event-meta">
              <span class="event-date">{formatDate(event.due_date)}</span>
              <span class="status-badge {event.status}">{event.status}</span>
              {#if isOverdue(event.due_date, event.status)}
                <span class="overdue-badge">OVERDUE</span>
              {/if}
            </div>
          </div>
          {#if event.description}
            <div class="event-description">{event.description}</div>
          {/if}
          {#if event.paid_date}
            <div class="paid-info">Paid on: {formatDate(event.paid_date)}</div>
          {/if}
          <div class="event-actions">
            {#if event.status === "not_sent"}
              <button class="mark-sent-btn" on:click={() => markAsSent(event.id)}
                >Mark as Sent</button
              >
            {:else if event.status === "sent"}
              <button class="mark-paid-btn" on:click={() => markAsPaid(event.id)}
                >Mark as Paid</button
              >
              <button
                class="mark-not-sent-btn"
                on:click={() => markAsNotSent(event.id)}>Back to Not Sent</button
              >
            {:else if event.status === "paid"}
              <button
                class="mark-sent-btn"
                on:click={() => markAsSent(event.id)}>Back to Sent</button
              >
            {/if}
            {#if event.invoice_id}
              <a href="/invoices" class="invoice-link">View Invoice</a>
            {/if}
            <button class="delete-btn" on:click={() => removeEvent(event.id)}
              >Delete</button
            >
          </div>
        </div>
      {/each}
    </div>
  {/if}

  {#if events.length === 0}
    <div class="no-events">
      <p>No payment events found.</p>
      <p>Add recurring fees to clients to generate payment events.</p>
    </div>
  {/if}
</div>

<style>
  h2 {
    margin-bottom: 1.5rem;
    color: var(--text-primary-color);
  }

  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background-color: var(--surface-color);
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    text-align: center;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--primary-color);
    margin-bottom: 0.5rem;
  }

  .stat-label {
    color: var(--text-secondary-color);
    font-size: 0.9rem;
  }

  .filters {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 2rem;
    padding: 1.5rem;
    background-color: var(--surface-color);
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  }

  .filter-group {
    flex: 1;
  }

  .filter-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-primary-color);
  }

  .filter-group select {
    width: 100%;
  }

  .timeline {
    margin-top: 2rem;
  }

  .timeline-section {
    margin-bottom: 2rem;
  }

  .section-title {
    font-size: 1.3rem;
    font-weight: 600;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid;
  }

  .section-title.future {
    color: var(--primary-color);
    border-color: var(--primary-color);
  }

  .section-title.past {
    color: var(--text-secondary-color);
    border-color: var(--border-color);
  }

  .today-marker {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 2rem 0;
  }

  .today-line {
    flex: 1;
    height: 2px;
    background: linear-gradient(
      to right,
      var(--border-color),
      var(--primary-color),
      var(--border-color)
    );
  }

  .today-label {
    font-weight: 700;
    color: var(--primary-color);
    padding: 0.25rem 1rem;
    background-color: var(--surface-color);
    border: 2px solid var(--primary-color);
    border-radius: 20px;
    font-size: 0.9rem;
  }

  .event-card {
    background-color: var(--surface-color);
    border-left: 4px solid var(--primary-color);
    padding: 1.25rem;
    border-radius: 6px;
    margin-bottom: 1rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    transition: box-shadow 0.2s ease;
  }

  .event-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  }

  .event-card.past {
    border-left-color: var(--text-secondary-color);
  }

  .event-card.overdue {
    border-left-color: #e53e3e;
    background-color: #fff5f5;
  }

  .event-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.75rem;
  }

  .event-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .client-name {
    font-weight: 600;
    font-size: 1.1rem;
    color: var(--text-primary-color);
  }

  .event-amount {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--primary-color);
  }

  .event-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.5rem;
  }

  .event-date {
    color: var(--text-secondary-color);
    font-size: 0.95rem;
  }

  .status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .status-badge.not_sent {
    background-color: #fee2e2;
    color: #991b1b;
  }

  .status-badge.sent {
    background-color: #fef3c7;
    color: #92400e;
  }

  .status-badge.paid {
    background-color: #d1fae5;
    color: #065f46;
  }

  .overdue-badge {
    background-color: #e53e3e;
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 700;
  }

  .event-description {
    color: var(--text-secondary-color);
    font-style: italic;
    margin-bottom: 0.75rem;
    font-size: 0.95rem;
  }

  .paid-info {
    color: var(--success-color);
    font-size: 0.9rem;
    font-weight: 500;
    margin-bottom: 0.75rem;
  }

  .event-actions {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .event-actions button,
  .event-actions a {
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
    text-decoration: none;
  }

  .mark-paid-btn {
    background-color: var(--success-color);
    color: white;
  }

  .mark-paid-btn:hover {
    background-color: #45a049;
  }

  .mark-sent-btn {
    background-color: #fbbf24;
    color: #78350f;
    border: 1px solid #f59e0b;
  }

  .mark-sent-btn:hover {
    background-color: #f59e0b;
    color: white;
  }

  .mark-not-sent-btn {
    background-color: #fecaca;
    color: #991b1b;
    border: 1px solid #f87171;
  }

  .mark-not-sent-btn:hover {
    background-color: #f87171;
    color: white;
  }

  .invoice-link {
    background-color: var(--primary-color);
    color: white;
    display: inline-flex;
    align-items: center;
  }

  .invoice-link:hover {
    background-color: var(--primary-color-darker);
  }

  .delete-btn {
    background-color: transparent;
    color: #e53e3e;
    border: 1px solid #e53e3e;
  }

  .delete-btn:hover {
    background-color: #e53e3e;
    color: white;
  }

  .no-events {
    text-align: center;
    padding: 3rem;
    background-color: var(--surface-color);
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  }

  .no-events p {
    color: var(--text-secondary-color);
    margin-bottom: 0.5rem;
  }

  @media (max-width: 768px) {
    .filters {
      flex-direction: column;
    }

    .event-header {
      flex-direction: column;
      gap: 0.75rem;
    }

    .event-meta {
      align-items: flex-start;
    }

    .event-actions {
      flex-direction: column;
    }

    .event-actions button,
    .event-actions a {
      width: 100%;
      text-align: center;
    }
  }
</style>
