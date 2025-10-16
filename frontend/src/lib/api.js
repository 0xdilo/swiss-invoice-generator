const API = "http://localhost:8000";

export async function getClients() {
  return fetch(`${API}/clients`).then(r => r.json());
}
export async function addClient(client) {
  return fetch(`${API}/clients`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(client)
  }).then(r => r.json());
}
export async function updateClient(id, client) {
  return fetch(`${API}/clients/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(client)
  }).then(r => r.json());
}
export async function deleteClient(id) {
  return fetch(`${API}/clients/${id}`, { method: "DELETE" }).then(r => r.json());
}

export async function getTemplates() {
  return fetch(`${API}/templates`).then(r => r.json());
}


export async function uploadTemplate(name, htmlFile, cssFile) {
  const form = new FormData();
  form.append("name", name);
  form.append("html_file", htmlFile);
  form.append("css_file", cssFile);
  return fetch(`${API}/templates`, { method: "POST", body: form }).then(r => r.json());
}
export async function updateTemplate(id, name, htmlFile, cssFile) {
  const form = new FormData();
  form.append("name", name);
  if (htmlFile) form.append("html_file", htmlFile);
  if (cssFile) form.append("css_file", cssFile);
  return fetch(`${API}/templates/${id}`, { method: "PUT", body: form }).then(r => r.json());
}



export async function deleteTemplate(id) {
  return fetch(`${API}/templates/${id}`, { method: "DELETE" }).then(r => r.json());
}
export async function getTemplateFields(id) {
  return fetch(`${API}/templates/${id}/fields`).then(r => r.json());
}

export async function getInvoices() {
  return fetch(`${API}/invoices`).then(r => r.json());
}
export async function createInvoice(client_id, template_id, data, logoFile) {
  const form = new FormData();
  form.append("client_id", client_id);
  form.append("template_id", template_id);
  form.append("data", JSON.stringify(data));
  if (logoFile) {
    form.append("logo_file", logoFile);
  }
  return fetch(`${API}/invoices`, { method: "POST", body: form }).then(r => r.json());
}
export async function updateInvoice(id, client_id, template_id, data, logoFile) {
  const form = new FormData();
  form.append("client_id", client_id);
  form.append("template_id", template_id);
  form.append("data", JSON.stringify(data));
  if (logoFile) {
    form.append("logo_file", logoFile);
  }
  return fetch(`${API}/invoices/${id}`, {
    method: "PUT",
    body: form
  }).then(r => r.json());
}
export async function deleteInvoice(id) {
  return fetch(`${API}/invoices/${id}`, { method: "DELETE" }).then(r => r.json());
}

export async function getBankDetails() {
  return fetch(`${API}/bank-details`).then(r => r.json());
}
export async function updateBankDetails(details) {
  return fetch(`${API}/bank-details`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(details)
  }).then(r => r.json());
}
