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

export async function getRecurringFees(clientId) {
  return fetch(`${API}/clients/${clientId}/recurring-fees`).then(r => r.json());
}
export async function addRecurringFee(clientId, fee) {
  return fetch(`${API}/clients/${clientId}/recurring-fees`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fee)
  }).then(r => r.json());
}
export async function updateRecurringFee(feeId, fee) {
  return fetch(`${API}/recurring-fees/${feeId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fee)
  }).then(r => r.json());
}
export async function deleteRecurringFee(feeId) {
  return fetch(`${API}/recurring-fees/${feeId}`, { method: "DELETE" }).then(r => r.json());
}

export async function getPaymentEvents(clientId = null, status = null) {
  let url = `${API}/payment-events`;
  const params = new URLSearchParams();
  if (clientId) params.append("client_id", clientId);
  if (status) params.append("status", status);
  if (params.toString()) url += `?${params.toString()}`;
  return fetch(url).then(r => r.json());
}
export async function createPaymentEvent(event) {
  return fetch(`${API}/payment-events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event)
  }).then(r => r.json());
}
export async function generatePaymentEvents(params = {}) {
  return fetch(`${API}/payment-events/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params)
  }).then(r => r.json());
}
export async function updatePaymentEvent(eventId, event) {
  return fetch(`${API}/payment-events/${eventId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event)
  }).then(r => r.json());
}
export async function deletePaymentEvent(eventId) {
  return fetch(`${API}/payment-events/${eventId}`, { method: "DELETE" }).then(r => r.json());
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
export async function getTemplateContent(id) {
  return fetch(`${API}/templates/${id}/content`).then(r => r.json());
}
export async function updateTemplateContent(id, content) {
  return fetch(`${API}/templates/${id}/content`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(content)
  }).then(r => r.json());
}
export async function previewTemplate(id) {
  return fetch(`${API}/templates/${id}/preview`, { method: "POST" }).then(r => r.json());
}

export async function getInvoices(clientId = null) {
  let url = `${API}/invoices`;
  if (clientId) url += `?client_id=${clientId}`;
  return fetch(url).then(r => r.json());
}

export async function getClientStats(clientId) {
  return fetch(`${API}/clients/${clientId}/stats`).then(r => r.json());
}
export async function createInvoice(client_id, template_id, data, logoFile, partner_a_share = 50, partner_b_share = 50, title = "", description = "") {
  const form = new FormData();
  form.append("client_id", client_id);
  form.append("template_id", template_id);
  form.append("data", JSON.stringify(data));
  form.append("partner_a_share", partner_a_share);
  form.append("partner_b_share", partner_b_share);
  form.append("title", title);
  form.append("description", description);
  if (logoFile) {
    form.append("logo_file", logoFile);
  }
  return fetch(`${API}/invoices`, { method: "POST", body: form }).then(r => r.json());
}
export async function updateInvoice(id, client_id, template_id, data, logoFile, partner_a_share = 50, partner_b_share = 50, title = "", description = "") {
  const form = new FormData();
  form.append("client_id", client_id);
  form.append("template_id", template_id);
  form.append("data", JSON.stringify(data));
  form.append("partner_a_share", partner_a_share);
  form.append("partner_b_share", partner_b_share);
  form.append("title", title);
  form.append("description", description);
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
export async function updateInvoiceStatus(id, status, paidDate = null) {
  const body = { status };
  if (paidDate) body.paid_date = paidDate;
  return fetch(`${API}/invoices/${id}/status`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  }).then(r => r.json());
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

export async function getPartners() {
  return fetch(`${API}/partners`).then(r => r.json());
}
export async function updatePartner(id, data) {
  return fetch(`${API}/partners/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  }).then(r => r.json());
}

export async function getExpenses(filters = {}) {
  const params = new URLSearchParams();
  if (filters.category) params.append("category", filters.category);
  if (filters.expense_type) params.append("expense_type", filters.expense_type);
  if (filters.status) params.append("status", filters.status);
  if (filters.date_from) params.append("date_from", filters.date_from);
  if (filters.date_to) params.append("date_to", filters.date_to);
  const url = params.toString() ? `${API}/expenses?${params}` : `${API}/expenses`;
  return fetch(url).then(r => r.json());
}
export async function createExpense(expense) {
  return fetch(`${API}/expenses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(expense)
  }).then(r => r.json());
}
export async function updateExpense(id, expense) {
  return fetch(`${API}/expenses/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(expense)
  }).then(r => r.json());
}
export async function deleteExpense(id) {
  return fetch(`${API}/expenses/${id}`, { method: "DELETE" }).then(r => r.json());
}
export async function getExpenseBalance() {
  return fetch(`${API}/expenses/balance`).then(r => r.json());
}

export async function getSettlements() {
  return fetch(`${API}/settlements`).then(r => r.json());
}
export async function createSettlement(settlement) {
  return fetch(`${API}/settlements`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settlement)
  }).then(r => r.json());
}

export async function getDashboardStats(period = "all") {
  return fetch(`${API}/dashboard/stats?period=${period}`).then(r => r.json());
}
export async function getDashboardRenewals(days = 30) {
  return fetch(`${API}/dashboard/renewals?days=${days}`).then(r => r.json());
}
export async function getDashboardOutstanding() {
  return fetch(`${API}/dashboard/outstanding`).then(r => r.json());
}
export async function getPartnerEarnings(period = "all") {
  return fetch(`${API}/dashboard/partner-earnings?period=${period}`).then(r => r.json());
}

export async function getTelegramConfig() {
  return fetch(`${API}/telegram/config`).then(r => r.json());
}
export async function updateTelegramConfig(config) {
  return fetch(`${API}/telegram/config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config)
  }).then(r => r.json());
}
export async function testTelegramNotification() {
  return fetch(`${API}/telegram/test`, { method: "POST" }).then(r => r.json());
}
export async function checkTelegramNotifications() {
  return fetch(`${API}/telegram/check`, { method: "POST" }).then(r => r.json());
}

export async function generateInvoiceFromRecurring(feeId) {
  return fetch(`${API}/recurring-fees/${feeId}/generate-invoice`, { method: "POST" }).then(r => r.json());
}

export async function getTodos(filters = {}) {
  const params = new URLSearchParams();
  if (filters.status) params.append("status", filters.status);
  if (filters.priority) params.append("priority", filters.priority);
  if (filters.client_id) params.append("client_id", filters.client_id);
  const url = params.toString() ? `${API}/todos?${params}` : `${API}/todos`;
  return fetch(url).then(r => r.json());
}
export async function createTodo(todo) {
  return fetch(`${API}/todos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(todo)
  }).then(r => r.json());
}
export async function updateTodo(id, todo) {
  return fetch(`${API}/todos/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(todo)
  }).then(r => r.json());
}
export async function deleteTodo(id) {
  return fetch(`${API}/todos/${id}`, { method: "DELETE" }).then(r => r.json());
}

export async function getCalendarEvents(filters = {}) {
  const params = new URLSearchParams();
  if (filters.start) params.append("start", filters.start);
  if (filters.end) params.append("end", filters.end);
  if (filters.client_id) params.append("client_id", filters.client_id);
  const url = params.toString() ? `${API}/calendar/events?${params}` : `${API}/calendar/events`;
  return fetch(url).then(r => r.json());
}
export async function createCalendarEvent(event) {
  return fetch(`${API}/calendar/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event)
  }).then(r => r.json());
}
export async function updateCalendarEvent(id, event) {
  return fetch(`${API}/calendar/events/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event)
  }).then(r => r.json());
}
export async function deleteCalendarEvent(id) {
  return fetch(`${API}/calendar/events/${id}`, { method: "DELETE" }).then(r => r.json());
}
