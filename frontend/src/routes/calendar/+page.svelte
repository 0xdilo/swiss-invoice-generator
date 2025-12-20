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

<div class="animate-fade-in">
  <header class="mb-6">
    <div class="flex justify-between items-center">
      <div class="flex items-center gap-3">
        <button class="w-9 h-9 bg-surface text-text-secondary rounded-[10px] flex items-center justify-center p-0 transition-all duration-150 shadow-sm hover:bg-bg hover:text-text" onclick={prevMonth} aria-label="Previous month">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <div class="flex items-baseline gap-2 min-w-[180px] justify-center">
          <span class="text-2xl font-bold tracking-tight text-text">{currentMonth}</span>
          <span class="text-lg text-text-muted font-medium">{currentYear}</span>
        </div>
        <button class="w-9 h-9 bg-surface text-text-secondary rounded-[10px] flex items-center justify-center p-0 transition-all duration-150 shadow-sm hover:bg-bg hover:text-text" onclick={nextMonth} aria-label="Next month">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
      </div>

      <div class="flex gap-3">
        <button class="bg-surface text-text px-4 py-2.5 font-medium rounded-[10px] shadow-sm transition-all duration-150 hover:bg-bg" onclick={goToToday}>Today</button>
        <button class="flex items-center gap-2 bg-text text-surface px-5 py-2.5 font-semibold rounded-[10px] shadow-md transition-all duration-200 hover:-translate-y-px hover:shadow-lg" onclick={() => openNewEvent()}>
          <span>+</span>
          <span class="max-sm:hidden">New Event</span>
        </button>
      </div>
    </div>
  </header>

  <div class="grid grid-cols-[1fr_280px] gap-6 max-[900px]:grid-cols-1">
    <div class="bg-surface rounded-2xl p-4 shadow-sm">
      <div class="mb-2">
        <div class="grid grid-cols-7 mb-2">
          {#each [0, 1, 2, 3, 4, 5, 6] as i}
            <div class="text-center text-[11px] font-semibold uppercase tracking-wider py-2 {i >= 5 ? 'text-text-muted' : 'text-text-secondary'}">{getWeekday(i)}</div>
          {/each}
        </div>

        <div class="grid grid-cols-7 gap-0.5">
          {#each calendarDays as day, i}
            <button
              class="bg-transparent rounded-lg flex flex-col items-center justify-start px-1 py-2 min-h-[72px] cursor-pointer transition-all duration-150 relative max-sm:px-0 max-sm:py-1 {!day.isCurrentMonth ? 'opacity-50' : ''} {isToday(day.date) ? 'bg-primary-light' : ''} hover:bg-bg"
              onclick={() => openDayView(day)}
              style="animation: dayFadeIn 0.3s ease backwards; animation-delay: {Math.floor(i / 7) * 0.02}s;"
            >
              <span class="text-[13px] font-medium leading-6 {isToday(day.date) ? 'bg-primary text-white rounded-full w-6 h-6 flex items-center justify-center font-semibold' : 'text-text'} {!day.isCurrentMonth ? 'text-text-muted opacity-50' : ''}">{day.date.getDate()}</span>

              {#if day.events.length > 0}
                <div class="flex gap-[3px] mt-1 items-center">
                  {#each day.events.slice(0, 2) as event}
                    <div class="w-1.5 h-1.5 rounded-full" style="background-color: {event.color || '#3b82f6'}"></div>
                  {/each}
                  {#if day.events.length > 2}
                    <span class="text-[10px] text-text-muted font-medium">+{day.events.length - 2}</span>
                  {/if}
                </div>
              {/if}
            </button>
          {/each}
        </div>
      </div>
    </div>

    <aside class="flex flex-col gap-6 max-[900px]:grid max-[900px]:grid-cols-2 max-[900px]:gap-4 max-sm:grid-cols-1">
      <div class="bg-surface rounded-2xl p-5 shadow-sm">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-text-secondary m-0 mb-4">Today</h3>
        {#if todayEvents.length === 0}
          <p class="text-sm text-text-muted m-0">No events today</p>
        {:else}
          <div class="flex flex-col gap-2">
            {#each todayEvents as event}
              <button class="flex items-center gap-3 p-3 bg-bg rounded-[10px] text-left w-full transition-all duration-150 hover:bg-border-light" onclick={() => openEditEvent(event)}>
                <div class="w-1 h-8 rounded-sm flex-shrink-0" style="background-color: {event.color || '#3b82f6'}"></div>
                <div class="flex-1 min-w-0 flex flex-col gap-0.5">
                  <span class="text-sm font-medium text-text whitespace-nowrap overflow-hidden text-ellipsis">{event.title}</span>
                  <span class="text-xs text-text-muted">
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

      <div class="bg-surface rounded-2xl p-5 shadow-sm">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-text-secondary m-0 mb-4">Upcoming</h3>
        {#if upcomingEvents.length === 0}
          <p class="text-sm text-text-muted m-0">No upcoming events</p>
        {:else}
          <div class="flex flex-col gap-2">
            {#each upcomingEvents as event}
              <button class="flex items-center gap-3 py-2.5 px-3 bg-bg rounded-[10px] text-left w-full transition-all duration-150 hover:bg-border-light" onclick={() => openEditEvent(event)}>
                <div class="w-1 h-6 rounded-sm flex-shrink-0" style="background-color: {event.color || '#3b82f6'}"></div>
                <div class="flex-1 min-w-0 flex flex-col gap-0.5">
                  <span class="text-sm font-medium text-text whitespace-nowrap overflow-hidden text-ellipsis">{event.title}</span>
                  <span class="text-xs text-text-muted">
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
    <div class="bg-surface rounded-2xl w-full max-w-[400px] shadow-2xl animate-modal-slide overflow-hidden" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      <header class="flex justify-between items-center px-6 py-5 border-b border-border-light">
        <h2 class="text-base font-semibold m-0">{formatFullDate(viewingDay.date)}</h2>
        <div class="flex gap-2 items-center">
          <button class="bg-bg text-text px-3 py-1.5 text-[13px] font-medium rounded-md transition-all duration-150 hover:bg-border-light" onclick={() => openNewEvent(viewingDay.date)}>+ Add</button>
          <button class="w-8 h-8 bg-transparent text-text-muted rounded-lg p-0 flex items-center justify-center transition-all duration-150 hover:bg-bg hover:text-text" onclick={() => viewingDay = null} aria-label="Close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </header>
      <div class="px-6 pt-4 pb-6 flex flex-col gap-2 max-h-[400px] overflow-y-auto">
        {#each viewingDay.events as event}
          <button class="flex gap-3 p-3.5 bg-bg rounded-[10px] text-left w-full transition-all duration-150 hover:bg-border-light" onclick={() => openEditEvent(event)}>
            <div class="w-1 rounded-sm flex-shrink-0" style="background-color: {event.color || '#3b82f6'}"></div>
            <div class="flex-1 min-w-0">
              <span class="block font-medium text-text mb-1">{event.title}</span>
              {#if event.description}
                <p class="text-[13px] text-text-secondary m-0 mb-1.5 leading-relaxed">{event.description}</p>
              {/if}
              <span class="text-xs text-text-muted">
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
    <div class="modal max-w-[480px]" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      <header class="modal-header">
        <h2 class="text-lg font-semibold m-0">{editingEvent ? "Edit Event" : "New Event"}</h2>
        <button class="w-8 h-8 bg-transparent text-text-muted rounded-lg p-0 flex items-center justify-center transition-all duration-150 hover:bg-bg hover:text-text" onclick={resetForm} aria-label="Close">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </header>

      <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
        <div class="p-6">
          <div class="mb-4">
            <input
              id="title"
              type="text"
              bind:value={form.title}
              required
              placeholder="Event title"
              class="w-full text-[17px] font-medium px-4 py-3.5 border border-border rounded-[10px] transition-all duration-150 focus:border-text focus:shadow-none focus:outline-none"
            />
          </div>

          <div class="mb-4">
            <label class="form-label">Type</label>
            <div class="flex gap-2 flex-wrap">
              {#each eventTypes as type}
                <button
                  type="button"
                  class="px-3.5 py-2 bg-bg border border-transparent rounded-lg text-[13px] font-medium text-text-secondary transition-all duration-150 hover:border-border {form.event_type === type.value ? 'bg-surface border-text text-text' : ''}"
                  onclick={() => form.event_type = type.value}
                >
                  {type.label}
                </button>
              {/each}
            </div>
          </div>

          <div class="mb-4">
            <label class="flex items-center gap-3 cursor-pointer text-[15px] text-text">
              <input type="checkbox" bind:checked={form.all_day} class="hidden" />
              <span class="w-11 h-6 rounded-xl relative transition-colors duration-200 {form.all_day ? 'bg-primary' : 'bg-border'}">
                <span class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-200 {form.all_day ? 'translate-x-5' : ''}"></span>
              </span>
              <span>All day</span>
            </label>
          </div>

          <div class="grid grid-cols-2 gap-4 mb-4 max-sm:grid-cols-1">
            <div>
              <label for="start" class="form-label">Start</label>
              <input id="start" type={form.all_day ? "date" : "datetime-local"} bind:value={form.start_datetime} required class="form-input" />
            </div>
            {#if !form.all_day}
              <div>
                <label for="end" class="form-label">End</label>
                <input id="end" type="datetime-local" bind:value={form.end_datetime} class="form-input" />
              </div>
            {/if}
          </div>

          <div class="mb-4">
            <label for="description" class="form-label">Notes</label>
            <textarea id="description" bind:value={form.description} placeholder="Add details..." rows="2" class="form-input resize-none"></textarea>
          </div>

          <div class="mb-4">
            <label for="client" class="form-label">Client</label>
            <select id="client" bind:value={form.client_id} class="form-input">
              <option value={null}>None</option>
              {#each clients as client}
                <option value={client.id}>{client.name}</option>
              {/each}
            </select>
          </div>

          <div class="mb-4">
            <label class="form-label">Color</label>
            <div class="flex gap-2.5">
              {#each colors as color}
                <button
                  type="button"
                  class="w-8 h-8 rounded-full border-2 border-transparent cursor-pointer transition-all duration-150 flex items-center justify-center text-white p-0 hover:scale-110 {form.color === color.value ? 'border-text shadow-[0_0_0_2px_var(--color-surface)]' : ''}"
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
            <button type="button" class="bg-transparent text-danger px-4 py-2.5 font-medium hover:bg-danger-light" onclick={handleDelete}>Delete</button>
          {/if}
          <div class="flex-1"></div>
          <button type="button" class="btn-cancel" onclick={resetForm}>Cancel</button>
          <button type="submit" class="bg-text text-surface px-6 py-2.5 font-semibold rounded-lg transition-all duration-200 hover:-translate-y-px hover:shadow-lg">{editingEvent ? "Save" : "Create"}</button>
        </footer>
      </form>
    </div>
  </div>
{/if}

<style>
  @keyframes dayFadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
</style>
