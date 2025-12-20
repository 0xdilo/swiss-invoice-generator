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

<div class="max-w-3xl mx-auto animate-fade-in">
  <header class="mb-8">
    <div class="flex justify-between items-start gap-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight mb-2">Tasks</h1>
        <div class="flex gap-4 text-sm text-text-muted">
          <span>{stats.pending} pending</span>
          {#if stats.high > 0}
            <span class="text-red-600 font-medium">{stats.high} urgent</span>
          {/if}
          {#if stats.overdue > 0}
            <span class="text-red-600">{stats.overdue} overdue</span>
          {/if}
        </div>
      </div>
      <button
        class="flex items-center gap-2.5 bg-text text-surface px-5 py-3 rounded-xl font-semibold text-sm
               shadow-md hover:-translate-y-px hover:shadow-lg transition-all duration-200"
        onclick={() => showForm = true}
      >
        <span class="text-lg font-normal">+</span>
        <span class="max-sm:hidden">New Task</span>
      </button>
    </div>
  </header>

  <div class="mb-6 border-b border-border-light">
    <div class="flex">
      <button
        class="relative bg-transparent px-0 py-3 mr-8 font-medium text-[15px] flex items-center gap-2 rounded-none transition-colors
               {filter === 'all' ? 'text-text' : 'text-text-secondary hover:text-text'}"
        onclick={() => filter = "all"}
      >
        Active
        <span class="text-xs px-2 py-0.5 rounded-full {filter === 'all' ? 'bg-text text-surface' : 'bg-border-light text-text-secondary'}">
          {todos.filter(t => t.status !== "completed").length}
        </span>
        {#if filter === 'all'}
          <span class="absolute bottom-0 left-0 right-0 h-0.5 bg-text"></span>
        {/if}
      </button>
      <button
        class="relative bg-transparent px-0 py-3 mr-8 font-medium text-[15px] flex items-center gap-2 rounded-none transition-colors
               {filter === 'completed' ? 'text-text' : 'text-text-secondary hover:text-text'}"
        onclick={() => filter = "completed"}
      >
        Done
        <span class="text-xs px-2 py-0.5 rounded-full {filter === 'completed' ? 'bg-text text-surface' : 'bg-border-light text-text-secondary'}">
          {stats.completed}
        </span>
        {#if filter === 'completed'}
          <span class="absolute bottom-0 left-0 right-0 h-0.5 bg-text"></span>
        {/if}
      </button>
    </div>
  </div>

  <main class="min-h-[300px]">
    {#if filteredTodos.length === 0}
      <div class="text-center py-16 px-8">
        <div class="w-16 h-16 mx-auto mb-6 bg-bg rounded-2xl flex items-center justify-center text-text-muted">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M9 11l3 3L22 4"/>
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
          </svg>
        </div>
        <p class="text-lg font-semibold mb-2">{filter === "completed" ? "No completed tasks yet" : "All clear"}</p>
        <p class="text-text-secondary">{filter === "completed" ? "Complete some tasks to see them here" : "Add a task to get started"}</p>
      </div>
    {:else}
      <ul class="flex flex-col gap-0.5">
        {#each filteredTodos as todo, i (todo.id)}
          {@const daysUntil = getDaysUntil(todo.due_date)}
          <li
            class="group flex items-start gap-4 p-4 bg-surface rounded-xl transition-all duration-200 animate-slide-in relative
                   hover:shadow-md
                   {completingId === todo.id ? 'scale-[1.02] bg-green-50' : ''}
                   {todo.status === 'completed' ? 'opacity-55' : ''}"
            style="animation-delay: {i * 0.03}s"
          >
            {#if todo.priority === 'high' && todo.status !== 'completed'}
              <span class="absolute left-0 top-0 bottom-0 w-[3px] bg-red-600 rounded-l-xl"></span>
            {/if}
            {#if isOverdue(todo)}
              <span class="absolute left-0 top-0 bottom-0 w-[3px] bg-red-600 rounded-l-xl"></span>
            {/if}

            <button
              class="relative w-[22px] h-[22px] border-2 rounded-md bg-transparent flex-shrink-0 mt-0.5
                     flex items-center justify-center transition-all duration-200
                     {todo.status === 'completed'
                       ? 'bg-success border-success'
                       : 'border-border hover:border-primary hover:bg-primary-light'}"
              onclick={() => toggleComplete(todo)}
            >
              <svg
                class="w-3 h-3 transition-all duration-200
                       {todo.status === 'completed' ? 'opacity-100 scale-100 stroke-white' : 'opacity-0 scale-50 stroke-primary'}"
                viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"
              >
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </button>

            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="font-medium text-[15px] {todo.status === 'completed' ? 'line-through text-text-secondary' : 'text-text'}">
                  {todo.title}
                </span>
                {#if todo.priority === "high" && todo.status !== 'completed'}
                  <span class="w-1.5 h-1.5 bg-red-600 rounded-full flex-shrink-0"></span>
                {/if}
              </div>

              {#if todo.description}
                <p class="text-sm text-text-secondary leading-relaxed mb-2">{todo.description}</p>
              {/if}

              <div class="flex gap-2 flex-wrap">
                {#if todo.due_date}
                  <span class="text-xs px-2.5 py-1 rounded font-medium
                               {isOverdue(todo) ? 'bg-red-100 text-red-600' :
                                daysUntil === 0 ? 'bg-blue-100 text-blue-700' :
                                isDueSoon(todo) ? 'bg-amber-100 text-amber-700' :
                                'bg-bg text-text-secondary'}">
                    {formatDate(todo.due_date)}
                  </span>
                {/if}
                {#if todo.client_name}
                  <span class="text-xs px-2.5 py-1 rounded border border-border text-text-muted">
                    {todo.client_name}
                  </span>
                {/if}
              </div>
            </div>

            <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity max-sm:opacity-100">
              <button
                class="w-8 h-8 bg-transparent text-text-muted rounded-md flex items-center justify-center
                       hover:bg-bg hover:text-text transition-all"
                onclick={() => editTodo(todo)}
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
              <button
                class="w-8 h-8 bg-transparent text-text-muted rounded-md flex items-center justify-center
                       hover:bg-red-100 hover:text-red-600 transition-all"
                onclick={() => handleDelete(todo.id)}
              >
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
  <div
    class="modal-backdrop"
    onclick={resetForm}
    role="button"
    tabindex="-1"
    onkeydown={(e) => e.key === 'Escape' && resetForm()}
  >
    <div class="modal max-w-md" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      <header class="modal-header">
        <h2 class="text-lg font-semibold">{editingTodo ? "Edit Task" : "New Task"}</h2>
        <button
          class="w-8 h-8 bg-transparent text-text-muted rounded-lg flex items-center justify-center
                 hover:bg-bg hover:text-text transition-all"
          onclick={resetForm}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </header>

      <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
        <div class="modal-body">
          <div class="mb-4">
            <input
              type="text"
              bind:value={form.title}
              required
              placeholder="What needs to be done?"
              class="form-input text-lg font-medium py-3.5"
            />
          </div>

          <div class="mb-4">
            <textarea
              bind:value={form.description}
              placeholder="Add notes..."
              rows="3"
              class="form-input resize-none"
            ></textarea>
          </div>

          <div class="grid grid-cols-2 gap-4 mb-4 max-sm:grid-cols-1">
            <div>
              <label class="form-label">Due date</label>
              <input type="date" bind:value={form.due_date} class="form-input" />
            </div>

            <div>
              <label class="form-label">Priority</label>
              <div class="flex gap-2">
                {#each ["low", "medium", "high"] as p}
                  <button
                    type="button"
                    class="flex-1 py-2 px-2 rounded-md text-xs font-semibold uppercase tracking-wide transition-all
                           {form.priority === p
                             ? (p === 'high' ? 'bg-red-100 border-red-600 text-red-600' : 'bg-surface border-text text-text')
                             : 'bg-bg border-transparent text-text-secondary hover:border-border'}
                           border"
                    onclick={() => form.priority = p}
                  >
                    {p}
                  </button>
                {/each}
              </div>
            </div>
          </div>

          <div>
            <label class="form-label">Client</label>
            <select bind:value={form.client_id} class="form-input">
              <option value={null}>None</option>
              {#each clients as client}
                <option value={client.id}>{client.name}</option>
              {/each}
            </select>
          </div>
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn-cancel" onclick={resetForm}>Cancel</button>
          <button type="submit" class="btn-primary">{editingTodo ? "Save Changes" : "Add Task"}</button>
        </footer>
      </form>
    </div>
  </div>
{/if}
