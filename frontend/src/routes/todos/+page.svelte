<script>
  import { onMount } from "svelte";
  import { getTodos, createTodo, updateTodo, deleteTodo, getClients } from "$lib/api.js";

  let todos = [];
  let clients = [];
  let filter = "all";
  let showForm = false;
  let editingTodo = null;
  let completingId = null;
  let form = {
    title: "",
    description: "",
    due_date: "",
    priority: "medium",
    client_id: null
  };

  async function load() {
    [todos, clients] = await Promise.all([getTodos(), getClients()]);
  }

  onMount(load);

  $: filteredTodos = todos.filter(t => {
    if (filter === "all") return t.status !== "completed";
    if (filter === "completed") return t.status === "completed";
    return true;
  });

  $: pendingTodos = filteredTodos.filter(t => t.status === "pending");
  $: completedTodos = filteredTodos.filter(t => t.status === "completed");

  $: stats = {
    total: todos.length,
    pending: todos.filter(t => t.status === "pending").length,
    high: todos.filter(t => t.priority === "high" && t.status === "pending").length,
    completed: todos.filter(t => t.status === "completed").length,
    overdue: todos.filter(t => isOverdue(t)).length
  };

  async function handleSubmit() {
    if (editingTodo) {
      await updateTodo(editingTodo.id, form);
    } else {
      await createTodo(form);
    }
    resetForm();
    await load();
  }

  async function toggleComplete(todo) {
    if (todo.status === "completed") {
      await updateTodo(todo.id, { ...todo, status: "pending" });
      await load();
    } else {
      completingId = todo.id;
      await new Promise(r => setTimeout(r, 600));
      await updateTodo(todo.id, { ...todo, status: "completed" });
      completingId = null;
      await load();
    }
  }

  async function handleDelete(id) {
    if (confirm("Delete this task?")) {
      await deleteTodo(id);
      await load();
    }
  }

  function editTodo(todo) {
    editingTodo = todo;
    form = {
      title: todo.title,
      description: todo.description || "",
      due_date: todo.due_date || "",
      priority: todo.priority,
      client_id: todo.client_id
    };
    showForm = true;
  }

  function resetForm() {
    showForm = false;
    editingTodo = null;
    form = { title: "", description: "", due_date: "", priority: "medium", client_id: null };
  }

  function formatDate(dateStr) {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) return "Today";
    if (date.toDateString() === tomorrow.toDateString()) return "Tomorrow";

    return date.toLocaleDateString("de-CH", { day: "numeric", month: "short" });
  }

  function isOverdue(todo) {
    if (!todo.due_date || todo.status === "completed") return false;
    const due = new Date(todo.due_date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return due < today;
  }

  function isDueSoon(todo) {
    if (!todo.due_date || todo.status === "completed") return false;
    const due = new Date(todo.due_date);
    const now = new Date();
    const diffDays = Math.ceil((due - now) / (1000 * 60 * 60 * 24));
    return diffDays >= 0 && diffDays <= 3;
  }

  function getDaysUntil(dateStr) {
    if (!dateStr) return null;
    const due = new Date(dateStr);
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    due.setHours(0, 0, 0, 0);
    return Math.ceil((due - now) / (1000 * 60 * 60 * 24));
  }
</script>

<div class="page">
  <header class="page-header">
    <div class="header-content">
      <div class="title-block">
        <h1>Tasks</h1>
        <div class="stats-inline">
          <span class="stat">{stats.pending} pending</span>
          {#if stats.high > 0}
            <span class="stat urgent">{stats.high} urgent</span>
          {/if}
          {#if stats.overdue > 0}
            <span class="stat overdue">{stats.overdue} overdue</span>
          {/if}
        </div>
      </div>
      <button class="btn-add" onclick={() => showForm = true}>
        <span class="btn-add-icon">+</span>
        <span class="btn-add-text">New Task</span>
      </button>
    </div>
  </header>

  <div class="filters-bar">
    <div class="filter-tabs">
      <button class:active={filter === "all"} onclick={() => filter = "all"}>
        Active
        <span class="count">{todos.filter(t => t.status !== "completed").length}</span>
      </button>
      <button class:active={filter === "completed"} onclick={() => filter = "completed"}>
        Done
        <span class="count">{stats.completed}</span>
      </button>
    </div>
  </div>

  <main class="content">
    {#if filteredTodos.length === 0}
      <div class="empty-state">
        <div class="empty-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M9 11l3 3L22 4"/>
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
          </svg>
        </div>
        <p class="empty-title">{filter === "completed" ? "No completed tasks yet" : "All clear"}</p>
        <p class="empty-subtitle">{filter === "completed" ? "Complete some tasks to see them here" : "Add a task to get started"}</p>
      </div>
    {:else}
      <ul class="task-list">
        {#each filteredTodos as todo, i (todo.id)}
          {@const daysUntil = getDaysUntil(todo.due_date)}
          <li
            class="task-item"
            class:completing={completingId === todo.id}
            class:completed={todo.status === "completed"}
            class:overdue={isOverdue(todo)}
            class:due-soon={isDueSoon(todo)}
            class:high={todo.priority === "high"}
            style="--delay: {i * 0.03}s"
          >
            <button
              class="checkbox"
              onclick={() => toggleComplete(todo)}
              aria-label={todo.status === "completed" ? "Mark as incomplete" : "Mark as complete"}
            >
              <svg class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <div class="check-ring"></div>
            </button>

            <div class="task-body">
              <div class="task-main">
                <span class="task-title">{todo.title}</span>
                {#if todo.priority === "high"}
                  <span class="priority-indicator" title="High priority"></span>
                {/if}
              </div>

              {#if todo.description}
                <p class="task-desc">{todo.description}</p>
              {/if}

              <div class="task-meta">
                {#if todo.due_date}
                  <span class="meta-tag" class:overdue={isOverdue(todo)} class:today={daysUntil === 0} class:soon={isDueSoon(todo) && !isOverdue(todo)}>
                    {formatDate(todo.due_date)}
                  </span>
                {/if}
                {#if todo.client_name}
                  <span class="meta-tag client">{todo.client_name}</span>
                {/if}
              </div>
            </div>

            <div class="task-actions">
              <button class="action-btn" onclick={() => editTodo(todo)} aria-label="Edit task">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
              <button class="action-btn delete" onclick={() => handleDelete(todo.id)} aria-label="Delete task">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </main>
</div>

{#if showForm}
  <div class="modal-backdrop" onclick={resetForm} role="button" tabindex="-1" onkeydown={(e) => e.key === 'Escape' && resetForm()}>
    <div class="modal" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      <header class="modal-header">
        <h2>{editingTodo ? "Edit Task" : "New Task"}</h2>
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
              placeholder="What needs to be done?"
              class="input-title"
            />
          </div>

          <div class="form-field">
            <textarea
              id="description"
              bind:value={form.description}
              placeholder="Add notes..."
              rows="3"
            ></textarea>
          </div>

          <div class="form-row-compact">
            <div class="form-field">
              <label for="due_date">Due date</label>
              <input id="due_date" type="date" bind:value={form.due_date} />
            </div>

            <div class="form-field">
              <label for="priority">Priority</label>
              <div class="priority-select">
                {#each ["low", "medium", "high"] as p}
                  <button
                    type="button"
                    class="priority-option {p}"
                    class:selected={form.priority === p}
                    onclick={() => form.priority = p}
                  >
                    {p}
                  </button>
                {/each}
              </div>
            </div>
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
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn-cancel" onclick={resetForm}>Cancel</button>
          <button type="submit" class="btn-submit">{editingTodo ? "Save Changes" : "Add Task"}</button>
        </footer>
      </form>
    </div>
  </div>
{/if}

<style>
  .page {
    max-width: 720px;
    margin: 0 auto;
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
  }

  .title-block h1 {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    margin-bottom: 0.5rem;
    color: var(--color-text);
  }

  .stats-inline {
    display: flex;
    gap: 1rem;
    font-size: 0.8125rem;
    color: var(--color-text-muted);
  }

  .stat {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .stat.urgent {
    color: #dc2626;
    font-weight: 500;
  }

  .stat.overdue {
    color: #dc2626;
  }

  .btn-add {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    background: var(--color-text);
    color: var(--color-surface);
    padding: 0.75rem 1.25rem;
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.875rem;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
  }

  .btn-add:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.18);
  }

  .btn-add-icon {
    font-size: 1.125rem;
    font-weight: 400;
  }

  .filters-bar {
    margin-bottom: 1.5rem;
    border-bottom: 1px solid var(--color-border-light);
    padding-bottom: 0;
  }

  .filter-tabs {
    display: flex;
    gap: 0;
  }

  .filter-tabs button {
    position: relative;
    background: transparent;
    color: var(--color-text-secondary);
    padding: 0.75rem 0;
    margin-right: 2rem;
    font-weight: 500;
    font-size: 0.9375rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    border-radius: 0;
    transition: color 0.2s ease;
  }

  .filter-tabs button::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 2px;
    background: transparent;
    transition: background 0.2s ease;
  }

  .filter-tabs button:hover {
    color: var(--color-text);
  }

  .filter-tabs button.active {
    color: var(--color-text);
  }

  .filter-tabs button.active::after {
    background: var(--color-text);
  }

  .filter-tabs .count {
    font-size: 0.75rem;
    background: var(--color-border-light);
    padding: 0.125rem 0.5rem;
    border-radius: 10px;
    color: var(--color-text-secondary);
  }

  .filter-tabs button.active .count {
    background: var(--color-text);
    color: var(--color-surface);
  }

  .content {
    min-height: 300px;
  }

  .task-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .task-item {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem 1.25rem;
    background: var(--color-surface);
    border-radius: 12px;
    transition: all 0.2s ease;
    animation: slideIn 0.3s ease backwards;
    animation-delay: var(--delay);
    position: relative;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(-12px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .task-item:hover {
    background: var(--color-surface);
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  }

  .task-item.completing {
    animation: completeTask 0.6s ease forwards;
  }

  @keyframes completeTask {
    0% { transform: scale(1); }
    30% { transform: scale(1.02); background: #dcfce7; }
    100% { transform: scale(1); opacity: 0.5; }
  }

  .task-item.completed {
    opacity: 0.55;
  }

  .task-item.completed .task-title {
    text-decoration: line-through;
    color: var(--color-text-secondary);
  }

  .task-item.high::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: #dc2626;
    border-radius: 12px 0 0 12px;
  }

  .task-item.overdue::before {
    background: #dc2626;
  }

  .checkbox {
    position: relative;
    width: 22px;
    height: 22px;
    border: 2px solid var(--color-border);
    border-radius: 6px;
    background: transparent;
    cursor: pointer;
    flex-shrink: 0;
    margin-top: 2px;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
  }

  .checkbox:hover {
    border-color: var(--color-primary);
    background: var(--color-primary-light);
  }

  .check-icon {
    width: 12px;
    height: 12px;
    opacity: 0;
    transform: scale(0.5);
    transition: all 0.2s ease;
    stroke: var(--color-primary);
  }

  .check-ring {
    position: absolute;
    inset: -4px;
    border: 2px solid var(--color-primary);
    border-radius: 10px;
    opacity: 0;
    transform: scale(0.8);
  }

  .task-item.completed .checkbox {
    background: var(--color-success);
    border-color: var(--color-success);
  }

  .task-item.completed .check-icon {
    opacity: 1;
    transform: scale(1);
    stroke: white;
  }

  .task-item.completing .check-ring {
    animation: ringPulse 0.6s ease;
  }

  @keyframes ringPulse {
    0% { opacity: 1; transform: scale(0.8); }
    100% { opacity: 0; transform: scale(1.4); }
  }

  .task-body {
    flex: 1;
    min-width: 0;
  }

  .task-main {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
  }

  .task-title {
    font-weight: 500;
    color: var(--color-text);
    font-size: 0.9375rem;
    line-height: 1.4;
  }

  .priority-indicator {
    width: 6px;
    height: 6px;
    background: #dc2626;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .task-desc {
    margin: 0.25rem 0 0.5rem;
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
    line-height: 1.5;
  }

  .task-meta {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .meta-tag {
    font-size: 0.75rem;
    padding: 0.2rem 0.6rem;
    background: var(--color-bg);
    color: var(--color-text-secondary);
    border-radius: 5px;
    font-weight: 500;
  }

  .meta-tag.today {
    background: #dbeafe;
    color: #1d4ed8;
  }

  .meta-tag.soon {
    background: #fef3c7;
    color: #92400e;
  }

  .meta-tag.overdue {
    background: #fee2e2;
    color: #dc2626;
  }

  .meta-tag.client {
    background: transparent;
    border: 1px solid var(--color-border);
    color: var(--color-text-muted);
  }

  .task-actions {
    display: flex;
    gap: 0.25rem;
    opacity: 0;
    transition: opacity 0.15s ease;
  }

  .task-item:hover .task-actions {
    opacity: 1;
  }

  .action-btn {
    width: 32px;
    height: 32px;
    background: transparent;
    color: var(--color-text-muted);
    border-radius: 6px;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
  }

  .action-btn:hover {
    background: var(--color-bg);
    color: var(--color-text);
  }

  .action-btn.delete:hover {
    background: #fee2e2;
    color: #dc2626;
  }

  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
  }

  .empty-icon {
    width: 64px;
    height: 64px;
    margin: 0 auto 1.5rem;
    background: var(--color-bg);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--color-text-muted);
  }

  .empty-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--color-text);
    margin: 0 0 0.5rem;
  }

  .empty-subtitle {
    font-size: 0.9375rem;
    color: var(--color-text-secondary);
    margin: 0;
  }

  /* Modal */
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

  .form-row-compact {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .priority-select {
    display: flex;
    gap: 0.5rem;
  }

  .priority-option {
    flex: 1;
    padding: 0.5rem;
    background: var(--color-bg);
    border: 1px solid transparent;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--color-text-secondary);
    transition: all 0.15s ease;
  }

  .priority-option:hover {
    border-color: var(--color-border);
  }

  .priority-option.selected {
    border-color: var(--color-text);
    background: var(--color-surface);
    color: var(--color-text);
  }

  .priority-option.high.selected {
    background: #fee2e2;
    border-color: #dc2626;
    color: #dc2626;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    padding: 1rem 1.5rem;
    background: var(--color-bg);
    border-top: 1px solid var(--color-border-light);
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

  @media (max-width: 640px) {
    .page {
      padding: 0 0.5rem;
    }

    .title-block h1 {
      font-size: 1.5rem;
    }

    .btn-add-text {
      display: none;
    }

    .btn-add {
      padding: 0.75rem;
    }

    .btn-add-icon {
      font-size: 1.25rem;
    }

    .task-actions {
      opacity: 1;
    }

    .form-row-compact {
      grid-template-columns: 1fr;
    }
  }
</style>
