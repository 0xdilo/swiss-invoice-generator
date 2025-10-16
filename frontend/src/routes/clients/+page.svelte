<script>
  import { onMount } from "svelte";
  import {
    getClients,
    addClient,
    updateClient,
    deleteClient,
  } from "$lib/api.js";
  let clients = [];
  let form = {
    name: "",
    address: "",
    cap: "",
    city: "",
    nation: "",
    email: "",
  };
  let editing = null;

  async function load() {
    clients = await getClients();
  }
  onMount(load);

  async function submit() {
    if (editing !== null) {
      await updateClient(editing, form);
      editing = null;
    } else {
      await addClient(form);
    }
    form = { name: "", address: "", cap: "", city: "", nation: "", email: "" };
    await load();
  }
  function edit(client) {
    editing = client.id;
    form = { ...client };
  }
  async function remove(id) {
    await deleteClient(id);
    await load();
  }
</script>

<h2>Clients</h2>
<form on:submit|preventDefault={submit} class="form">
  <div class="form-group">
    <label for="client-name">Name</label>
    <input
      id="client-name"
      placeholder="Enter client name"
      bind:value={form.name}
      required
    />
  </div>

  <div class="form-group">
    <label for="client-address">Address</label>
    <input
      id="client-address"
      placeholder="Enter street address"
      bind:value={form.address}
      required
    />
  </div>

  <div class="form-group">
    <label for="client-cap">CAP (Postal Code)</label>
    <input
      id="client-cap"
      placeholder="Enter postal code"
      bind:value={form.cap}
      required
    />
  </div>

  <div class="form-group">
    <label for="client-city">City</label>
    <input
      id="client-city"
      placeholder="Enter city"
      bind:value={form.city}
      required
    />
  </div>

  <div class="form-group">
    <label for="client-nation">Country</label>
    <input
      id="client-nation"
      placeholder="Enter country"
      bind:value={form.nation}
      required
    />
  </div>

  <div class="form-group">
    <label for="client-email">Email</label>
    <input
      id="client-email"
      type="email"
      placeholder="Enter email address"
      bind:value={form.email}
      required
    />
  </div>

  <div class="form-actions">
    <button>{editing !== null ? "Update" : "Add"} Client</button>
    {#if editing !== null}
      <button
        type="button"
        on:click={() => {
          editing = null;
          form = {
            name: "",
            address: "",
            cap: "",
            city: "",
            nation: "",
            email: "",
          };
        }}>Cancel</button
      >
    {/if}
  </div>
</form>
<ul>
  {#each clients as c}
    <li>
      <div class="client-info">
        <span class="client-name">{c.name}</span>
        <span class="client-email">{c.email}</span>
      </div>
      <div class="actions">
        <button class="edit-btn" on:click={() => edit(c)}>Edit</button>
        <button class="delete-btn" on:click={() => remove(c.id)}>Delete</button>
      </div>
    </li>
  {/each}
</ul>

<style>
  .form {
    display: grid;
    gap: 1rem;
    max-width: 500px;
    margin-bottom: 2.5rem;
    padding: 2rem;
    background-color: var(--surface-color);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  .form-group {
    margin-bottom: 0.5rem;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-primary-color);
  }

  button {
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    border: none;
    font-size: 1rem;
    font-weight: 500;
    color: #fff;
    background-color: var(--primary-color);
    cursor: pointer;
    transition: background-color 0.2s ease;
  }

  button:hover {
    background-color: var(--primary-color-darker);
  }

  button[type="button"] {
    background-color: var(--surface-color);
    color: var(--text-secondary-color);
    border: 1px solid var(--border-color);
  }

  button[type="button"]:hover {
    background-color: #f0f0f0;
  }

  .form-actions {
    display: flex;
    gap: 0.75rem;
    margin-top: 1rem;
  }

  ul {
    list-style-type: none;
    padding: 0;
    margin-top: 2rem;
  }

  li {
    background-color: var(--surface-color);
    padding: 1rem 1.5rem;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    margin-bottom: 1rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: box-shadow 0.2s ease;
  }

  li:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .client-info {
    display: flex;
    flex-direction: column;
  }

  .client-name {
    font-weight: 600;
    color: var(--text-primary-color);
    font-size: 1.1rem;
  }

  .client-email {
    font-size: 0.9rem;
    color: var(--text-secondary-color);
  }

  .actions {
    display: flex;
    gap: 0.5rem;
  }

  .actions button {
    padding: 0.4rem 0.8rem;
    font-size: 0.875rem;
    border-radius: 4px;
    cursor: pointer;
    transition:
      background-color 0.2s ease,
      color 0.2s ease;
  }

  .actions .edit-btn {
    background-color: var(--primary-color);
    color: white;
    border: 1px solid var(--primary-color);
  }
  .actions .edit-btn:hover {
    background-color: var(--primary-color-darker);
    border-color: var(--primary-color-darker);
  }

  .actions .delete-btn {
    background-color: transparent;
    color: #e53e3e;
    border: 1px solid #e53e3e;
  }
  .actions .delete-btn:hover {
    background-color: #e53e3e;
    color: white;
  }

  @media (max-width: 600px) {
    .form {
      padding: 1.5rem;
    }

    li {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .client-info {
      margin-bottom: 0.5rem;
    }

    .actions {
      width: 100%;
      justify-content: flex-start;
    }

    .form-actions {
      flex-direction: column;
    }

    .form-actions button {
      width: 100%;
    }
  }
</style>

