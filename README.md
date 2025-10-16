# Swiss Invoice Generator

A web application for generating Swiss-compliant invoices with QR-bill support.  
Includes client management, customizable templates, and PDF export.
> This project was created for my own work needs. It's simple and useless.

---

## Features

- Swiss QR-bill generation
- Custom HTML/CSS invoice templates
- Client and bank details management
- Invoice creation, editing, and deletion
- PDF export

---

## Getting Started

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend will be available at [http://localhost:8000](http://localhost:8000).

### Frontend

```bash
cd frontend
bun install
bun run dev
```

The frontend will be available at [http://localhost:5173](http://localhost:5173).

---

## Template Variables

You can use any variable (tag) in your invoice HTML template.

**The following variables are automatically provided by the system and should NOT be manually filled in the invoice form.**  
They are always available in your template:

| Variable                | Description                        |
|-------------------------|------------------------------------|
| `{{ customer.name }}`   | Client name                        |
| `{{ customer.address }}`| Client address                     |
| `{{ customer.cap }}`    | Client postal code                 |
| `{{ customer.city }}`   | Client city                        |
| `{{ customer.nation }}` | Client country                     |
| `{{ customer.email }}`  | Client email                       |
| `{{ items }}`           | List of items (see below)          |
| `{{ subtotal }}`        | Total before taxes/discounts       |
| `{{ net_total }}`       | Final total                        |
| `{{ invoice_number }}`  | Invoice ID                         |
| `{{ date }}`            | Invoice date                       |
| `{{ notes }}`           | Notes                              |
| `{{ qr_image }}`        | QR-bill image                      |
| `{{ logo }}`            | Company logo (if uploaded)         |

**Do not add these fields in the invoice form.**  
They are automatically filled by the backend and always available for use in your template.

---

**You can also add any custom fields you want in the invoice form.**  
For example, if you add a field called `reference` in the form, you can use `{{ reference }}` in your template.

---

### Items Example

To display invoice items in your template, use:

```html
{% for item in items %}
  <tr>
    <td>{{ item.desc }}</td>
    <td>{{ item.qty }}</td>
    <td>{{ item.price }}</td>
    <td>{{ item.total }}</td>
  </tr>
{% endfor %}
```

---

## Configuration

- **Bank Details:** Set your IBAN and creditor info in the app.
- **Templates:** Upload your HTML and CSS files in the Templates section.
- **Logo:** If your template uses `{{ logo }}`, you can upload a logo when creating an invoice.

---

## File Structure

- `backend/templates/` — Invoice templates (HTML/CSS)
- `backend/results/` — Generated invoices and PDFs



