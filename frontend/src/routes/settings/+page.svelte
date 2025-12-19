<script>
  import { onMount } from "svelte";
  import { page } from '$app/stores';
  import {
    getPartners, updatePartner,
    getTelegramConfig, updateTelegramConfig, testTelegramNotification,
    getBankDetails, updateBankDetails,
    getTemplates, uploadTemplate, updateTemplate, deleteTemplate,
    getTemplateContent, updateTemplateContent, previewTemplate
  } from "$lib/api.js";

  let activeTab = "partners";
  let message = "";
  let messageType = "success";

  $: {
    const tab = $page.url.searchParams.get('tab');
    if (tab && ['partners', 'bank', 'templates', 'notifications'].includes(tab)) {
      activeTab = tab;
    }
  }

  let partners = [];
  let telegramConfig = {
    bot_token: "",
    enabled: false,
    notify_renewals_7d: true,
    notify_renewals_14d: true,
    notify_renewals_30d: false,
    notify_overdue: true
  };
  let bankDetails = {
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
  let templates = [];
  let templateForm = { name: "", htmlFile: null, cssFile: null };
  let editingTemplate = null;
  let testingTelegram = false;
  let selectedTemplate = null;
  let templateHtml = "";
  let templateCss = "";
  let templatePreview = "";
  let previewLoading = false;
  let savingTemplate = false;

  async function load() {
    [partners, templates] = await Promise.all([
      getPartners(),
      getTemplates()
    ]);
    const config = await getTelegramConfig();
    if (config && Object.keys(config).length > 0) {
      telegramConfig = { ...telegramConfig, ...config };
    }
    const bank = await getBankDetails();
    if (bank) bankDetails = bank;
  }

  onMount(load);

  function showMessage(msg, type = "success") {
    message = msg;
    messageType = type;
    setTimeout(() => message = "", 4000);
  }

  async function savePartner(partner) {
    await updatePartner(partner.id, {
      name: partner.name,
      default_share: partner.default_share,
      telegram_chat_id: partner.telegram_chat_id,
      color: partner.color
    });
    showMessage("Partner updated!");
  }

  function updatePartnerShare(index, value) {
    partners[index].default_share = parseFloat(value);
    if (partners.length > 1) {
      const otherIndex = index === 0 ? 1 : 0;
      partners[otherIndex].default_share = 100 - parseFloat(value);
    }
  }

  async function saveTelegramConfig() {
    await updateTelegramConfig(telegramConfig);
    showMessage("Telegram settings saved!");
  }

  async function testTelegram() {
    testingTelegram = true;
    try {
      const result = await testTelegramNotification();
      if (result.ok) {
        showMessage(`Test sent to ${result.sent_to} recipient(s)!`);
      }
    } catch (e) {
      showMessage("Failed to send test notification", "error");
    }
    testingTelegram = false;
  }

  async function saveBankDetails() {
    await updateBankDetails(bankDetails);
    showMessage("Bank details saved!");
  }

  async function submitTemplate() {
    if (editingTemplate !== null) {
      await updateTemplate(
        editingTemplate,
        templateForm.name,
        templateForm.htmlFile ? templateForm.htmlFile[0] : null,
        templateForm.cssFile ? templateForm.cssFile[0] : null
      );
      editingTemplate = null;
    } else {
      await uploadTemplate(templateForm.name, templateForm.htmlFile[0], templateForm.cssFile[0]);
    }
    templateForm = { name: "", htmlFile: null, cssFile: null };
    templates = await getTemplates();
    showMessage(editingTemplate ? "Template updated!" : "Template uploaded!");
  }

  function editTemplate(t) {
    editingTemplate = t.id;
    templateForm = { name: t.name, htmlFile: null, cssFile: null };
  }

  async function removeTemplate(id) {
    if (confirm("Delete this template?")) {
      await deleteTemplate(id);
      templates = await getTemplates();
      showMessage("Template deleted!");
    }
  }

  function cancelTemplateEdit() {
    editingTemplate = null;
    templateForm = { name: "", htmlFile: null, cssFile: null };
  }

  async function selectTemplateForEdit(template) {
    if (selectedTemplate?.id === template.id) {
      selectedTemplate = null;
      templateHtml = "";
      templateCss = "";
      templatePreview = "";
      return;
    }
    selectedTemplate = template;
    previewLoading = true;
    try {
      const content = await getTemplateContent(template.id);
      templateHtml = content.html || "";
      templateCss = content.css || "";
      await refreshPreview();
    } catch (e) {
      showMessage("Failed to load template content", "error");
    }
    previewLoading = false;
  }

  async function refreshPreview() {
    if (!selectedTemplate) return;
    previewLoading = true;
    try {
      const result = await previewTemplate(selectedTemplate.id);
      templatePreview = result.html || "";
    } catch (e) {
      templatePreview = "<p>Preview failed</p>";
    }
    previewLoading = false;
  }

  async function saveTemplateContent() {
    if (!selectedTemplate) return;
    savingTemplate = true;
    try {
      await updateTemplateContent(selectedTemplate.id, {
        html: templateHtml,
        css: templateCss
      });
      await refreshPreview();
      showMessage("Template saved!");
    } catch (e) {
      showMessage("Failed to save template", "error");
    }
    savingTemplate = false;
  }

  function closeTemplateEditor() {
    selectedTemplate = null;
    templateHtml = "";
    templateCss = "";
    templatePreview = "";
  }
</script>

<div class="page-header">
  <div>
    <h1>Settings</h1>
    <p class="subtitle">Manage your business configuration</p>
  </div>
</div>

{#if message}
  <div class="toast {messageType}">
    {#if messageType === "success"}
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
    {:else}
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
    {/if}
    {message}
  </div>
{/if}

<div class="tabs">
  <button class:active={activeTab === "partners"} onclick={() => activeTab = "partners"}>
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
      <circle cx="9" cy="7" r="4"/>
    </svg>
    Partners
  </button>
  <button class:active={activeTab === "bank"} onclick={() => activeTab = "bank"}>
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>
      <line x1="1" y1="10" x2="23" y2="10"/>
    </svg>
    Bank & QR
  </button>
  <button class:active={activeTab === "templates"} onclick={() => activeTab = "templates"}>
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
      <line x1="3" y1="9" x2="21" y2="9"/>
      <line x1="9" y1="21" x2="9" y2="9"/>
    </svg>
    Templates
  </button>
  <button class:active={activeTab === "telegram"} onclick={() => activeTab = "telegram"}>
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M22 2L11 13"/>
      <path d="M22 2L15 22L11 13L2 9L22 2Z"/>
    </svg>
    Notifications
  </button>
</div>

{#if activeTab === "partners"}
  <div class="card">
    <div class="card-header">
      <h3>Partners</h3>
      <p class="card-desc">Configure partner names and default revenue sharing</p>
    </div>
    <div class="card-body">
      <div class="partners-grid">
        {#each partners as partner, i}
          <div class="partner-card" style="border-top-color: {partner.color}">
            <div class="partner-header">
              <input type="color" bind:value={partner.color} class="color-picker" />
              <input type="text" bind:value={partner.name} placeholder="Partner name" class="partner-name-input" />
            </div>
            <div class="form-group">
              <label>Default Share (%)</label>
              <input type="number" min="0" max="100" step="1" value={partner.default_share} oninput={(e) => updatePartnerShare(i, e.target.value)} />
            </div>
            <div class="form-group">
              <label>Telegram Chat ID</label>
              <input type="text" bind:value={partner.telegram_chat_id} placeholder="e.g. 123456789" />
            </div>
            <button class="btn-primary btn-block" onclick={() => savePartner(partner)}>Save Partner</button>
          </div>
        {/each}
      </div>
    </div>
  </div>
{/if}

{#if activeTab === "bank"}
  <div class="card">
    <div class="card-header">
      <h3>Bank & Creditor Details</h3>
      <p class="card-desc">Used for Swiss QR bill generation on invoices</p>
    </div>
    <div class="card-body">
      <form class="bank-form" onsubmit={(e) => { e.preventDefault(); saveBankDetails(); }}>
        <div class="form-section">
          <h4>Bank Information</h4>
          <div class="form-grid">
            <div class="form-group">
              <label>IBAN</label>
              <input type="text" bind:value={bankDetails.iban} placeholder="CH00 0000 0000 0000 0000 0" required />
            </div>
            <div class="form-group">
              <label>BIC / SWIFT</label>
              <input type="text" bind:value={bankDetails.bic} placeholder="BANKCHXX" required />
            </div>
          </div>
          <div class="form-group">
            <label>Bank Name</label>
            <input type="text" bind:value={bankDetails.bank_name} placeholder="Bank name" required />
          </div>
          <div class="form-group">
            <label>Bank Address</label>
            <input type="text" bind:value={bankDetails.bank_address} placeholder="Bank address" required />
          </div>
        </div>

        <div class="form-section">
          <h4>Creditor Information</h4>
          <div class="form-group">
            <label>Creditor Name</label>
            <input type="text" bind:value={bankDetails.creditor_name} placeholder="Your company name" required />
          </div>
          <div class="form-group">
            <label>Street</label>
            <input type="text" bind:value={bankDetails.creditor_street} placeholder="Street address" required />
          </div>
          <div class="form-grid">
            <div class="form-group">
              <label>Postal Code</label>
              <input type="text" bind:value={bankDetails.creditor_postalcode} placeholder="0000" required />
            </div>
            <div class="form-group">
              <label>City</label>
              <input type="text" bind:value={bankDetails.creditor_city} placeholder="City" required />
            </div>
            <div class="form-group">
              <label>Country</label>
              <input type="text" bind:value={bankDetails.creditor_country} placeholder="CH" required />
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn-primary">Save Bank Details</button>
        </div>
      </form>
    </div>
  </div>
{/if}

{#if activeTab === "templates"}
  {#if selectedTemplate}
    <div class="template-editor">
      <div class="editor-header">
        <div class="editor-title">
          <h3>Editing: {selectedTemplate.name}</h3>
        </div>
        <div class="editor-actions">
          <button class="btn-secondary" onclick={refreshPreview} disabled={previewLoading}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            Refresh Preview
          </button>
          <button class="btn-primary" onclick={saveTemplateContent} disabled={savingTemplate}>
            {savingTemplate ? "Saving..." : "Save Changes"}
          </button>
          <button class="btn-icon" onclick={closeTemplateEditor}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </div>
      <div class="editor-layout">
        <div class="editor-panels">
          <div class="editor-panel">
            <div class="panel-header">
              <span>HTML</span>
            </div>
            <textarea class="code-editor" bind:value={templateHtml} spellcheck="false"></textarea>
          </div>
          <div class="editor-panel">
            <div class="panel-header">
              <span>CSS</span>
            </div>
            <textarea class="code-editor" bind:value={templateCss} spellcheck="false"></textarea>
          </div>
        </div>
        <div class="preview-panel">
          <div class="panel-header">
            <span>Preview</span>
            {#if previewLoading}
              <span class="loading-indicator">Loading...</span>
            {/if}
          </div>
          <div class="preview-frame">
            {#if templatePreview}
              <iframe srcdoc={templatePreview} title="Template Preview" sandbox="allow-same-origin"></iframe>
            {:else}
              <div class="preview-placeholder">
                <p>Click "Refresh Preview" to see the rendered template</p>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  {:else}
    <div class="card">
      <div class="card-header">
        <h3>Invoice Templates</h3>
        <p class="card-desc">Upload and edit HTML/CSS templates for invoice generation</p>
      </div>
      <div class="card-body">
        <form class="template-form" onsubmit={(e) => { e.preventDefault(); submitTemplate(); }}>
          <div class="form-row">
            <div class="form-group">
              <label>Template Name</label>
              <input type="text" bind:value={templateForm.name} placeholder="e.g. Standard Invoice" required />
            </div>
            <div class="form-group">
              <label>HTML File</label>
              <input type="file" accept=".html" bind:files={templateForm.htmlFile} required={!editingTemplate} />
            </div>
            <div class="form-group">
              <label>CSS File</label>
              <input type="file" accept=".css" bind:files={templateForm.cssFile} required={!editingTemplate} />
            </div>
            <div class="form-group form-actions-inline">
              <button type="submit" class="btn-primary">
                {editingTemplate !== null ? "Update" : "Upload"}
              </button>
              {#if editingTemplate !== null}
                <button type="button" class="btn-secondary" onclick={cancelTemplateEdit}>Cancel</button>
              {/if}
            </div>
          </div>
        </form>

        {#if templates.length > 0}
          <div class="templates-list">
            {#each templates as t}
              <div class="template-item">
                <div class="template-info">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                  <span class="template-name">{t.name}</span>
                </div>
                <div class="template-actions">
                  <button class="btn-sm primary" onclick={() => selectTemplateForEdit(t)}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                    Edit & Preview
                  </button>
                  <button class="btn-sm danger" onclick={() => removeTemplate(t.id)}>Delete</button>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <p class="empty-text">No templates uploaded yet</p>
        {/if}
      </div>
    </div>
  {/if}
{/if}

{#if activeTab === "telegram"}
  <div class="card">
    <div class="card-header">
      <h3>Telegram Notifications</h3>
      <p class="card-desc">Set up Telegram bot for renewal reminders and alerts</p>
    </div>
    <div class="card-body">
      <div class="telegram-form">
        <div class="form-group">
          <label>Bot Token</label>
          <input type="password" bind:value={telegramConfig.bot_token} placeholder="From @BotFather" />
        </div>

        <div class="checkbox-group">
          <label class="checkbox-label">
            <input type="checkbox" bind:checked={telegramConfig.enabled} />
            <span>Enable Telegram Notifications</span>
          </label>
        </div>

        <div class="notification-options">
          <h4>Notification Types</h4>
          <div class="checkbox-grid">
            <label class="checkbox-label">
              <input type="checkbox" bind:checked={telegramConfig.notify_renewals_7d} />
              <span>Renewals due in 7 days</span>
            </label>
            <label class="checkbox-label">
              <input type="checkbox" bind:checked={telegramConfig.notify_renewals_14d} />
              <span>Renewals due in 14 days</span>
            </label>
            <label class="checkbox-label">
              <input type="checkbox" bind:checked={telegramConfig.notify_renewals_30d} />
              <span>Renewals due in 30 days</span>
            </label>
            <label class="checkbox-label">
              <input type="checkbox" bind:checked={telegramConfig.notify_overdue} />
              <span>Overdue payments</span>
            </label>
          </div>
        </div>

        <div class="btn-row">
          <button class="btn-primary" onclick={saveTelegramConfig}>Save Settings</button>
          <button class="btn-secondary" onclick={testTelegram} disabled={testingTelegram}>
            {testingTelegram ? "Sending..." : "Test Notification"}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.5rem;
  }

  h1 { margin-bottom: 0.25rem; }

  .subtitle {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 0.9375rem;
  }

  .toast {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.875rem 1.25rem;
    margin-bottom: 1.5rem;
    border-radius: var(--radius-lg);
    font-size: 0.9375rem;
    font-weight: 500;
  }

  .toast.success {
    background: var(--color-success-light);
    color: #065f46;
  }

  .toast.error {
    background: var(--color-danger-light);
    color: #991b1b;
  }

  .tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    background: var(--color-surface);
    padding: 0.375rem;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
  }

  .tabs button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1rem;
    border-radius: var(--radius-md);
    background: transparent;
    color: var(--color-text-secondary);
    font-weight: 500;
    transition: all 0.15s ease;
  }

  .tabs button:hover {
    background: var(--color-bg);
    color: var(--color-text);
  }

  .tabs button.active {
    background: var(--color-primary);
    color: white;
  }

  .card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    margin-bottom: 1.5rem;
    overflow: hidden;
  }

  .card-header {
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .card-header h3 {
    margin: 0 0 0.25rem 0;
    font-size: 1.125rem;
  }

  .card-desc {
    margin: 0;
    font-size: 0.875rem;
    color: var(--color-text-secondary);
  }

  .card-body {
    padding: 1.5rem;
  }

  .partners-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
  }

  .partner-card {
    padding: 1.25rem;
    background: var(--color-bg);
    border-radius: var(--radius-lg);
    border-top: 4px solid;
  }

  .partner-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.25rem;
  }

  .color-picker {
    width: 40px;
    height: 40px;
    padding: 0;
    border: none;
    border-radius: var(--radius-md);
    cursor: pointer;
    flex-shrink: 0;
  }

  .partner-name-input {
    flex: 1;
    font-size: 1.125rem;
    font-weight: 600;
    padding: 0.5rem 0.75rem;
  }

  .form-group {
    margin-bottom: 1rem;
  }

  .form-group label {
    display: block;
    margin-bottom: 0.375rem;
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  .form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .form-section {
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--color-border-light);
  }

  .form-section:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
  }

  .form-section h4 {
    margin: 0 0 1rem 0;
    font-size: 0.9375rem;
    font-weight: 600;
    color: var(--color-text);
  }

  .bank-form {
    max-width: 600px;
  }

  .template-form {
    margin-bottom: 1.5rem;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr auto;
    gap: 1rem;
    align-items: end;
  }

  .form-actions-inline {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0;
  }

  .templates-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .template-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.875rem 1rem;
    background: var(--color-bg);
    border-radius: var(--radius-md);
  }

  .template-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: var(--color-text-secondary);
  }

  .template-name {
    font-weight: 500;
    color: var(--color-text);
  }

  .template-actions {
    display: flex;
    gap: 0.375rem;
  }

  .btn-primary {
    background: var(--color-primary);
    color: white;
  }

  .btn-primary:hover {
    background: var(--color-primary-hover);
  }

  .btn-secondary {
    background: var(--color-surface);
    color: var(--color-text);
    border: 1px solid var(--color-border);
  }

  .btn-secondary:hover {
    background: var(--color-bg);
  }

  .btn-secondary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-block {
    width: 100%;
    margin-top: 0.5rem;
  }

  .btn-sm {
    padding: 0.375rem 0.75rem;
    font-size: 0.8125rem;
    background: var(--color-surface);
    color: var(--color-text-secondary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
  }

  .btn-sm:hover {
    background: var(--color-bg);
    color: var(--color-text);
  }

  .btn-sm.danger {
    color: var(--color-danger);
    border-color: var(--color-danger);
  }

  .btn-sm.danger:hover {
    background: var(--color-danger-light);
  }

  .telegram-form {
    max-width: 500px;
  }

  .checkbox-group {
    margin: 1rem 0;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    cursor: pointer;
    padding: 0.375rem 0;
  }

  .checkbox-label input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
    accent-color: var(--color-primary);
  }

  .notification-options {
    margin: 1.5rem 0;
    padding: 1.25rem;
    background: var(--color-bg);
    border-radius: var(--radius-lg);
  }

  .notification-options h4 {
    margin: 0 0 1rem 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--color-text-secondary);
  }

  .checkbox-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }

  .btn-row {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .form-actions {
    display: flex;
    gap: 0.75rem;
  }

  .empty-text {
    text-align: center;
    color: var(--color-text-muted);
    padding: 2rem;
  }

  @media (max-width: 768px) {
    .tabs {
      flex-wrap: wrap;
    }

    .tabs button {
      flex: 1;
      min-width: 120px;
      justify-content: center;
    }

    .form-row {
      grid-template-columns: 1fr;
    }

    .form-grid {
      grid-template-columns: 1fr;
    }

    .partners-grid {
      grid-template-columns: 1fr;
    }

    .checkbox-grid {
      grid-template-columns: 1fr;
    }

    .btn-row {
      flex-direction: column;
    }

    .btn-row button {
      width: 100%;
    }
  }

  .template-editor {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    overflow: hidden;
  }

  .editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--color-border-light);
    background: var(--color-bg);
  }

  .editor-title h3 {
    margin: 0;
    font-size: 1rem;
  }

  .editor-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .editor-actions .btn-secondary,
  .editor-actions .btn-primary {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.5rem 0.875rem;
    font-size: 0.875rem;
  }

  .btn-icon {
    background: transparent;
    border: none;
    color: var(--color-text-secondary);
    padding: 0.375rem;
    border-radius: var(--radius-sm);
    cursor: pointer;
  }

  .btn-icon:hover {
    background: var(--color-bg);
    color: var(--color-text);
  }

  .editor-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    min-height: 600px;
  }

  .editor-panels {
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--color-border-light);
  }

  .editor-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-bottom: 1px solid var(--color-border-light);
  }

  .editor-panel:last-child {
    border-bottom: none;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.625rem 1rem;
    background: var(--color-bg);
    border-bottom: 1px solid var(--color-border-light);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-secondary);
  }

  .loading-indicator {
    font-weight: 400;
    font-size: 0.6875rem;
    text-transform: none;
    letter-spacing: normal;
    color: var(--color-primary);
  }

  .code-editor {
    flex: 1;
    padding: 1rem;
    border: none;
    resize: none;
    font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
    font-size: 0.8125rem;
    line-height: 1.5;
    background: var(--color-surface);
    color: var(--color-text);
  }

  .code-editor:focus {
    outline: none;
    box-shadow: inset 0 0 0 2px var(--color-primary-light);
  }

  .preview-panel {
    display: flex;
    flex-direction: column;
    background: var(--color-bg);
  }

  .preview-frame {
    flex: 1;
    padding: 1rem;
    overflow: auto;
  }

  .preview-frame iframe {
    width: 100%;
    height: 100%;
    border: 1px solid var(--color-border-light);
    border-radius: var(--radius-sm);
    background: white;
  }

  .preview-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--color-text-muted);
    font-size: 0.875rem;
  }

  .btn-sm.primary {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
  }

  .btn-sm.primary:hover {
    background: var(--color-primary-hover);
    border-color: var(--color-primary-hover);
  }

  @media (max-width: 1024px) {
    .editor-layout {
      grid-template-columns: 1fr;
      min-height: auto;
    }

    .editor-panels {
      border-right: none;
      border-bottom: 1px solid var(--color-border-light);
    }

    .editor-panel {
      min-height: 200px;
    }

    .preview-panel {
      min-height: 400px;
    }
  }
</style>
