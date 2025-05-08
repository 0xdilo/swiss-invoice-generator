<script>
  import { onMount } from "svelte";
  import { getBankDetails, updateBankDetails } from "$lib/api.js";

  let details = {
    iban: "",
    bank_name: "",
    bank_address: "",
    bic: "",
    creditor_name: "",
    creditor_street: "",
    creditor_postalcode: "",
    creditor_city: "",
    creditor_country: "",
  };
  let message = "";

  async function load() {
    const d = await getBankDetails();
    if (d) details = d;
  }
  onMount(load);

  async function submit() {
    await updateBankDetails(details);
    message = "Bank details updated!";
  }
</script>

<h2>Bank Details</h2>
<form on:submit|preventDefault={submit} class="form">
  <input placeholder="IBAN" bind:value={details.iban} required />
  <input placeholder="Bank Name" bind:value={details.bank_name} required />
  <input
    placeholder="Bank Address"
    bind:value={details.bank_address}
    required
  />
  <input placeholder="BIC" bind:value={details.bic} required />
  <input
    placeholder="Creditor Name"
    bind:value={details.creditor_name}
    required
  />
  <input
    placeholder="Creditor Street"
    bind:value={details.creditor_street}
    required
  />
  <input
    placeholder="Creditor Postal Code"
    bind:value={details.creditor_postalcode}
    required
  />
  <input
    placeholder="Creditor City"
    bind:value={details.creditor_city}
    required
  />
  <input
    placeholder="Creditor Country"
    bind:value={details.creditor_country}
    required
  />
  <button>Save</button>
</form>
{#if message}
  <p class="feedback-message success">{message}</p>
{/if}

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

  input {
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

  input:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.25);
    outline: none;
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

  .feedback-message {
    padding: 0.75rem 1.25rem;
    margin-top: 1.5rem;
    border-radius: 6px;
    font-size: 0.95rem;
    text-align: center;
    max-width: 500px;
  }

  .feedback-message.success {
    background-color: #e6f7e7;
    color: #27672a;
    border: 1px solid #a8dba9;
  }

  .feedback-message.error {
    background-color: #fdecea;
    color: #9b2c2c;
    border: 1px solid #f7b0b0;
  }

  @media (max-width: 600px) {
    .form {
      padding: 1.5rem;
    }
  }
</style>

