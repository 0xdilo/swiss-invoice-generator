<script>
  import { onMount } from "svelte";
  import { getCalendarEvents, createCalendarEvent, updateCalendarEvent, deleteCalendarEvent, getClients } from "$lib/api.js";

  let events = [];
  let clients = [];
  let currentDate = new Date();
  let showForm = false;
  let editingEvent = null;
  let selectedDate = null;
  let viewingDay = null;
  let form = {
    title: "",
    description: "",
    start_datetime: "",
    end_datetime: "",
    all_day: false,
    event_type: "appointment",
    client_id: null,
    color: "#3b82f6"
  };

  const eventTypes = [
    { value: "appointment", label: "Appointment", icon: "calendar" },
    { value: "meeting", label: "Meeting", icon: "users" },
    { value: "deadline", label: "Deadline", icon: "alert" },
    { value: "reminder", label: "Reminder", icon: "bell" }
  ];

  const colors = [
    { value: "#3b82f6", name: "Blue" },
    { value: "#10b981", name: "Green" },
    { value: "#f59e0b", name: "Amber" },
    { value: "#ef4444", name: "Red" },
    { value: "#8b5cf6", name: "Purple" },
    { value: "#ec4899", name: "Pink" }
  ];

  async function load() {
    const startOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const endOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    [events, clients] = await Promise.all([
      getCalendarEvents({
        start: startOfMonth.toISOString().split("T")[0],
        end: endOfMonth.toISOString().split("T")[0]
      }),
      getClients()
    ]);
  }

  onMount(load);

  $: currentMonth = currentDate.toLocaleString("default", { month: "long" });
  $: currentYear = currentDate.getFullYear();

  $: calendarDays = (() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startPadding = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1;
    const days = [];

    for (let i = startPadding - 1; i >= 0; i--) {
      const d = new Date(year, month, -i);
      days.push({ date: d, isCurrentMonth: false, events: [] });
    }

    for (let i = 1; i <= lastDay.getDate(); i++) {
      const d = new Date(year, month, i);
      const dayEvents = events.filter(e => {
        const eventDate = new Date(e.start_datetime);
        return eventDate.getFullYear() === d.getFullYear() &&
               eventDate.getMonth() === d.getMonth() &&
               eventDate.getDate() === d.getDate();
      });
      days.push({ date: d, isCurrentMonth: true, events: dayEvents });
    }

    const remaining = 42 - days.length;
    for (let i = 1; i <= remaining; i++) {
      const d = new Date(year, month + 1, i);
      days.push({ date: d, isCurrentMonth: false, events: [] });
    }

    return days;
  })();

  $: todayEvents = events.filter(e => {
    const eventDate = new Date(e.start_datetime);
    const today = new Date();
    return eventDate.toDateString() === today.toDateString();
  });

  $: upcomingEvents = events
    .filter(e => new Date(e.start_datetime) > new Date())
    .sort((a, b) => new Date(a.start_datetime) - new Date(b.start_datetime))
    .slice(0, 5);

  function prevMonth() {
    currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1);
    load();
  }

  function nextMonth() {
    currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1);
    load();
  }

  function goToToday() {
    currentDate = new Date();
    load();
  }

  function isToday(date) {
    const today = new Date();
    return date.getFullYear() === today.getFullYear() &&
           date.getMonth() === today.getMonth() &&
           date.getDate() === today.getDate();
  }

  function openDayView(day) {
    if (day.events.length > 0) {
      viewingDay = day;
    } else {
      openNewEvent(day.date);
    }
  }

  function openNewEvent(date = null) {
    viewingDay = null;
    selectedDate = date;
    const dateStr = date ? date.toISOString().split("T")[0] : new Date().toISOString().split("T")[0];
    form = {
      title: "",
      description: "",
      start_datetime: `${dateStr}T09:00`,
      end_datetime: `${dateStr}T10:00`,
      all_day: false,
      event_type: "appointment",
      client_id: null,
      color: "#3b82f6"
    };
    editingEvent = null;
    showForm = true;
  }

  function openEditEvent(event) {
    viewingDay = null;
    editingEvent = event;
    const startDt = event.start_datetime ? event.start_datetime.replace(" ", "T").slice(0, 16) : "";
    const endDt = event.end_datetime ? event.end_datetime.replace(" ", "T").slice(0, 16) : "";
    form = {
      title: event.title,
      description: event.description || "",
      start_datetime: startDt,
      end_datetime: endDt,
      all_day: !!event.all_day,
      event_type: event.event_type || "appointment",
      client_id: event.client_id,
      color: event.color || "#3b82f6"
    };
    showForm = true;
  }

  async function handleSubmit() {
    const eventData = {
      ...form,
      start_datetime: form.start_datetime.replace("T", " ") + ":00",
      end_datetime: form.end_datetime ? form.end_datetime.replace("T", " ") + ":00" : null
    };
    if (editingEvent) {
      await updateCalendarEvent(editingEvent.id, eventData);
    } else {
      await createCalendarEvent(eventData);
    }
    resetForm();
    await load();
  }

  async function handleDelete() {
    if (editingEvent && confirm("Delete this event?")) {
      await deleteCalendarEvent(editingEvent.id);
      resetForm();
      await load();
    }
  }

  function resetForm() {
    showForm = false;
    editingEvent = null;
    selectedDate = null;
  }

  function formatEventTime(datetime) {
    if (!datetime) return "";
    const d = new Date(datetime.replace(" ", "T"));
    return d.toLocaleTimeString("de-CH", { hour: "2-digit", minute: "2-digit" });
  }

  function formatFullDate(date) {
    return date.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });
  }

  function getWeekday(index) {
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    return days[index];
  }
</script>

<div class="page">
  <header class="page-header">
    <div class="header-main">
      <div class="month-nav">
        <button class="nav-arrow" onclick={prevMonth} aria-label="Previous month">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <div class="month-display">
          <span class="month-name">{currentMonth}</span>
          <span class="year">{currentYear}</span>
        </div>
        <button class="nav-arrow" onclick={nextMonth} aria-label="Next month">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
      </div>

      <div class="header-actions">
        <button class="btn-today" onclick={goToToday}>Today</button>
        <button class="btn-add" onclick={() => openNewEvent()}>
          <span>+</span>
          <span class="btn-add-text">New Event</span>
        </button>
      </div>
    </div>
  </header>

  <div class="calendar-layout">
    <div class="calendar-main">
      <div class="calendar-grid">
        <div class="weekday-row">
          {#each [0, 1, 2, 3, 4, 5, 6] as i}
            <div class="weekday-cell" class:weekend={i >= 5}>{getWeekday(i)}</div>
          {/each}
        </div>

        <div class="days-grid">
          {#each calendarDays as day, i}
            <button
              class="day-cell"
              class:other-month={!day.isCurrentMonth}
              class:today={isToday(day.date)}
              class:has-events={day.events.length > 0}
              onclick={() => openDayView(day)}
              style="--delay: {Math.floor(i / 7) * 0.02}s"
            >
              <span class="day-number">{day.date.getDate()}</span>

              {#if day.events.length > 0}
                <div class="day-events">
                  {#each day.events.slice(0, 2) as event}
                    <div class="event-dot" style="background-color: {event.color || '#3b82f6'}"></div>
                  {/each}
                  {#if day.events.length > 2}
                    <span class="event-count">+{day.events.length - 2}</span>
                  {/if}
                </div>
              {/if}
            </button>
          {/each}
        </div>
      </div>
    </div>

    <aside class="sidebar-panel">
      <div class="panel-section">
        <h3 class="panel-title">Today</h3>
        {#if todayEvents.length === 0}
          <p class="panel-empty">No events today</p>
        {:else}
          <div class="event-list">
            {#each todayEvents as event}
              <button class="event-card" onclick={() => openEditEvent(event)}>
                <div class="event-color" style="background-color: {event.color || '#3b82f6'}"></div>
                <div class="event-info">
                  <span class="event-title">{event.title}</span>
                  <span class="event-time">
                    {#if event.all_day}
                      All day
                    {:else}
                      {formatEventTime(event.start_datetime)}
                    {/if}
                  </span>
                </div>
              </button>
            {/each}
          </div>
        {/if}
      </div>

      <div class="panel-section">
        <h3 class="panel-title">Upcoming</h3>
        {#if upcomingEvents.length === 0}
          <p class="panel-empty">No upcoming events</p>
        {:else}
          <div class="event-list">
            {#each upcomingEvents as event}
              <button class="event-card compact" onclick={() => openEditEvent(event)}>
                <div class="event-color" style="background-color: {event.color || '#3b82f6'}"></div>
                <div class="event-info">
                  <span class="event-title">{event.title}</span>
                  <span class="event-date">
                    {new Date(event.start_datetime).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                  </span>
                </div>
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </aside>
  </div>
</div>

{#if viewingDay}
  <div class="modal-backdrop" onclick={() => viewingDay = null} role="button" tabindex="-1" onkeydown={(e) => e.key === 'Escape' && (viewingDay = null)}>
    <div class="day-modal" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      <header class="day-modal-header">
        <h2>{formatFullDate(viewingDay.date)}</h2>
        <div class="day-modal-actions">
          <button class="btn-add-small" onclick={() => openNewEvent(viewingDay.date)}>+ Add</button>
          <button class="modal-close" onclick={() => viewingDay = null} aria-label="Close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </header>
      <div class="day-modal-body">
        {#each viewingDay.events as event}
          <button class="day-event-card" onclick={() => openEditEvent(event)}>
            <div class="day-event-color" style="background-color: {event.color || '#3b82f6'}"></div>
            <div class="day-event-content">
              <span class="day-event-title">{event.title}</span>
              {#if event.description}
                <p class="day-event-desc">{event.description}</p>
              {/if}
              <span class="day-event-time">
                {#if event.all_day}
                  All day
                {:else}
                  {formatEventTime(event.start_datetime)}{event.end_datetime ? ` - ${formatEventTime(event.end_datetime)}` : ""}
                {/if}
              </span>
            </div>
          </button>
        {/each}
      </div>
    </div>
  </div>
{/if}

{#if showForm}
  <div class="modal-backdrop" onclick={resetForm} role="button" tabindex="-1" onkeydown={(e) => e.key === 'Escape' && resetForm()}>
    <div class="modal" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      <header class="modal-header">
        <h2>{editingEvent ? "Edit Event" : "New Event"}</h2>
        <button class="modal-close" onclick={resetForm} aria-label="Close">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </header>

      <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
        <div class="form-body">
          <div class="form-field">
            <input
              id="title"
              type="text"
              bind:value={form.title}
              required
              placeholder="Event title"
              class="input-title"
            />
          </div>

          <div class="form-field">
            <label>Type</label>
            <div class="type-select">
              {#each eventTypes as type}
                <button
                  type="button"
                  class="type-option"
                  class:selected={form.event_type === type.value}
                  onclick={() => form.event_type = type.value}
                >
                  {type.label}
                </button>
              {/each}
            </div>
          </div>

          <div class="form-field">
            <label class="toggle-label">
              <input type="checkbox" bind:checked={form.all_day} />
              <span class="toggle-track">
                <span class="toggle-thumb"></span>
              </span>
              <span>All day</span>
            </label>
          </div>

          <div class="form-row">
            <div class="form-field">
              <label for="start">Start</label>
              <input id="start" type={form.all_day ? "date" : "datetime-local"} bind:value={form.start_datetime} required />
            </div>
            {#if !form.all_day}
              <div class="form-field">
                <label for="end">End</label>
                <input id="end" type="datetime-local" bind:value={form.end_datetime} />
              </div>
            {/if}
          </div>

          <div class="form-field">
            <label for="description">Notes</label>
            <textarea id="description" bind:value={form.description} placeholder="Add details..." rows="2"></textarea>
          </div>

          <div class="form-field">
            <label for="client">Client</label>
            <select id="client" bind:value={form.client_id}>
              <option value={null}>None</option>
              {#each clients as client}
                <option value={client.id}>{client.name}</option>
              {/each}
            </select>
          </div>

          <div class="form-field">
            <label>Color</label>
            <div class="color-select">
              {#each colors as color}
                <button
                  type="button"
                  class="color-option"
                  class:selected={form.color === color.value}
                  style="background-color: {color.value}"
                  onclick={() => form.color = color.value}
                  aria-label={color.name}
                >
                  {#if form.color === color.value}
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  {/if}
                </button>
              {/each}
            </div>
          </div>
        </div>

        <footer class="modal-footer">
          {#if editingEvent}
            <button type="button" class="btn-delete" onclick={handleDelete}>Delete</button>
          {/if}
          <div class="spacer"></div>
          <button type="button" class="btn-cancel" onclick={resetForm}>Cancel</button>
          <button type="submit" class="btn-submit">{editingEvent ? "Save" : "Create"}</button>
        </footer>
      </form>
    </div>
  </div>
{/if}

<style>
  .page {
    animation: fadeIn 0.4s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .page-header {
    margin-bottom: 1.5rem;
  }

  .header-main {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .month-nav {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .nav-arrow {
    width: 36px;
    height: 36px;
    background: var(--color-surface);
    color: var(--color-text-secondary);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    transition: all 0.15s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }

  .nav-arrow:hover {
    background: var(--color-bg);
    color: var(--color-text);
  }

  .month-display {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    min-width: 180px;
    justify-content: center;
  }

  .month-name {
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--color-text);
  }

  .year {
    font-size: 1.125rem;
    color: var(--color-text-muted);
    font-weight: 500;
  }

  .header-actions {
    display: flex;
    gap: 0.75rem;
  }

  .btn-today {
    background: var(--color-surface);
    color: var(--color-text);
    padding: 0.625rem 1rem;
    font-weight: 500;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    transition: all 0.15s ease;
  }

  .btn-today:hover {
    background: var(--color-bg);
  }

  .btn-add {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: var(--color-text);
    color: var(--color-surface);
    padding: 0.625rem 1.25rem;
    font-weight: 600;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
    transition: all 0.2s ease;
  }

  .btn-add:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.18);
  }

  .calendar-layout {
    display: grid;
    grid-template-columns: 1fr 280px;
    gap: 1.5rem;
  }

  .calendar-main {
    background: var(--color-surface);
    border-radius: 16px;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }

  .weekday-row {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    margin-bottom: 0.5rem;
  }

  .weekday-cell {
    text-align: center;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-secondary);
    padding: 0.5rem 0;
  }

  .weekday-cell.weekend {
    color: var(--color-text-muted);
  }

  .days-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 2px;
  }

  .day-cell {
    background: transparent;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: 0.5rem 0.25rem;
    min-height: 72px;
    cursor: pointer;
    transition: all 0.15s ease;
    animation: dayFadeIn 0.3s ease backwards;
    animation-delay: var(--delay);
    position: relative;
  }

  @keyframes dayFadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .day-cell:hover {
    background: var(--color-bg);
  }

  .day-cell.other-month .day-number {
    color: var(--color-text-muted);
    opacity: 0.5;
  }

  .day-cell.today {
    background: var(--color-primary-light);
  }

  .day-cell.today .day-number {
    background: var(--color-primary);
    color: white;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
  }

  .day-number {
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--color-text);
    line-height: 24px;
  }

  .day-events {
    display: flex;
    gap: 3px;
    margin-top: 4px;
    align-items: center;
  }

  .event-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }

  .event-count {
    font-size: 0.625rem;
    color: var(--color-text-muted);
    font-weight: 500;
  }

  .sidebar-panel {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .panel-section {
    background: var(--color-surface);
    border-radius: 16px;
    padding: 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }

  .panel-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-secondary);
    margin: 0 0 1rem;
  }

  .panel-empty {
    font-size: 0.875rem;
    color: var(--color-text-muted);
    margin: 0;
  }

  .event-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .event-card {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: var(--color-bg);
    border-radius: 10px;
    text-align: left;
    width: 100%;
    transition: all 0.15s ease;
  }

  .event-card:hover {
    background: var(--color-border-light);
  }

  .event-card.compact {
    padding: 0.625rem 0.75rem;
  }

  .event-color {
    width: 4px;
    height: 32px;
    border-radius: 2px;
    flex-shrink: 0;
  }

  .event-card.compact .event-color {
    height: 24px;
  }

  .event-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .event-title {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--color-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .event-time,
  .event-date {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }

  /* Day View Modal */
  .day-modal {
    background: var(--color-surface);
    border-radius: 16px;
    width: 100%;
    max-width: 400px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    animation: modalSlide 0.3s ease;
    overflow: hidden;
  }

  .day-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .day-modal-header h2 {
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
  }

  .day-modal-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .btn-add-small {
    background: var(--color-bg);
    color: var(--color-text);
    padding: 0.375rem 0.75rem;
    font-size: 0.8125rem;
    font-weight: 500;
    border-radius: 6px;
    transition: all 0.15s ease;
  }

  .btn-add-small:hover {
    background: var(--color-border-light);
  }

  .day-modal-body {
    padding: 1rem 1.5rem 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-height: 400px;
    overflow-y: auto;
  }

  .day-event-card {
    display: flex;
    gap: 0.75rem;
    padding: 0.875rem;
    background: var(--color-bg);
    border-radius: 10px;
    text-align: left;
    width: 100%;
    transition: all 0.15s ease;
  }

  .day-event-card:hover {
    background: var(--color-border-light);
  }

  .day-event-color {
    width: 4px;
    border-radius: 2px;
    flex-shrink: 0;
  }

  .day-event-content {
    flex: 1;
    min-width: 0;
  }

  .day-event-title {
    display: block;
    font-weight: 500;
    color: var(--color-text);
    margin-bottom: 0.25rem;
  }

  .day-event-desc {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
    margin: 0 0 0.375rem;
    line-height: 1.4;
  }

  .day-event-time {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }

  /* Form Modal */
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
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
    border-radius: 16px;
    width: 100%;
    max-width: 480px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    animation: modalSlide 0.3s ease;
    overflow: hidden;
  }

  @keyframes modalSlide {
    from {
      opacity: 0;
      transform: translateY(20px) scale(0.98);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .modal-header h2 {
    font-size: 1.125rem;
    font-weight: 600;
    margin: 0;
  }

  .modal-close {
    width: 32px;
    height: 32px;
    background: transparent;
    color: var(--color-text-muted);
    border-radius: 8px;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
  }

  .modal-close:hover {
    background: var(--color-bg);
    color: var(--color-text);
  }

  .form-body {
    padding: 1.5rem;
  }

  .form-field {
    margin-bottom: 1rem;
  }

  .form-field label {
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-secondary);
    margin-bottom: 0.5rem;
  }

  .input-title {
    font-size: 1.0625rem;
    font-weight: 500;
    padding: 0.875rem 1rem;
    border: 1px solid var(--color-border);
    border-radius: 10px;
  }

  .input-title:focus {
    border-color: var(--color-text);
    box-shadow: none;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .type-select {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .type-option {
    padding: 0.5rem 0.875rem;
    background: var(--color-bg);
    border: 1px solid transparent;
    border-radius: 8px;
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--color-text-secondary);
    transition: all 0.15s ease;
  }

  .type-option:hover {
    border-color: var(--color-border);
  }

  .type-option.selected {
    background: var(--color-surface);
    border-color: var(--color-text);
    color: var(--color-text);
  }

  .toggle-label {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    cursor: pointer;
    font-size: 0.9375rem;
    color: var(--color-text);
    font-weight: 400;
  }

  .toggle-label input {
    display: none;
  }

  .toggle-track {
    width: 44px;
    height: 24px;
    background: var(--color-border);
    border-radius: 12px;
    position: relative;
    transition: background 0.2s ease;
  }

  .toggle-label input:checked + .toggle-track {
    background: var(--color-primary);
  }

  .toggle-thumb {
    position: absolute;
    top: 2px;
    left: 2px;
    width: 20px;
    height: 20px;
    background: white;
    border-radius: 50%;
    transition: transform 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  }

  .toggle-label input:checked + .toggle-track .toggle-thumb {
    transform: translateX(20px);
  }

  .color-select {
    display: flex;
    gap: 0.625rem;
  }

  .color-option {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: 2px solid transparent;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    padding: 0;
  }

  .color-option:hover {
    transform: scale(1.1);
  }

  .color-option.selected {
    border-color: var(--color-text);
    box-shadow: 0 0 0 2px var(--color-surface);
  }

  .modal-footer {
    display: flex;
    gap: 0.75rem;
    padding: 1rem 1.5rem;
    background: var(--color-bg);
    border-top: 1px solid var(--color-border-light);
  }

  .spacer {
    flex: 1;
  }

  .btn-cancel {
    background: transparent;
    color: var(--color-text-secondary);
    padding: 0.625rem 1.25rem;
    font-weight: 500;
  }

  .btn-cancel:hover {
    color: var(--color-text);
  }

  .btn-submit {
    background: var(--color-text);
    color: var(--color-surface);
    padding: 0.625rem 1.5rem;
    font-weight: 600;
    border-radius: 8px;
    transition: all 0.2s ease;
  }

  .btn-submit:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }

  .btn-delete {
    background: transparent;
    color: #dc2626;
    padding: 0.625rem 1rem;
    font-weight: 500;
  }

  .btn-delete:hover {
    background: #fee2e2;
  }

  @media (max-width: 900px) {
    .calendar-layout {
      grid-template-columns: 1fr;
    }

    .sidebar-panel {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }
  }

  @media (max-width: 640px) {
    .month-display {
      min-width: 140px;
    }

    .month-name {
      font-size: 1.25rem;
    }

    .btn-add-text {
      display: none;
    }

    .btn-add {
      padding: 0.625rem 0.875rem;
    }

    .sidebar-panel {
      grid-template-columns: 1fr;
    }

    .day-cell {
      padding: 0.25rem;
    }

    .day-number {
      font-size: 0.8125rem;
    }

    .form-row {
      grid-template-columns: 1fr;
    }
  }
</style>
