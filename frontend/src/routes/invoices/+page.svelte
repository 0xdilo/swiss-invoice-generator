<script>
  import {
    getClients,
    getTemplates,
    getTemplateFields,
    createInvoice,
    getInvoices,
    updateInvoice,
    deleteInvoice,
  } from "$lib/api.js";
  import { onMount } from "svelte";
  let clients = [],
    templates = [],
    invoices = [];
  let client_id = "",
    template_id = "";
  let dynamicFields = [];
  let dynamicData = {};
  let items = [{ desc: "", price: 0, qty: 1 }];
  let invoiceUrl = "";
  let editing = null;
  let logoUploadFile = null;
  let showLogoUploadUI = false;

  const AUTO_FIELDS = [
    "client",
    "customer",
    "items",
    "subtotal",
    "net_total",
    "total",
    "qr_image",
    "invoice_number",
    "date",
    "logo",
  ];

  async function load() {
    clients = await getClients();
    templates = await getTemplates();
    invoices = await getInvoices();
  }
  onMount(load);

  $: if (template_id) {
    getTemplateFields(template_id).then((res) => {
      const allFields = res.fields || [];
      dynamicFields = allFields.filter((f) => {
        if (AUTO_FIELDS.includes(f)) return false;
        if (f.startsWith("client.")) return false;
        if (f.startsWith("customer.")) return false;
        if (f.startsWith("item.")) return false;
        if (f.startsWith("items")) return false;
        if (f.startsWith("loop.")) return false;
        return true;
      });
      showLogoUploadUI = allFields.includes("logo");
    });
  } else {
    dynamicFields = [];
    showLogoUploadUI = false;
  }

  function addItem() {
    items = [...items, { desc: "", price: 0, qty: 1 }];
  }

  function removeItem(index) {
    if (items.length > 1) {
      items = items.filter((_, i) => i !== index);
    }
  }

  function formatSwissDate(isoDate) {
    const [year, month, day] = isoDate.split("-");
    return `${day}.${month}.${year}`;
  }

  async function submit() {
    const isoDate = dynamicData.date || new Date().toISOString().split("T")[0];
    const data = { ...dynamicData, items, date: isoDate };
    if (editing !== null) {
      const res = await updateInvoice(
        editing,
        client_id,
        template_id,
        data,
        logoUploadFile ? logoUploadFile[0] : null,
      );
      invoiceUrl = `http://localhost:8000/invoices/${res.id}/pdf?t=${Date.now()}`;
      editing = null;
    } else {
      const res = await createInvoice(
        client_id,
        template_id,
        data,
        logoUploadFile ? logoUploadFile[0] : null,
      );
      invoiceUrl = `http://localhost:8000/invoices/${res.id}/pdf?t=${Date.now()}`;
    }
    dynamicData = {};
    items = [{ desc: "", price: 0, qty: 1 }];
    client_id = "";
    template_id = "";
    logoUploadFile = null;
    await load();
  }

  function edit(inv) {
    editing = inv.id;
    client_id = inv.client_id;
    template_id = inv.template_id;
    const d = JSON.parse(inv.data);
    dynamicData = {};
    items = d.items || [];
    for (const k in d) if (k !== "items") dynamicData[k] = d[k];
  }

  async function remove(id) {
    await deleteInvoice(id);
    await load();
  }
</script>

<h2>Invoices</h2>
<form on:submit|preventDefault={submit} class="form">
  <div class="form-group">
    <label for="client-select">Client</label>
    <select id="client-select" bind:value={client_id} required>
      <option value="" disabled selected>Select client</option>
      {#each clients as c}
        <option value={c.id}>{c.name}</option>
      {/each}
    </select>
  </div>

  <div class="form-group">
    <label for="template-select">Template</label>
    <select id="template-select" bind:value={template_id} required>
      <option value="" disabled selected>Select template</option>
      {#each templates as t}
        <option value={t.id}>{t.name}</option>
      {/each}
    </select>
  </div>

  {#if showLogoUploadUI}
    <div class="form-group">
      <label for="logoInput" class="file-label">Upload Logo (optional)</label>
      <input
        id="logoInput"
        type="file"
        accept="image/*"
        bind:files={logoUploadFile}
      />
    </div>
  {/if}

  {#each dynamicFields as field}
    <div class="form-group">
      <label for={`field-${field}`}>{field}</label>
      <input
        id={`field-${field}`}
        placeholder={`Enter ${field}`}
        bind:value={dynamicData[field]}
        type={field.toLowerCase().includes("date") ? "date" : "text"}
        required
      />
    </div>
  {/each}

  <h3>Items</h3>
  {#each items as item, i}
    <div class="item-container">
      <div class="item-row">
        <div class="item-description">
          <label for={`item-desc-${i}`}>Description</label>
          <input
            id={`item-desc-${i}`}
            class="description-input"
            placeholder="Enter item description"
            bind:value={item.desc}
            required
          />
        </div>

        <div class="item-price">
          <label for={`item-price-${i}`}>Price</label>
          <input
            id={`item-price-${i}`}
            type="number"
            placeholder="Price"
            bind:value={item.price}
            step="0.01"
            min="0"
            required
          />
        </div>

        <div class="item-qty">
          <label for={`item-qty-${i}`}>Quantity</label>
          <input
            id={`item-qty-${i}`}
            type="number"
            placeholder="Qty"
            bind:value={item.qty}
            step="0.1"
            min="0"
            required
          />
        </div>

        {#if items.length > 1}
          <div class="item-remove">
            <button 
              type="button" 
              class="remove-item-btn" 
              on:click={() => removeItem(i)}
              title="Remove item"
            >×</button>
          </div>
        {/if}
      </div>
    </div>
  {/each}

  <button type="button" class="add-item-btn" on:click={addItem}>Add Item</button
  >

  <div class="form-actions">
    <button>{editing !== null ? "Update" : "Create"} Invoice</button>
    {#if editing !== null}
      <button
        type="button"
        on:click={() => {
          editing = null;
          dynamicData = {};
          items = [{ desc: "", price: 0, qty: 1 }];
          client_id = "";
          template_id = "";
          logoUploadFile = null;
        }}>Cancel</button
      >
    {/if}
  </div>
</form>

{#if invoiceUrl}
  <a href={invoiceUrl} target="_blank" class="download-pdf-link">Download PDF</a
  >
{/if}

<ul>
  {#each invoices as inv}
    <li>
      <div class="invoice-details">
        <span class="invoice-id">Invoice #{inv.id}</span>
        <span class="invoice-meta"
          >Client: {inv.client_id}, Template: {inv.template_id}</span
        >
      </div>
      <div class="actions">
        <button class="edit-btn" on:click={() => edit(inv)}>Edit</button>
        <a
          href={`http://localhost:8000/invoices/${inv.id}/pdf?t=${Date.now()}`}
          target="_blank"
          class="pdf-link">PDF</a
        >
        <button class="delete-btn" on:click={() => remove(inv.id)}
          >Delete</button
        >
      </div>
    </li>
  {/each}
</ul>

<style>
  .form {
    display: grid;
    gap: 1rem;
    max-width: 700px;
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

  .item-container {
    margin-bottom: 1.5rem;
    padding: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    background-color: #f9f9f9;
  }

  .item-row {
    display: grid;
    grid-template-columns: 3fr 1fr 1fr auto;
    gap: 1rem;
    align-items: start;
  }

  .item-description {
    width: 100%;
  }

  .description-input {
    min-height: 2.5rem;
    font-size: 1rem;
  }

  .add-item-btn {
    margin-bottom: 1rem;
  }

  .remove-item-btn {
    background-color: #e53e3e;
    color: white;
    border: none;
    border-radius: 50%;
    width: 2rem;
    height: 2rem;
    font-size: 1.2rem;
    font-weight: bold;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 1.5rem;
    transition: background-color 0.2s ease;
  }

  .remove-item-btn:hover {
    background-color: #c53030;
  }

  .item-remove {
    display: flex;
    justify-content: center;
  }

  input[type="text"],
  input[type="number"],
  input[type="date"],
  select {
    padding: 0.75rem 1rem;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-size: 1rem;
    color: var(--text-primary-color);
    background-color: #fff;
    transition:
      border-color 0.2s ease,
      box-shadow 0.2s ease;
    width: 100%;
  }

  input[type="text"]:focus,
  input[type="number"]:focus,
  input[type="date"]:focus,
  select:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.25);
    outline: none;
  }

  .file-label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-secondary-color);
  }

  input[type="file"] {
    padding: 0.6rem 0.8rem;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-size: 0.9rem;
    color: var(--text-secondary-color);
    background-color: #fff;
    cursor: pointer;
  }

  input[type="file"]::file-selector-button {
    padding: 0.5rem 1rem;
    margin-right: 1rem;
    border: none;
    border-radius: 4px;
    background-color: var(--primary-color);
    color: white;
    cursor: pointer;
    transition: background-color 0.2s ease;
  }

  input[type="file"]::file-selector-button:hover {
    background-color: var(--primary-color-darker);
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
  .download-pdf-link {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    margin-top: 1.5rem;
    background-color: var(--success-color);
    color: white;
    font-weight: 500;
    text-decoration: none;
    border-radius: 6px;
    text-align: center;
    transition: background-color 0.2s ease;
  }

  .download-pdf-link:hover {
    background-color: #388e3c;
    text-decoration: none;
  }

  h3 {
    margin-top: 1rem;
    margin-bottom: 0.75rem;
    color: var(--text-primary-color);
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

  .invoice-details {
    display: flex;
    flex-direction: column;
  }

  .invoice-id {
    font-weight: 600;
    color: var(--text-primary-color);
    font-size: 1.1rem;
  }

  .invoice-meta {
    font-size: 0.9rem;
    color: var(--text-secondary-color);
  }

  .actions {
    display: flex;
    gap: 0.5rem;
  }

  .actions button,
  .actions .pdf-link {
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

  .actions .pdf-link {
    display: inline-block;
    background-color: var(--text-secondary-color);
    color: white;
    border: 1px solid var(--text-secondary-color);
    text-decoration: none;
  }

  .actions .pdf-link:hover {
    background-color: #333;
    border-color: #333;
    text-decoration: none;
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

  @media (max-width: 700px) {
    .form {
      padding: 1.5rem;
    }

    .item-row {
      display: grid;
      grid-template-columns: 1fr;
      gap: 0.8rem;
    }

    .item-container {
      padding: 0.8rem;
    }

    li {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .invoice-details {
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

