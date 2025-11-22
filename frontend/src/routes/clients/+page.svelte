<script>
  import { onMount } from "svelte";
  import {
    getClients,
    addClient,
    updateClient,
    deleteClient,
    getRecurringFees,
    addRecurringFee,
    updateRecurringFee,
    deleteRecurringFee,
    generatePaymentEvents,
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
  let managingFeesFor = null;
  let recurringFees = [];
  let feeForm = {
    amount: "",
    currency: "CHF",
    frequency: "yearly",
    start_date: "",
    description: "",
  };
  let editingFee = null;

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

  async function manageFees(clientId) {
    if (managingFeesFor === clientId) {
      managingFeesFor = null;
      recurringFees = [];
    } else {
      managingFeesFor = clientId;
      await loadFees(clientId);
    }
  }

  async function loadFees(clientId) {
    recurringFees = await getRecurringFees(clientId);
  }

  async function submitFee() {
    if (editingFee !== null) {
      await updateRecurringFee(editingFee, feeForm);
      editingFee = null;
    } else {
      await addRecurringFee(managingFeesFor, feeForm);
    }
    feeForm = {
      amount: "",
      currency: "CHF",
      frequency: "yearly",
      start_date: "",
      description: "",
    };
    await loadFees(managingFeesFor);
  }

  function editFee(fee) {
    editingFee = fee.id;
    feeForm = { ...fee };
  }

  async function removeFee(feeId) {
    await deleteRecurringFee(feeId);
    await loadFees(managingFeesFor);
  }

  async function generateEvents(clientId) {
    const result = await generatePaymentEvents({ client_id: clientId });
    alert(`Generated ${result.generated} payment event(s)`);
    await loadFees(clientId);
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
      <div class="client-header">
        <div class="client-info">
          <span class="client-name">{c.name}</span>
          <span class="client-email">{c.email}</span>
        </div>
        <div class="actions">
          <button class="edit-btn" on:click={() => edit(c)}>Edit</button>
          <button
            class="fees-btn"
            on:click={() => manageFees(c.id)}
            type="button"
          >
            {managingFeesFor === c.id ? "Hide Fees" : "Manage Fees"}
          </button>
          <button class="delete-btn" on:click={() => remove(c.id)}>Delete</button>
        </div>
      </div>

      {#if managingFeesFor === c.id}
        <div class="fees-section">
          <h3>Recurring Fees for {c.name}</h3>

          <form on:submit|preventDefault={submitFee} class="fee-form">
            <div class="form-row">
              <div class="form-group">
                <label for="fee-amount">Amount</label>
                <input
                  id="fee-amount"
                  type="number"
                  step="0.01"
                  placeholder="400.00"
                  bind:value={feeForm.amount}
                  required
                />
              </div>

              <div class="form-group">
                <label for="fee-currency">Currency</label>
                <input
                  id="fee-currency"
                  placeholder="CHF"
                  bind:value={feeForm.currency}
                  required
                />
              </div>

              <div class="form-group">
                <label for="fee-frequency">Frequency</label>
                <select id="fee-frequency" bind:value={feeForm.frequency} required>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                  <option value="one-time">One-time</option>
                </select>
              </div>

              <div class="form-group">
                <label for="fee-start-date">Start Date</label>
                <input
                  id="fee-start-date"
                  type="date"
                  bind:value={feeForm.start_date}
                  required
                />
              </div>
            </div>

            <div class="form-group">
              <label for="fee-description">Description</label>
              <input
                id="fee-description"
                placeholder="Annual maintenance fee"
                bind:value={feeForm.description}
              />
            </div>

            <div class="fee-form-actions">
              <button type="submit"
                >{editingFee !== null ? "Update" : "Add"} Fee</button
              >
              {#if editingFee !== null}
                <button
                  type="button"
                  on:click={() => {
                    editingFee = null;
                    feeForm = {
                      amount: "",
                      currency: "CHF",
                      frequency: "yearly",
                      start_date: "",
                      description: "",
                    };
                  }}>Cancel</button
                >
              {/if}
            </div>
          </form>

          {#if recurringFees.length > 0}
            <div class="fees-list">
              <h4>Existing Recurring Fees</h4>
              {#each recurringFees as fee}
                <div class="fee-item">
                  <div class="fee-details">
                    <span class="fee-amount"
                      >{fee.amount} {fee.currency}</span
                    >
                    <span class="fee-frequency">{fee.frequency}</span>
                    <span class="fee-date">Starts: {fee.start_date}</span>
                    {#if fee.description}
                      <span class="fee-description">{fee.description}</span>
                    {/if}
                  </div>
                  <div class="fee-actions">
                    <button class="edit-btn" on:click={() => editFee(fee)}
                      >Edit</button
                    >
                    <button class="delete-btn" on:click={() => removeFee(fee.id)}
                      >Delete</button
                    >
                  </div>
                </div>
              {/each}
              <button
                class="generate-btn"
                type="button"
                on:click={() => generateEvents(c.id)}
              >
                Generate Payment Events
              </button>
            </div>
          {:else}
            <p class="no-fees">No recurring fees yet.</p>
          {/if}
        </div>
      {/if}
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
    transition: box-shadow 0.2s ease;
  }

  li:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .client-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
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

  .actions .fees-btn {
    background-color: transparent;
    color: var(--primary-color);
    border: 1px solid var(--primary-color);
  }
  .actions .fees-btn:hover {
    background-color: var(--primary-color);
    color: white;
  }

  .fees-section {
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border-color);
  }

  .fees-section h3 {
    margin-bottom: 1rem;
    color: var(--text-primary-color);
    font-size: 1.1rem;
  }

  .fees-section h4 {
    margin-bottom: 0.75rem;
    color: var(--text-secondary-color);
    font-size: 1rem;
  }

  .fee-form {
    background-color: #f9fafb;
    padding: 1.25rem;
    border-radius: 6px;
    margin-bottom: 1.5rem;
  }

  .form-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .fee-form-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
  }

  .fees-list {
    margin-top: 1rem;
  }

  .fee-item {
    background-color: #f9fafb;
    padding: 1rem;
    border-radius: 6px;
    margin-bottom: 0.75rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .fee-details {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: center;
  }

  .fee-amount {
    font-weight: 600;
    color: var(--text-primary-color);
    font-size: 1.1rem;
  }

  .fee-frequency {
    background-color: var(--primary-color);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 500;
  }

  .fee-date {
    color: var(--text-secondary-color);
    font-size: 0.9rem;
  }

  .fee-description {
    color: var(--text-secondary-color);
    font-style: italic;
    font-size: 0.9rem;
  }

  .fee-actions {
    display: flex;
    gap: 0.5rem;
  }

  .no-fees {
    color: var(--text-secondary-color);
    font-style: italic;
    margin-top: 1rem;
  }

  .generate-btn {
    margin-top: 1rem;
    background-color: var(--success-color);
    color: white;
  }

  .generate-btn:hover {
    background-color: #45a049;
  }

  @media (max-width: 600px) {
    .form {
      padding: 1.5rem;
    }

    .client-header {
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
      flex-wrap: wrap;
    }

    .fee-item {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .fee-actions {
      width: 100%;
    }

    .form-actions {
      flex-direction: column;
    }

    .form-actions button {
      width: 100%;
    }
  }
</style>

