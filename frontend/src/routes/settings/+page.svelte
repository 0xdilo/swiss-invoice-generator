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
  let showUploadForm = false;

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
    showUploadForm = false;
    templates = await getTemplates();
    showMessage(editingTemplate ? "Template updated!" : "Template uploaded!");
  }

  function editTemplate(t) {
    editingTemplate = t.id;
    templateForm = { name: t.name, htmlFile: null, cssFile: null };
    showUploadForm = true;
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
    showUploadForm = false;
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

<div class="settings-page">
  <header class="page-header">
    <div class="header-content">
      <h1>Settings</h1>
      <p class="subtitle">Manage your business configuration</p>
    </div>
  </header>

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
      <span>{message}</span>
    </div>
  {/if}

  <div class="tabs-container">
    <div class="tabs">
      <button class:active={activeTab === "partners"} onclick={() => activeTab = "partners"}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
          <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
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
  </div>

  {#if activeTab === "partners"}
    <div class="content-section">
      <div class="section-header">
        <h2>Partners</h2>
        <p>Configure partner names and default revenue sharing</p>
      </div>
      <div class="partners-grid">
        {#each partners as partner, i}
          <div class="partner-card" style="--partner-color: {partner.color}">
            <div class="partner-accent"></div>
            <div class="partner-content">
              <div class="partner-header">
                <input type="color" bind:value={partner.color} class="color-picker" />
                <input type="text" bind:value={partner.name} placeholder="Partner name" class="partner-name-input" />
              </div>

              <div class="form-field">
                <label>Default Share</label>
                <div class="share-input-wrapper">
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="1"
                    value={partner.default_share}
                    oninput={(e) => updatePartnerShare(i, e.target.value)}
                  />
                  <span class="share-suffix">%</span>
                </div>
              </div>

              <div class="form-field">
                <label>Telegram Chat ID</label>
                <input type="text" bind:value={partner.telegram_chat_id} placeholder="e.g. 123456789" />
              </div>

              <button class="btn-save" onclick={() => savePartner(partner)}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Save Partner
              </button>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  {#if activeTab === "bank"}
    <div class="content-section">
      <div class="section-header">
        <h2>Bank & Creditor Details</h2>
        <p>Used for Swiss QR bill generation on invoices</p>
      </div>

      <form class="settings-form" onsubmit={(e) => { e.preventDefault(); saveBankDetails(); }}>
        <div class="form-card">
          <div class="form-card-header">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>
              <line x1="1" y1="10" x2="23" y2="10"/>
            </svg>
            <h3>Bank Information</h3>
          </div>
          <div class="form-card-body">
            <div class="form-row">
              <div class="form-field">
                <label>IBAN</label>
                <input type="text" bind:value={bankDetails.iban} placeholder="CH00 0000 0000 0000 0000 0" required />
              </div>
              <div class="form-field">
                <label>BIC / SWIFT</label>
                <input type="text" bind:value={bankDetails.bic} placeholder="BANKCHXX" required />
              </div>
            </div>
            <div class="form-field">
              <label>Bank Name</label>
              <input type="text" bind:value={bankDetails.bank_name} placeholder="Bank name" required />
            </div>
            <div class="form-field">
              <label>Bank Address</label>
              <input type="text" bind:value={bankDetails.bank_address} placeholder="Bank address" required />
            </div>
          </div>
        </div>

        <div class="form-card">
          <div class="form-card-header">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            <h3>Creditor Information</h3>
          </div>
          <div class="form-card-body">
            <div class="form-field">
              <label>Creditor Name</label>
              <input type="text" bind:value={bankDetails.creditor_name} placeholder="Your company name" required />
            </div>
            <div class="form-field">
              <label>Street Address</label>
              <input type="text" bind:value={bankDetails.creditor_street} placeholder="Street address" required />
            </div>
            <div class="form-row three-col">
              <div class="form-field">
                <label>Postal Code</label>
                <input type="text" bind:value={bankDetails.creditor_postalcode} placeholder="0000" required />
              </div>
              <div class="form-field flex-2">
                <label>City</label>
                <input type="text" bind:value={bankDetails.creditor_city} placeholder="City" required />
              </div>
              <div class="form-field">
                <label>Country</label>
                <input type="text" bind:value={bankDetails.creditor_country} placeholder="CH" required />
              </div>
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn-primary">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Save Bank Details
          </button>
        </div>
      </form>
    </div>
  {/if}

  {#if activeTab === "templates"}
    {#if selectedTemplate}
      <div class="template-editor">
        <div class="editor-header">
          <div class="editor-title">
            <span class="editor-badge">Editing</span>
            <h3>{selectedTemplate.name}</h3>
          </div>
          <div class="editor-actions">
            <button class="btn-secondary" onclick={refreshPreview} disabled={previewLoading}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 4 23 10 17 10"/>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
              </svg>
              Refresh
            </button>
            <button class="btn-primary" onclick={saveTemplateContent} disabled={savingTemplate}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              {savingTemplate ? "Saving..." : "Save"}
            </button>
            <button class="btn-close" onclick={closeTemplateEditor}>
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
                <span class="panel-label">HTML</span>
              </div>
              <textarea class="code-editor" bind:value={templateHtml} spellcheck="false"></textarea>
            </div>
            <div class="editor-panel">
              <div class="panel-header">
                <span class="panel-label">CSS</span>
              </div>
              <textarea class="code-editor" bind:value={templateCss} spellcheck="false"></textarea>
            </div>
          </div>
          <div class="preview-panel">
            <div class="panel-header">
              <span class="panel-label">Preview</span>
              {#if previewLoading}
                <span class="loading-dot"></span>
              {/if}
            </div>
            <div class="preview-frame">
              {#if templatePreview}
                <iframe srcdoc={templatePreview} title="Template Preview" sandbox="allow-same-origin"></iframe>
              {:else}
                <div class="preview-placeholder">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                  <p>Click "Refresh" to preview</p>
                </div>
              {/if}
            </div>
          </div>
        </div>
      </div>
    {:else}
      <div class="content-section">
        <div class="section-header">
          <div>
            <h2>Invoice Templates</h2>
            <p>Upload and edit HTML/CSS templates for invoice generation</p>
          </div>
          <button class="btn-primary" onclick={() => showUploadForm = !showUploadForm}>
            {#if showUploadForm}
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
              Cancel
            {:else}
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Upload Template
            {/if}
          </button>
        </div>

        {#if showUploadForm}
          <form class="upload-form" onsubmit={(e) => { e.preventDefault(); submitTemplate(); }}>
            <div class="upload-form-badge">{editingTemplate !== null ? "Edit" : "New"}</div>
            <div class="form-row three-col">
              <div class="form-field">
                <label>Template Name</label>
                <input type="text" bind:value={templateForm.name} placeholder="e.g. Standard Invoice" required />
              </div>
              <div class="form-field">
                <label>HTML File</label>
                <input type="file" accept=".html" bind:files={templateForm.htmlFile} required={!editingTemplate} />
              </div>
              <div class="form-field">
                <label>CSS File</label>
                <input type="file" accept=".css" bind:files={templateForm.cssFile} required={!editingTemplate} />
              </div>
            </div>
            <div class="upload-actions">
              <button type="button" class="btn-cancel" onclick={cancelTemplateEdit}>Cancel</button>
              <button type="submit" class="btn-primary">
                {editingTemplate !== null ? "Update Template" : "Upload Template"}
              </button>
            </div>
          </form>
        {/if}

        {#if templates.length > 0}
          <div class="templates-grid">
            {#each templates as t, i}
              <div class="template-card" style="animation-delay: {i * 50}ms">
                <div class="template-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <polyline points="10 9 9 9 8 9"/>
                  </svg>
                </div>
                <div class="template-info">
                  <span class="template-name">{t.name}</span>
                  <span class="template-meta">Invoice template</span>
                </div>
                <div class="template-actions">
                  <button class="action-btn primary" onclick={() => selectTemplateForEdit(t)}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                    Edit
                  </button>
                  <button class="action-btn danger" onclick={() => removeTemplate(t.id)}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6"/>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                  </button>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <div class="empty-state">
            <div class="empty-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="3" y1="9" x2="21" y2="9"/>
                <line x1="9" y1="21" x2="9" y2="9"/>
              </svg>
            </div>
            <p>No templates uploaded yet</p>
            <button class="btn-primary" onclick={() => showUploadForm = true}>Upload your first template</button>
          </div>
        {/if}
      </div>
    {/if}
  {/if}

  {#if activeTab === "telegram"}
    <div class="content-section">
      <div class="section-header">
        <h2>Telegram Notifications</h2>
        <p>Set up Telegram bot for renewal reminders and alerts</p>
      </div>

      <div class="settings-form">
        <div class="form-card">
          <div class="form-card-header">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 2L11 13"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z"/>
            </svg>
            <h3>Bot Configuration</h3>
          </div>
          <div class="form-card-body">
            <div class="form-field">
              <label>Bot Token</label>
              <input type="password" bind:value={telegramConfig.bot_token} placeholder="Get this from @BotFather" />
            </div>

            <label class="toggle-control">
              <input type="checkbox" bind:checked={telegramConfig.enabled} />
              <div class="toggle-switch"></div>
              <div class="toggle-text">
                <span class="toggle-title">Enable Notifications</span>
                <span class="toggle-desc">Receive alerts via Telegram</span>
              </div>
            </label>
          </div>
        </div>

        <div class="form-card">
          <div class="form-card-header">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <h3>Notification Types</h3>
          </div>
          <div class="form-card-body">
            <div class="notification-grid">
              <label class="notification-option">
                <input type="checkbox" bind:checked={telegramConfig.notify_renewals_7d} />
                <div class="option-content">
                  <span class="option-badge urgent">7 days</span>
                  <span class="option-title">Urgent renewals</span>
                </div>
              </label>
              <label class="notification-option">
                <input type="checkbox" bind:checked={telegramConfig.notify_renewals_14d} />
                <div class="option-content">
                  <span class="option-badge warning">14 days</span>
                  <span class="option-title">Upcoming renewals</span>
                </div>
              </label>
              <label class="notification-option">
                <input type="checkbox" bind:checked={telegramConfig.notify_renewals_30d} />
                <div class="option-content">
                  <span class="option-badge">30 days</span>
                  <span class="option-title">Early reminders</span>
                </div>
              </label>
              <label class="notification-option">
                <input type="checkbox" bind:checked={telegramConfig.notify_overdue} />
                <div class="option-content">
                  <span class="option-badge danger">Overdue</span>
                  <span class="option-title">Payment alerts</span>
                </div>
              </label>
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button class="btn-secondary" onclick={testTelegram} disabled={testingTelegram}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            {testingTelegram ? "Sending..." : "Send Test"}
          </button>
          <button class="btn-primary" onclick={saveTelegramConfig}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Save Settings
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .settings-page {
    max-width: 900px;
    margin: 0 auto;
  }

  .page-header {
    margin-bottom: 1.5rem;
  }

  .page-header h1 {
    font-size: 1.75rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.03em;
  }

  .subtitle {
    margin: 0.25rem 0 0;
    color: var(--color-text-secondary);
    font-size: 0.9375rem;
  }

  .toast {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.25rem;
    margin-bottom: 1.5rem;
    border-radius: 12px;
    font-weight: 500;
    animation: slideIn 0.3s ease;
  }

  @keyframes slideIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .toast.success {
    background: rgba(16, 185, 129, 0.1);
    color: #059669;
  }

  .toast.error {
    background: rgba(239, 68, 68, 0.1);
    color: #dc2626;
  }

  .tabs-container {
    margin-bottom: 2rem;
  }

  .tabs {
    display: flex;
    gap: 0.375rem;
    background: var(--color-surface);
    padding: 0.375rem;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }

  .tabs button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border: none;
    border-radius: 10px;
    background: transparent;
    color: var(--color-text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    flex: 1;
    justify-content: center;
  }

  .tabs button:hover {
    background: var(--color-bg);
    color: var(--color-text);
  }

  .tabs button.active {
    background: var(--color-primary);
    color: white;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
  }

  .content-section {
    animation: fadeIn 0.3s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.5rem;
  }

  .section-header h2 {
    font-size: 1.125rem;
    font-weight: 600;
    margin: 0 0 0.25rem;
  }

  .section-header p {
    margin: 0;
    font-size: 0.875rem;
    color: var(--color-text-secondary);
  }

  .partners-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 1.5rem;
  }

  .partner-card {
    background: var(--color-surface);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
  }

  .partner-accent {
    height: 4px;
    background: var(--partner-color);
  }

  .partner-content {
    padding: 1.5rem;
  }

  .partner-header {
    display: flex;
    align-items: center;
    gap: 0.875rem;
    margin-bottom: 1.5rem;
  }

  .color-picker {
    width: 48px;
    height: 48px;
    padding: 0;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    flex-shrink: 0;
  }

  .partner-name-input {
    flex: 1;
    font-size: 1.25rem;
    font-weight: 600;
    padding: 0.5rem 0.75rem;
    border: 1px solid transparent;
    border-radius: 8px;
    background: transparent;
    transition: all 0.2s ease;
  }

  .partner-name-input:hover,
  .partner-name-input:focus {
    background: var(--color-bg);
    border-color: var(--color-border);
  }

  .form-field {
    margin-bottom: 1rem;
  }

  .form-field label {
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.375rem;
  }

  .form-field input,
  .form-field select {
    width: 100%;
    padding: 0.625rem 0.875rem;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    font-size: 0.9375rem;
    background: white;
    transition: all 0.2s ease;
  }

  .form-field input:focus,
  .form-field select:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .share-input-wrapper {
    position: relative;
  }

  .share-input-wrapper input {
    padding-right: 2.5rem;
  }

  .share-suffix {
    position: absolute;
    right: 0.875rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--color-text-muted);
    font-weight: 500;
  }

  .btn-save {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.75rem;
    margin-top: 0.5rem;
    background: var(--partner-color);
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 0.9375rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-save:hover {
    filter: brightness(1.1);
    transform: translateY(-1px);
  }

  .settings-form {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .form-card {
    background: var(--color-surface);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
  }

  .form-card-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.5rem;
    background: var(--color-bg);
    border-bottom: 1px solid var(--color-border-light);
  }

  .form-card-header svg {
    color: var(--color-primary);
  }

  .form-card-header h3 {
    margin: 0;
    font-size: 0.9375rem;
    font-weight: 600;
  }

  .form-card-body {
    padding: 1.5rem;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .form-row.three-col {
    grid-template-columns: 1fr 2fr 1fr;
  }

  .form-field.flex-2 {
    grid-column: span 1;
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
  }

  .btn-primary {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    background: var(--color-primary);
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 0.9375rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-primary:hover {
    background: var(--color-primary-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  }

  .btn-secondary {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    background: white;
    color: var(--color-text-secondary);
    border: 1px solid var(--color-border);
    border-radius: 10px;
    font-size: 0.9375rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-secondary:hover {
    background: var(--color-bg);
    color: var(--color-text);
  }

  .btn-secondary:disabled,
  .btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  .btn-cancel {
    padding: 0.625rem 1.25rem;
    background: white;
    color: var(--color-text-secondary);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    font-size: 0.9375rem;
    font-weight: 500;
    cursor: pointer;
  }

  .upload-form {
    background: var(--color-surface);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    animation: slideIn 0.3s ease;
  }

  .upload-form-badge {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: var(--color-primary);
    color: white;
    font-size: 0.6875rem;
    font-weight: 600;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .upload-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--color-border-light);
  }

  .templates-grid {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .template-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.25rem;
    background: var(--color-surface);
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    animation: fadeIn 0.4s ease backwards;
    transition: all 0.2s ease;
  }

  .template-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    transform: translateY(-1px);
  }

  .template-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: var(--color-primary-light);
    color: var(--color-primary);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .template-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .template-name {
    font-weight: 600;
    font-size: 0.9375rem;
  }

  .template-meta {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }

  .template-actions {
    display: flex;
    gap: 0.5rem;
  }

  .action-btn {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.5rem 0.875rem;
    border: none;
    border-radius: 8px;
    font-size: 0.8125rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .action-btn.primary {
    background: var(--color-primary);
    color: white;
  }

  .action-btn.primary:hover {
    background: var(--color-primary-hover);
  }

  .action-btn.danger {
    background: transparent;
    color: var(--color-text-muted);
  }

  .action-btn.danger:hover {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    background: var(--color-surface);
    border-radius: 16px;
    text-align: center;
  }

  .empty-icon {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background: var(--color-bg);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1.5rem;
    color: var(--color-text-muted);
    opacity: 0.5;
  }

  .empty-state p {
    color: var(--color-text-secondary);
    margin: 0 0 1.5rem;
  }

  .toggle-control {
    display: flex;
    align-items: flex-start;
    gap: 0.875rem;
    cursor: pointer;
    padding: 1rem;
    background: var(--color-bg);
    border-radius: 10px;
    margin-top: 1rem;
  }

  .toggle-control input {
    display: none;
  }

  .toggle-switch {
    width: 44px;
    height: 24px;
    background: var(--color-border);
    border-radius: 12px;
    position: relative;
    transition: all 0.2s ease;
    flex-shrink: 0;
  }

  .toggle-switch::after {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    width: 20px;
    height: 20px;
    background: white;
    border-radius: 50%;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  }

  .toggle-control input:checked + .toggle-switch {
    background: var(--color-primary);
  }

  .toggle-control input:checked + .toggle-switch::after {
    left: 22px;
  }

  .toggle-text {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .toggle-title {
    font-weight: 600;
    font-size: 0.9375rem;
  }

  .toggle-desc {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .notification-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }

  .notification-option {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    background: var(--color-bg);
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .notification-option:hover {
    background: var(--color-border-light);
  }

  .notification-option input {
    width: 18px;
    height: 18px;
    accent-color: var(--color-primary);
    cursor: pointer;
  }

  .option-content {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .option-badge {
    display: inline-block;
    font-size: 0.6875rem;
    font-weight: 600;
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
    background: var(--color-surface);
    color: var(--color-text-secondary);
    width: fit-content;
  }

  .option-badge.urgent { background: rgba(239, 68, 68, 0.1); color: #dc2626; }
  .option-badge.warning { background: rgba(245, 158, 11, 0.1); color: #d97706; }
  .option-badge.danger { background: rgba(239, 68, 68, 0.1); color: #dc2626; }

  .option-title {
    font-size: 0.8125rem;
    color: var(--color-text);
  }

  .template-editor {
    background: var(--color-surface);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
    animation: fadeIn 0.3s ease;
  }

  .editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    background: var(--color-bg);
    border-bottom: 1px solid var(--color-border-light);
  }

  .editor-title {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .editor-badge {
    background: var(--color-primary);
    color: white;
    font-size: 0.6875rem;
    font-weight: 600;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .editor-title h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
  }

  .editor-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .editor-actions .btn-secondary,
  .editor-actions .btn-primary {
    padding: 0.5rem 0.875rem;
    font-size: 0.875rem;
  }

  .btn-close {
    padding: 0.375rem;
    background: transparent;
    border: none;
    color: var(--color-text-muted);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-close:hover {
    background: var(--color-surface);
    color: var(--color-text);
  }

  .editor-layout {
    display: grid;
    grid-template-columns: 360px 1fr;
    min-height: 700px;
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
  }

  .panel-label {
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-muted);
  }

  .loading-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-primary);
    animation: pulse 1s ease infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
  }

  .code-editor {
    flex: 1;
    padding: 0.75rem;
    border: none;
    resize: none;
    font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
    font-size: 0.75rem;
    line-height: 1.5;
    background: var(--color-surface);
    color: var(--color-text);
    min-height: 200px;
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
    display: flex;
    flex-direction: column;
  }

  .preview-frame iframe {
    width: 100%;
    flex: 1;
    min-height: 600px;
    border: 1px solid var(--color-border-light);
    border-radius: 8px;
    background: white;
  }

  .preview-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--color-text-muted);
    gap: 1rem;
  }

  .preview-placeholder svg {
    opacity: 0.3;
  }

  .preview-placeholder p {
    margin: 0;
    font-size: 0.875rem;
  }

  @media (max-width: 768px) {
    .tabs {
      flex-wrap: wrap;
    }

    .tabs button {
      min-width: calc(50% - 0.1875rem);
    }

    .partners-grid {
      grid-template-columns: 1fr;
    }

    .form-row,
    .form-row.three-col {
      grid-template-columns: 1fr;
    }

    .notification-grid {
      grid-template-columns: 1fr;
    }

    .editor-layout {
      grid-template-columns: 1fr;
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

    .section-header {
      flex-direction: column;
      gap: 1rem;
    }

    .section-header .btn-primary {
      width: 100%;
      justify-content: center;
    }

    .form-actions {
      flex-direction: column;
    }

    .form-actions button {
      width: 100%;
      justify-content: center;
    }
  }
</style>
