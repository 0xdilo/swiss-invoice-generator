<script>
  import {
    getTemplates,
    uploadTemplate,
    updateTemplate,
    deleteTemplate,
  } from "$lib/api.js";
  import { onMount } from "svelte";
  let templates = [];
  let name = "";
  let htmlFile;
  let cssFile;
  let editing = null;

  async function load() {
    templates = await getTemplates();
  }
  onMount(load);

  async function submit() {
    if (editing !== null) {
      await updateTemplate(
        editing,
        name,
        htmlFile ? htmlFile[0] : null,
        cssFile ? cssFile[0] : null,
      );
      editing = null;
    } else {
      await uploadTemplate(name, htmlFile[0], cssFile[0]);
    }
    name = "";
    htmlFile = null;
    cssFile = null;
    await load();
  }
  function edit(t) {
    editing = t.id;
    name = t.name;
    htmlFile = null;
    cssFile = null;
  }
  async function remove(id) {
    await deleteTemplate(id);
    await load();
  }
</script>

<h2>Templates</h2>
<form on:submit|preventDefault={submit} class="form">
  <input placeholder="Template Name" bind:value={name} required />
  <input type="file" accept=".html" bind:files={htmlFile} required={!editing} />
  <input type="file" accept=".css" bind:files={cssFile} required={!editing} />
  <div class="form-actions">
    <button>{editing !== null ? "Update" : "Upload"}</button>
    {#if editing !== null}
      <button
        type="button"
        on:click={() => {
          editing = null;
          name = "";
          htmlFile = null;
          cssFile = null;
        }}>Cancel</button
      >
    {/if}
  </div>
</form>
<ul>
  {#each templates as t}
    <li>
      <div class="template-name">{t.name}</div>
      <div class="actions">
        <button class="edit-btn" on:click={() => edit(t)}>Edit</button>
        <button class="delete-btn" on:click={() => remove(t.id)}>Delete</button>
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

  input[type="text"],
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
  select:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.25);
    outline: none;
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
    margin-top: 0.5rem;
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

  .template-name {
    font-weight: 600;
    color: var(--text-primary-color);
    font-size: 1.1rem;
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

    .template-name {
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

