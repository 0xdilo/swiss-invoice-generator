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

<div class="max-w-[900px] mx-auto">
  <header class="mb-6">
    <h1 class="text-[1.75rem] font-bold m-0 tracking-[-0.03em]">Settings</h1>
    <p class="mt-1 mb-0 text-text-secondary text-[0.9375rem]">Manage your business configuration</p>
  </header>

  {#if message}
    <div class="flex items-center gap-3 px-5 py-4 mb-6 rounded-xl font-medium {messageType === 'success' ? 'bg-emerald-500/10 text-emerald-600' : 'bg-red-500/10 text-red-600'}" style="animation: slideIn 0.3s ease;">
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

  <div class="mb-8">
    <div class="flex gap-1.5 bg-surface p-1.5 rounded-xl shadow-sm">
      <button class="flex items-center gap-2 px-4 py-3 border-none rounded-[10px] text-[0.875rem] font-medium cursor-pointer transition-all duration-200 flex-1 justify-center {activeTab === 'partners' ? 'bg-primary text-white shadow-lg' : 'bg-transparent text-text-secondary hover:bg-bg hover:text-text'}" onclick={() => activeTab = "partners"}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
          <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
        Partners
      </button>
      <button class="flex items-center gap-2 px-4 py-3 border-none rounded-[10px] text-[0.875rem] font-medium cursor-pointer transition-all duration-200 flex-1 justify-center {activeTab === 'bank' ? 'bg-primary text-white shadow-lg' : 'bg-transparent text-text-secondary hover:bg-bg hover:text-text'}" onclick={() => activeTab = "bank"}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>
          <line x1="1" y1="10" x2="23" y2="10"/>
        </svg>
        Bank & QR
      </button>
      <button class="flex items-center gap-2 px-4 py-3 border-none rounded-[10px] text-[0.875rem] font-medium cursor-pointer transition-all duration-200 flex-1 justify-center {activeTab === 'templates' ? 'bg-primary text-white shadow-lg' : 'bg-transparent text-text-secondary hover:bg-bg hover:text-text'}" onclick={() => activeTab = "templates"}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <line x1="3" y1="9" x2="21" y2="9"/>
          <line x1="9" y1="21" x2="9" y2="9"/>
        </svg>
        Templates
      </button>
      <button class="flex items-center gap-2 px-4 py-3 border-none rounded-[10px] text-[0.875rem] font-medium cursor-pointer transition-all duration-200 flex-1 justify-center {activeTab === 'telegram' ? 'bg-primary text-white shadow-lg' : 'bg-transparent text-text-secondary hover:bg-bg hover:text-text'}" onclick={() => activeTab = "telegram"}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 2L11 13"/>
          <path d="M22 2L15 22L11 13L2 9L22 2Z"/>
        </svg>
        Notifications
      </button>
    </div>
  </div>

  {#if activeTab === "partners"}
    <div class="animate-fade-in">
      <div class="flex justify-between items-start mb-6">
        <div>
          <h2 class="text-lg font-semibold m-0 mb-1">Partners</h2>
          <p class="m-0 text-[0.875rem] text-text-secondary">Configure partner names and default revenue sharing</p>
        </div>
      </div>
      <div class="grid grid-cols-[repeat(auto-fit,minmax(320px,1fr))] gap-6">
        {#each partners as partner, i}
          <div class="bg-surface rounded-2xl overflow-hidden shadow-sm">
            <div class="h-1" style="background: {partner.color}"></div>
            <div class="p-6">
              <div class="flex items-center gap-3.5 mb-6">
                <input type="color" bind:value={partner.color} class="w-12 h-12 p-0 border-none rounded-xl cursor-pointer flex-shrink-0" />
                <input type="text" bind:value={partner.name} placeholder="Partner name" class="flex-1 text-xl font-semibold px-3 py-2 border border-transparent rounded-lg bg-transparent transition-all duration-200 hover:bg-bg hover:border-border focus:bg-bg focus:border-border focus:outline-none" />
              </div>

              <div class="mb-4">
                <label class="form-label">Default Share</label>
                <div class="relative">
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="1"
                    value={partner.default_share}
                    oninput={(e) => updatePartnerShare(i, e.target.value)}
                    class="form-input pr-10"
                  />
                  <span class="absolute right-3.5 top-1/2 -translate-y-1/2 text-text-muted font-medium">%</span>
                </div>
              </div>

              <div class="mb-4">
                <label class="form-label">Telegram Chat ID</label>
                <input type="text" bind:value={partner.telegram_chat_id} placeholder="e.g. 123456789" class="form-input" />
              </div>

              <button class="w-full flex items-center justify-center gap-2 px-3 py-3 mt-2 text-white border-none rounded-[10px] text-[0.9375rem] font-semibold cursor-pointer transition-all duration-200 hover:brightness-110 hover:-translate-y-px" style="background: {partner.color}" onclick={() => savePartner(partner)}>
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
    <div class="animate-fade-in">
      <div class="flex justify-between items-start mb-6">
        <div>
          <h2 class="text-lg font-semibold m-0 mb-1">Bank & Creditor Details</h2>
          <p class="m-0 text-[0.875rem] text-text-secondary">Used for Swiss QR bill generation on invoices</p>
        </div>
      </div>

      <form class="flex flex-col gap-6" onsubmit={(e) => { e.preventDefault(); saveBankDetails(); }}>
        <div class="card">
          <div class="flex items-center gap-3 px-6 py-4 bg-bg border-b border-border-light">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-primary">
              <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>
              <line x1="1" y1="10" x2="23" y2="10"/>
            </svg>
            <h3 class="m-0 text-[0.9375rem] font-semibold">Bank Information</h3>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-2 gap-4">
              <div class="mb-4">
                <label class="form-label">IBAN</label>
                <input type="text" bind:value={bankDetails.iban} placeholder="CH00 0000 0000 0000 0000 0" required class="form-input" />
              </div>
              <div class="mb-4">
                <label class="form-label">BIC / SWIFT</label>
                <input type="text" bind:value={bankDetails.bic} placeholder="BANKCHXX" required class="form-input" />
              </div>
            </div>
            <div class="mb-4">
              <label class="form-label">Bank Name</label>
              <input type="text" bind:value={bankDetails.bank_name} placeholder="Bank name" required class="form-input" />
            </div>
            <div class="mb-4">
              <label class="form-label">Bank Address</label>
              <input type="text" bind:value={bankDetails.bank_address} placeholder="Bank address" required class="form-input" />
            </div>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center gap-3 px-6 py-4 bg-bg border-b border-border-light">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-primary">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            <h3 class="m-0 text-[0.9375rem] font-semibold">Creditor Information</h3>
          </div>
          <div class="p-6">
            <div class="mb-4">
              <label class="form-label">Creditor Name</label>
              <input type="text" bind:value={bankDetails.creditor_name} placeholder="Your company name" required class="form-input" />
            </div>
            <div class="mb-4">
              <label class="form-label">Street Address</label>
              <input type="text" bind:value={bankDetails.creditor_street} placeholder="Street address" required class="form-input" />
            </div>
            <div class="grid grid-cols-[1fr_2fr_1fr] gap-4">
              <div class="mb-4">
                <label class="form-label">Postal Code</label>
                <input type="text" bind:value={bankDetails.creditor_postalcode} placeholder="0000" required class="form-input" />
              </div>
              <div class="mb-4">
                <label class="form-label">City</label>
                <input type="text" bind:value={bankDetails.creditor_city} placeholder="City" required class="form-input" />
              </div>
              <div class="mb-4">
                <label class="form-label">Country</label>
                <input type="text" bind:value={bankDetails.creditor_country} placeholder="CH" required class="form-input" />
              </div>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-3">
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
      <div class="bg-surface rounded-2xl overflow-hidden shadow-sm animate-fade-in">
        <div class="flex justify-between items-center px-6 py-4 bg-bg border-b border-border-light">
          <div class="flex items-center gap-3">
            <span class="bg-primary text-white text-[0.6875rem] font-semibold px-2 py-1 rounded-md uppercase tracking-wider">Editing</span>
            <h3 class="m-0 text-base font-semibold">{selectedTemplate.name}</h3>
          </div>
          <div class="flex gap-2 items-center">
            <button class="btn-secondary text-[0.875rem] px-3.5 py-2" onclick={refreshPreview} disabled={previewLoading}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 4 23 10 17 10"/>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
              </svg>
              Refresh
            </button>
            <button class="btn-primary text-[0.875rem] px-3.5 py-2" onclick={saveTemplateContent} disabled={savingTemplate}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              {savingTemplate ? "Saving..." : "Save"}
            </button>
            <button class="p-1.5 bg-transparent border-none text-text-muted rounded-md cursor-pointer transition-all duration-150 hover:bg-surface hover:text-text" onclick={closeTemplateEditor}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="grid grid-cols-[360px_1fr] min-h-[700px]">
          <div class="flex flex-col border-r border-border-light">
            <div class="flex-1 flex flex-col border-b border-border-light">
              <div class="flex justify-between items-center px-4 py-2.5 bg-bg border-b border-border-light">
                <span class="text-[0.6875rem] font-semibold uppercase tracking-wider text-text-muted">HTML</span>
              </div>
              <textarea class="flex-1 p-3 border-none resize-none font-mono text-xs leading-6 bg-surface text-text min-h-[200px] focus:outline-none focus:shadow-[inset_0_0_0_2px] focus:shadow-primary/20" bind:value={templateHtml} spellcheck="false"></textarea>
            </div>
            <div class="flex-1 flex flex-col">
              <div class="flex justify-between items-center px-4 py-2.5 bg-bg border-b border-border-light">
                <span class="text-[0.6875rem] font-semibold uppercase tracking-wider text-text-muted">CSS</span>
              </div>
              <textarea class="flex-1 p-3 border-none resize-none font-mono text-xs leading-6 bg-surface text-text min-h-[200px] focus:outline-none focus:shadow-[inset_0_0_0_2px] focus:shadow-primary/20" bind:value={templateCss} spellcheck="false"></textarea>
            </div>
          </div>
          <div class="flex flex-col bg-bg">
            <div class="flex justify-between items-center px-4 py-2.5 bg-bg border-b border-border-light">
              <span class="text-[0.6875rem] font-semibold uppercase tracking-wider text-text-muted">Preview</span>
              {#if previewLoading}
                <span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              {/if}
            </div>
            <div class="flex-1 p-4 overflow-auto flex flex-col">
              {#if templatePreview}
                <iframe srcdoc={templatePreview} title="Template Preview" sandbox="allow-same-origin" class="w-full flex-1 min-h-[600px] border border-border-light rounded-lg bg-white"></iframe>
              {:else}
                <div class="flex flex-col items-center justify-center h-full text-text-muted gap-4">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" class="opacity-30">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                  <p class="m-0 text-[0.875rem]">Click "Refresh" to preview</p>
                </div>
              {/if}
            </div>
          </div>
        </div>
      </div>
    {:else}
      <div class="animate-fade-in">
        <div class="flex justify-between items-start mb-6">
          <div>
            <h2 class="text-lg font-semibold m-0 mb-1">Invoice Templates</h2>
            <p class="m-0 text-[0.875rem] text-text-secondary">Upload and edit HTML/CSS templates for invoice generation</p>
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
          <form class="bg-surface rounded-2xl p-6 mb-6 relative shadow-sm" style="animation: slideIn 0.3s ease;" onsubmit={(e) => { e.preventDefault(); submitTemplate(); }}>
            <div class="absolute top-4 right-4 bg-primary text-white text-[0.6875rem] font-semibold px-2 py-1 rounded-md uppercase tracking-wider">{editingTemplate !== null ? "Edit" : "New"}</div>
            <div class="grid grid-cols-[1fr_1fr_1fr] gap-4">
              <div class="mb-4">
                <label class="form-label">Template Name</label>
                <input type="text" bind:value={templateForm.name} placeholder="e.g. Standard Invoice" required class="form-input" />
              </div>
              <div class="mb-4">
                <label class="form-label">HTML File</label>
                <input type="file" accept=".html" bind:files={templateForm.htmlFile} required={!editingTemplate} class="form-input" />
              </div>
              <div class="mb-4">
                <label class="form-label">CSS File</label>
                <input type="file" accept=".css" bind:files={templateForm.cssFile} required={!editingTemplate} class="form-input" />
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-4 pt-4 border-t border-border-light">
              <button type="button" class="btn-cancel" onclick={cancelTemplateEdit}>Cancel</button>
              <button type="submit" class="btn-primary">
                {editingTemplate !== null ? "Update Template" : "Upload Template"}
              </button>
            </div>
          </form>
        {/if}

        {#if templates.length > 0}
          <div class="flex flex-col gap-3">
            {#each templates as t, i}
              <div class="flex items-center gap-4 px-5 py-4 bg-surface rounded-xl shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-px animate-fade-in" style="animation-delay: {i * 50}ms">
                <div class="w-12 h-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <polyline points="10 9 9 9 8 9"/>
                  </svg>
                </div>
                <div class="flex-1 flex flex-col gap-0.5">
                  <span class="font-semibold text-[0.9375rem]">{t.name}</span>
                  <span class="text-xs text-text-muted">Invoice template</span>
                </div>
                <div class="flex gap-2">
                  <button class="flex items-center gap-1.5 px-3.5 py-2 border-none rounded-lg text-[0.8125rem] font-medium cursor-pointer transition-all duration-150 bg-primary text-white hover:bg-primary/90" onclick={() => selectTemplateForEdit(t)}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                    Edit
                  </button>
                  <button class="flex items-center gap-1.5 px-3.5 py-2 border-none rounded-lg text-[0.8125rem] font-medium cursor-pointer transition-all duration-150 bg-transparent text-text-muted hover:bg-red-500/10 hover:text-red-500" onclick={() => removeTemplate(t.id)}>
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
          <div class="flex flex-col items-center justify-center py-16 px-8 bg-surface rounded-2xl text-center">
            <div class="w-24 h-24 rounded-full bg-bg flex items-center justify-center mb-6 text-text-muted opacity-50">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="3" y1="9" x2="21" y2="9"/>
                <line x1="9" y1="21" x2="9" y2="9"/>
              </svg>
            </div>
            <p class="text-text-secondary m-0 mb-6">No templates uploaded yet</p>
            <button class="btn-primary" onclick={() => showUploadForm = true}>Upload your first template</button>
          </div>
        {/if}
      </div>
    {/if}
  {/if}

  {#if activeTab === "telegram"}
    <div class="animate-fade-in">
      <div class="flex justify-between items-start mb-6">
        <div>
          <h2 class="text-lg font-semibold m-0 mb-1">Telegram Notifications</h2>
          <p class="m-0 text-[0.875rem] text-text-secondary">Set up Telegram bot for renewal reminders and alerts</p>
        </div>
      </div>

      <div class="flex flex-col gap-6">
        <div class="card">
          <div class="flex items-center gap-3 px-6 py-4 bg-bg border-b border-border-light">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-primary">
              <path d="M22 2L11 13"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z"/>
            </svg>
            <h3 class="m-0 text-[0.9375rem] font-semibold">Bot Configuration</h3>
          </div>
          <div class="p-6">
            <div class="mb-4">
              <label class="form-label">Bot Token</label>
              <input type="password" bind:value={telegramConfig.bot_token} placeholder="Get this from @BotFather" class="form-input" />
            </div>

            <label class="flex items-start gap-3.5 cursor-pointer p-4 bg-bg rounded-[10px] mt-4">
              <input type="checkbox" bind:checked={telegramConfig.enabled} class="hidden" />
              <div class="w-11 h-6 rounded-xl relative transition-colors duration-200 flex-shrink-0 {telegramConfig.enabled ? 'bg-primary' : 'bg-border'}">
                <div class="absolute top-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-200 {telegramConfig.enabled ? 'left-[22px]' : 'left-0.5'}"></div>
              </div>
              <div class="flex flex-col gap-0.5">
                <span class="font-semibold text-[0.9375rem]">Enable Notifications</span>
                <span class="text-[0.8125rem] text-text-secondary">Receive alerts via Telegram</span>
              </div>
            </label>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center gap-3 px-6 py-4 bg-bg border-b border-border-light">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-primary">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <h3 class="m-0 text-[0.9375rem] font-semibold">Notification Types</h3>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-2 gap-3">
              <label class="flex items-center gap-3 p-4 bg-bg rounded-[10px] cursor-pointer transition-all duration-200 hover:bg-border-light">
                <input type="checkbox" bind:checked={telegramConfig.notify_renewals_7d} class="w-[18px] h-[18px] accent-primary cursor-pointer" />
                <div class="flex flex-col gap-1">
                  <span class="inline-block text-[0.6875rem] font-semibold px-2 py-0.5 rounded bg-red-500/10 text-red-600 w-fit">7 days</span>
                  <span class="text-[0.8125rem] text-text">Urgent renewals</span>
                </div>
              </label>
              <label class="flex items-center gap-3 p-4 bg-bg rounded-[10px] cursor-pointer transition-all duration-200 hover:bg-border-light">
                <input type="checkbox" bind:checked={telegramConfig.notify_renewals_14d} class="w-[18px] h-[18px] accent-primary cursor-pointer" />
                <div class="flex flex-col gap-1">
                  <span class="inline-block text-[0.6875rem] font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-600 w-fit">14 days</span>
                  <span class="text-[0.8125rem] text-text">Upcoming renewals</span>
                </div>
              </label>
              <label class="flex items-center gap-3 p-4 bg-bg rounded-[10px] cursor-pointer transition-all duration-200 hover:bg-border-light">
                <input type="checkbox" bind:checked={telegramConfig.notify_renewals_30d} class="w-[18px] h-[18px] accent-primary cursor-pointer" />
                <div class="flex flex-col gap-1">
                  <span class="inline-block text-[0.6875rem] font-semibold px-2 py-0.5 rounded bg-surface text-text-secondary w-fit">30 days</span>
                  <span class="text-[0.8125rem] text-text">Early reminders</span>
                </div>
              </label>
              <label class="flex items-center gap-3 p-4 bg-bg rounded-[10px] cursor-pointer transition-all duration-200 hover:bg-border-light">
                <input type="checkbox" bind:checked={telegramConfig.notify_overdue} class="w-[18px] h-[18px] accent-primary cursor-pointer" />
                <div class="flex flex-col gap-1">
                  <span class="inline-block text-[0.6875rem] font-semibold px-2 py-0.5 rounded bg-red-500/10 text-red-600 w-fit">Overdue</span>
                  <span class="text-[0.8125rem] text-text">Payment alerts</span>
                </div>
              </label>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-3">
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
  @keyframes slideIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .btn-primary:disabled,
  .btn-secondary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-primary:disabled:hover,
  .btn-secondary:disabled:hover {
    transform: none;
  }

  @media (max-width: 768px) {
    .grid-cols-\[repeat\(auto-fit\,minmax\(320px\,1fr\)\)\] {
      grid-template-columns: 1fr;
    }

    .grid-cols-2 {
      grid-template-columns: 1fr;
    }

    .grid-cols-\[1fr_1fr_1fr\],
    .grid-cols-\[1fr_2fr_1fr\] {
      grid-template-columns: 1fr;
    }

    .grid-cols-\[360px_1fr\] {
      grid-template-columns: 1fr;
    }

    .flex.gap-1\.5.bg-surface {
      flex-wrap: wrap;
    }

    .flex.gap-1\.5.bg-surface > button {
      min-width: calc(50% - 0.1875rem);
    }

    .flex.justify-between.items-start button {
      width: 100%;
      justify-content: center;
    }

    .flex.justify-end.gap-3 {
      flex-direction: column;
    }

    .flex.justify-end.gap-3 button {
      width: 100%;
      justify-content: center;
    }
  }
</style>
