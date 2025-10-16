import os
import re
import json
import sqlite3
import base64
import io
import shutil
import secrets
from decimal import Decimal
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from qrbill import QRBill
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = "db.sqlite"
TEMPLATE_DIR = "templates"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

def db():
    return sqlite3.connect(DB)

def init_db():
    with db() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, address TEXT, cap TEXT, city TEXT, nation TEXT, email TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, template_dir TEXT, html_filename TEXT, css_filename TEXT, fields TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE,
            client_id INTEGER, template_id INTEGER, data TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS bank_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            iban TEXT, bank_name TEXT, bank_address TEXT, bic TEXT,
            creditor_name TEXT, creditor_street TEXT, creditor_postalcode TEXT,
            creditor_city TEXT, creditor_country TEXT
        )''')
        c.execute("SELECT COUNT(*) FROM bank_details")
        if c.fetchone()[0] == 0:
            c.execute('''INSERT INTO bank_details
                (iban, bank_name, bank_address, bic, creditor_name, creditor_street, creditor_postalcode, creditor_city, creditor_country)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                ("CH5800791123000889012", "My Bank", "Bankstrasse 1", "POFICHBEXXX",
                 "My Company AG", "My Street 1", "8000", "Zurich", "CH"))

        # Migration: Add invoice_number column if it doesn't exist
        c.execute("PRAGMA table_info(invoices)")
        columns = [col[1] for col in c.fetchall()]
        if "invoice_number" not in columns:
            c.execute("ALTER TABLE invoices ADD COLUMN invoice_number TEXT")
            # Populate invoice_number for existing invoices
            c.execute("SELECT id FROM invoices WHERE invoice_number IS NULL")
            for row in c.fetchall():
                invoice_id = row[0]
                # Generate unique invoice number
                while True:
                    new_invoice_number = generate_invoice_number()
                    c.execute("SELECT COUNT(*) FROM invoices WHERE invoice_number=?", (new_invoice_number,))
                    if c.fetchone()[0] == 0:
                        break
                c.execute("UPDATE invoices SET invoice_number=? WHERE id=?", (new_invoice_number, invoice_id))

        conn.commit()

init_db()

def generate_invoice_number():
    """Generate a short random invoice number (8 characters, alphanumeric uppercase)"""
    return ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))

def extract_jinja_fields(html: str):
    return list(set(re.findall(r"\{\{\s*([a-zA-Z0-9_\.]+)\s*\}\}", html)))

def generate_qr_bill_svg(amount, debtor, additional_info, bank_details, output_dir):
    """Generate QR bill SVG file and save it to the specified directory"""
    required_bank_fields = [
        "iban", "creditor_name", "creditor_street", "creditor_postalcode", "creditor_city", "creditor_country"
    ]
    for field in required_bank_fields:
        if not bank_details.get(field):
            raise Exception(f"Bank detail '{field}' is missing or empty.")

    for k in ["name", "street", "pcode", "city", "country"]:
        if not debtor.get(k):
            raise Exception(f"Debtor information '{k}' is incomplete.")

    if not amount or float(amount) <= 0:
        raise Exception("Amount must be greater than zero.")

    bill = QRBill(
        account=bank_details["iban"],
        creditor={
            "name": bank_details["creditor_name"],
            "street": bank_details["creditor_street"],
            "pcode": bank_details["creditor_postalcode"],
            "city": bank_details["creditor_city"], 
            "country": bank_details["creditor_country"],
        },
        amount=str(amount),
        debtor=debtor,
    )
    
    os.makedirs(output_dir, exist_ok=True)
    
    svg_path = os.path.join(output_dir, "qr_bill.svg")
    with open(svg_path, "w", encoding="utf-8") as svg_file:
        bill.as_svg(svg_file)
    
    return svg_path

def copy_asset_if_exists(src_path, dest_dir):
    """Copy a file to dest_dir if it exists."""
    if os.path.exists(src_path):
        shutil.copy(src_path, os.path.join(dest_dir, os.path.basename(src_path)))

def to_swiss_date(date_str):
    """Convert YYYY-MM-DD or ISO date to DD.MM.YYYY. If already Swiss, return as is."""
    if not date_str:
        return ""
    if '.' in date_str and len(date_str.split('.')) == 3:
        return date_str
    try:
        parts = date_str[:10].split('-')
        if len(parts) == 3:
            year, month, day = parts
            return f"{day}.{month}.{year}"
    except Exception:
        pass
    return date_str

@app.get("/clients")
def get_clients():
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM clients")
        rows = c.fetchall()
        return [dict(zip([col[0] for col in c.description], row)) for row in rows]

@app.post("/clients")
def add_client(client: dict):
    with db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO clients (name, address, cap, city, nation, email) VALUES (?, ?, ?, ?, ?, ?)",
            (client["name"], client["address"], client["cap"], client["city"], client["nation"], client["email"])
        )
        conn.commit()
        return {"id": c.lastrowid}

@app.put("/clients/{client_id}")
def update_client(client_id: int, client: dict):
    with db() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE clients SET name=?, address=?, cap=?, city=?, nation=?, email=? WHERE id=?",
            (client["name"], client["address"], client["cap"], client["city"], client["nation"], client["email"], client_id)
        )
        conn.commit()
        return {"ok": True}

@app.delete("/clients/{client_id}")
def delete_client(client_id: int):
    with db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM clients WHERE id=?", (client_id,))
        conn.commit()
        return {"ok": True}

@app.get("/bank-details")
def get_bank_details():
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM bank_details LIMIT 1")
        row = c.fetchone()
        return dict(zip([col[0] for col in c.description], row)) if row else {}

@app.put("/bank-details")
def update_bank_details(details: dict = Body(...)):
    with db() as conn:
        c = conn.cursor()
        c.execute("UPDATE bank_details SET iban=?, bank_name=?, bank_address=?, bic=?, creditor_name=?, creditor_street=?, creditor_postalcode=?, creditor_city=?, creditor_country=? WHERE id=1",
            (details["iban"], details["bank_name"], details["bank_address"], details["bic"],
             details["creditor_name"], details["creditor_street"], details["creditor_postalcode"],
             details["creditor_city"], details["creditor_country"]))
        conn.commit()
        return {"ok": True}

@app.get("/templates")
def get_templates():
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM templates")
        rows = c.fetchall()
        return [dict(zip([col[0] for col in c.description], row)) for row in rows]

@app.post("/templates")
def upload_template(
    name: str = Form(...),
    html_file: UploadFile = File(...),
    css_file: UploadFile = File(...)
):
    template_dir_path = os.path.join(TEMPLATE_DIR, name)
    os.makedirs(template_dir_path, exist_ok=True)
    html_filename = html_file.filename
    css_filename = css_file.filename
    html_path = os.path.join(template_dir_path, html_filename)
    css_path = os.path.join(template_dir_path, css_filename)
    with open(html_path, "wb") as f:
        f.write(html_file.file.read())
    with open(css_path, "wb") as f:
        f.write(css_file.file.read())
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    fields = extract_jinja_fields(html_content)
    with db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO templates (name, template_dir, html_filename, css_filename, fields) VALUES (?, ?, ?, ?, ?)",
                  (name, name, html_filename, css_filename, json.dumps(fields)))
        conn.commit()
        return {"id": c.lastrowid, "fields": fields}

@app.put("/templates/{template_id}")
def update_template(
    template_id: int,
    name: str = Form(...),
    html_file: UploadFile = File(None),
    css_file: UploadFile = File(None)
):
    with db() as conn:
        c = conn.cursor()
        
        c.execute("SELECT template_dir FROM templates WHERE id=?", (template_id,))
        current = c.fetchone()
        if not current:
            raise HTTPException(404, "Template not found")
            
        current_dir = current[0]
        
        template_dir_path = os.path.join(TEMPLATE_DIR, name)
        os.makedirs(template_dir_path, exist_ok=True)
        
        if html_file and css_file:
            html_filename = html_file.filename
            css_filename = css_file.filename
            html_path = os.path.join(template_dir_path, html_filename)
            css_path = os.path.join(template_dir_path, css_filename)
            
            with open(html_path, "wb") as f:
                f.write(html_file.file.read())
            with open(css_path, "wb") as f:
                f.write(css_file.file.read())
                
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
                
            fields = extract_jinja_fields(html_content)
            c.execute("UPDATE templates SET name=?, template_dir=?, html_filename=?, css_filename=?, fields=? WHERE id=?",
                     (name, name, html_filename, css_filename, json.dumps(fields), template_id))
                     
        elif html_file:
            html_filename = html_file.filename
            html_path = os.path.join(template_dir_path, html_filename)
            
            with open(html_path, "wb") as f:
                f.write(html_file.file.read())
                
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
                
            fields = extract_jinja_fields(html_content)
            c.execute("UPDATE templates SET name=?, template_dir=?, html_filename=?, fields=? WHERE id=?",
                     (name, name, html_filename, json.dumps(fields), template_id))
                     
        elif css_file:
            css_filename = css_file.filename
            css_path = os.path.join(template_dir_path, css_filename)
            
            with open(css_path, "wb") as f:
                f.write(css_file.file.read())
                
            c.execute("UPDATE templates SET name=?, template_dir=?, css_filename=? WHERE id=?",
                     (name, name, css_filename, template_id))
        else:
            c.execute("SELECT html_filename, css_filename FROM templates WHERE id=?", (template_id,))
            files = c.fetchone()
            if files and files[0] and files[1]:
                old_dir_path = os.path.join(TEMPLATE_DIR, current_dir)
                
                if os.path.exists(old_dir_path) and current_dir != name:
                    for filename in os.listdir(old_dir_path):
                        old_file_path = os.path.join(old_dir_path, filename)
                        new_file_path = os.path.join(template_dir_path, filename)
                        if os.path.isfile(old_file_path):
                            shutil.copy(old_file_path, new_file_path)
                            
            c.execute("UPDATE templates SET name=?, template_dir=? WHERE id=?", 
                     (name, name, template_id))
                     
        conn.commit()
        return {"ok": True}

@app.delete("/templates/{template_id}")
def delete_template(template_id: int):
    with db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM templates WHERE id=?", (template_id,))
        conn.commit()
        return {"ok": True}

@app.get("/templates/{template_id}/fields")
def get_template_fields(template_id: int):
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT fields FROM templates WHERE id=?", (template_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(404, "Template not found")
        return {"fields": json.loads(row[0])}

@app.get("/invoices")
def get_invoices():
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM invoices")
        rows = c.fetchall()
        return [dict(zip([col[0] for col in c.description], row)) for row in rows]

@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int):
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(404, "Invoice not found")
        return dict(zip([col[0] for col in c.description], row))

@app.post("/invoices")
async def create_invoice(
    client_id: int = Form(...),
    template_id: int = Form(...),
    data: str = Form(...),
    logo_file: UploadFile = File(None)
):
    RESULTS_DIR = "results"
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    with db() as conn:
        c = conn.cursor()
        # Generate unique invoice number
        while True:
            invoice_number = generate_invoice_number()
            c.execute("SELECT COUNT(*) FROM invoices WHERE invoice_number=?", (invoice_number,))
            if c.fetchone()[0] == 0:
                break
        c.execute("INSERT INTO invoices (invoice_number, client_id, template_id, data) VALUES (?, ?, ?, ?)",
                  (invoice_number, client_id, template_id, data))
        conn.commit()
        invoice_id = c.lastrowid

        c.execute("SELECT template_dir, html_filename, css_filename FROM templates WHERE id=?", (template_id,))
        tpl = c.fetchone()
        if not tpl:
            raise HTTPException(404, "Template not found")
        template_dir_name, html_filename, css_filename = tpl
        template_dir_path = os.path.join(TEMPLATE_DIR, template_dir_name)
        css_path = os.path.join(template_dir_path, css_filename)

        c.execute("SELECT * FROM clients WHERE id=?", (client_id,))
        client_row = c.fetchone()
        client_dict = dict(zip([col[0] for col in c.description], client_row))
        
        client_dict["zip"] = client_dict["cap"]  
        client_dict["formatted_city"] = f"{client_dict['city']}, {client_dict['cap']}"
        client_dict["country"] = client_dict.get("nation") or "CH"

        c.execute("SELECT * FROM bank_details LIMIT 1")
        bank_row = c.fetchone()
        bank_details = dict(zip([col[0] for col in c.description], bank_row))

        invoice_data = json.loads(data)
        items = invoice_data.get("items", [])

        for item in items:
            item["total"] = float(item["price"]) * float(item["qty"])
            item["price"] = f"{float(item['price']):.2f}"
            item["total"] = f"{item['total']:.2f}"

        subtotal = sum(float(item["total"]) for item in items)
        net_total = subtotal  
        subtotal = f"{subtotal:.2f}"
        net_total = f"{net_total:.2f}"

        debtor = {
            "name": client_dict["name"],
            "street": client_dict["address"],
            "pcode": client_dict["cap"], 
            "city": client_dict["city"],
            "country": client_dict["country"]
        }
        additional_info = invoice_data.get("notes", "")

        invoice_dir = os.path.join(RESULTS_DIR, f"invoice_{invoice_id}")
        os.makedirs(invoice_dir, exist_ok=True)

        qr_svg_path = None
        qr_svg_rel_path = ""
        try:
            qr_svg_path = generate_qr_bill_svg(net_total, debtor, additional_info, bank_details, invoice_dir)
            qr_svg_rel_path = os.path.basename(qr_svg_path)  
        except Exception as e:
            print(f"QR-bill generation failed for invoice {invoice_id}: {e}")
            qr_svg_rel_path = ""

        logo_rel_path = None
        if logo_file:
            original_filename = logo_file.filename
            extension = os.path.splitext(original_filename)[1] if '.' in original_filename else '.png'
            saved_logo_filename = f"uploaded_logo{extension}"
            logo_save_path = os.path.join(invoice_dir, saved_logo_filename)
            with open(logo_save_path, "wb") as buffer:
                shutil.copyfileobj(logo_file.file, buffer)
            logo_rel_path = saved_logo_filename
            await logo_file.close()  

        customer_dict = client_dict.copy()
        
        invoice_date_raw = invoice_data.get("date") or ""
        invoice_date = to_swiss_date(invoice_date_raw)
        
        invoice_data_copy = invoice_data.copy()
        for k in ["date", "invoice_date"]:
            if k in invoice_data_copy:
                del invoice_data_copy[k]

        context = {
            "client": client_dict,
            "customer": customer_dict,
            "qr_image": qr_svg_rel_path,
            "items": items,
            "subtotal": subtotal,
            "net_total": net_total,
            "total": net_total,
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "date": invoice_date,
            "logo": logo_rel_path,
            **invoice_data_copy
        }

        shutil.copy(css_path, os.path.join(invoice_dir, css_filename))
        
        for asset in ["logo.png", "qr.png"]:
            asset_path = os.path.join(template_dir_path, asset)
            copy_asset_if_exists(asset_path, invoice_dir)

        env = Environment(loader=FileSystemLoader(template_dir_path))
        template = env.get_template(html_filename)
        html_content_rendered = template.render(**context)
        
        if qr_svg_rel_path and os.path.exists(os.path.join(invoice_dir, qr_svg_rel_path)):
            html_content_rendered = re.sub(r'\{\{\s*qr_image\s*\}\}', 
                                          f'<img src="{qr_svg_rel_path}" alt="QR Bill" />', 
                                          html_content_rendered)

        if logo_rel_path and os.path.exists(os.path.join(invoice_dir, logo_rel_path)):
            html_content_rendered = re.sub(r'\{\{\s*logo\s*\}\}',
                                          f'<img src="{logo_rel_path}" alt="Company Logo" style="max-height:100px; width:auto;" />',
                                          html_content_rendered)
        
        rendered_html_path = os.path.join(invoice_dir, "rendered.html")
        with open(rendered_html_path, "w", encoding="utf-8") as f:
            f.write(html_content_rendered)

        pdf_path = os.path.join(invoice_dir, "invoice.pdf")
        HTML(filename=rendered_html_path, base_url=f"file://{os.path.abspath(invoice_dir)}/").write_pdf(pdf_path)

        return {
            "id": invoice_id,
            "html": rendered_html_path,
            "pdf": pdf_path
        }

@app.put("/invoices/{invoice_id}")
async def update_invoice(
    invoice_id: int, 
    client_id: int = Form(...),
    template_id: int = Form(...),
    data: str = Form(...),
    logo_file: UploadFile = File(None)
):
    RESULTS_DIR = "results"
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    with db() as conn:
        c = conn.cursor()

        # Get existing invoice_number
        c.execute("SELECT invoice_number FROM invoices WHERE id=?", (invoice_id,))
        existing = c.fetchone()
        if not existing:
            raise HTTPException(404, "Invoice not found")
        invoice_number = existing[0]

        # Update the invoice record
        c.execute("UPDATE invoices SET client_id=?, template_id=?, data=? WHERE id=?",
                  (client_id, template_id, data, invoice_id))
        conn.commit()

        # Get template info
        c.execute("SELECT template_dir, html_filename, css_filename FROM templates WHERE id=?", (template_id,))
        tpl = c.fetchone()
        if not tpl:
            raise HTTPException(404, "Template not found")
        template_dir_name, html_filename, css_filename = tpl
        template_dir_path = os.path.join(TEMPLATE_DIR, template_dir_name)
        css_path = os.path.join(template_dir_path, css_filename)

        # Get client info
        c.execute("SELECT * FROM clients WHERE id=?", (client_id,))
        client_row = c.fetchone()
        client_dict = dict(zip([col[0] for col in c.description], client_row))
        
        client_dict["zip"] = client_dict["cap"]  
        client_dict["formatted_city"] = f"{client_dict['city']}, {client_dict['cap']}"
        client_dict["country"] = client_dict.get("nation") or "CH"

        # Get bank details
        c.execute("SELECT * FROM bank_details LIMIT 1")
        bank_row = c.fetchone()
        bank_details = dict(zip([col[0] for col in c.description], bank_row))

        # Parse invoice data
        invoice_data = json.loads(data)
        items = invoice_data.get("items", [])

        # Calculate totals
        for item in items:
            item["total"] = float(item["price"]) * float(item["qty"])
            item["price"] = f"{float(item['price']):.2f}"
            item["total"] = f"{item['total']:.2f}"

        subtotal = sum(float(item["total"]) for item in items)
        net_total = subtotal  
        subtotal = f"{subtotal:.2f}"
        net_total = f"{net_total:.2f}"

        # Prepare QR bill data
        debtor = {
            "name": client_dict["name"],
            "street": client_dict["address"],
            "pcode": client_dict["cap"], 
            "city": client_dict["city"],
            "country": client_dict["country"]
        }
        additional_info = invoice_data.get("notes", "")

        invoice_dir = os.path.join(RESULTS_DIR, f"invoice_{invoice_id}")
        os.makedirs(invoice_dir, exist_ok=True)

        # Generate QR bill
        qr_svg_path = None
        qr_svg_rel_path = ""
        try:
            qr_svg_path = generate_qr_bill_svg(net_total, debtor, additional_info, bank_details, invoice_dir)
            qr_svg_rel_path = os.path.basename(qr_svg_path)  
        except Exception as e:
            print(f"QR-bill generation failed for invoice {invoice_id}: {e}")
            qr_svg_rel_path = ""

        # Handle logo
        logo_rel_path = None
        if logo_file:
            original_filename = logo_file.filename
            extension = os.path.splitext(original_filename)[1] if '.' in original_filename else '.png'
            saved_logo_filename = f"uploaded_logo{extension}"
            logo_save_path = os.path.join(invoice_dir, saved_logo_filename)
            with open(logo_save_path, "wb") as buffer:
                shutil.copyfileobj(logo_file.file, buffer)
            logo_rel_path = saved_logo_filename
            await logo_file.close()
        else:
            # Check if existing logo exists and preserve it
            for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
                existing_logo = os.path.join(invoice_dir, f"uploaded_logo{ext}")
                if os.path.exists(existing_logo):
                    logo_rel_path = f"uploaded_logo{ext}"
                    break  

        customer_dict = client_dict.copy()
        
        # Format dates
        invoice_date_raw = invoice_data.get("date") or ""
        invoice_date = to_swiss_date(invoice_date_raw)
        
        invoice_data_copy = invoice_data.copy()
        for k in ["date", "invoice_date"]:
            if k in invoice_data_copy:
                del invoice_data_copy[k]

        # Prepare context
        context = {
            "client": client_dict,
            "customer": customer_dict,
            "qr_image": qr_svg_rel_path,
            "items": items,
            "subtotal": subtotal,
            "net_total": net_total,
            "total": net_total,
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "date": invoice_date,
            "logo": logo_rel_path,
            **invoice_data_copy
        }

        # Copy CSS file
        shutil.copy(css_path, os.path.join(invoice_dir, css_filename))
        
        # Copy assets
        for asset in ["logo.png", "qr.png"]:
            asset_path = os.path.join(template_dir_path, asset)
            copy_asset_if_exists(asset_path, invoice_dir)

        # Render HTML
        env = Environment(loader=FileSystemLoader(template_dir_path))
        template = env.get_template(html_filename)
        html_content_rendered = template.render(**context)
        
        # Replace template tags for images
        if qr_svg_rel_path and os.path.exists(os.path.join(invoice_dir, qr_svg_rel_path)):
            html_content_rendered = re.sub(r'\{\{\s*qr_image\s*\}\}', 
                                          f'<img src="{qr_svg_rel_path}" alt="QR Bill" />', 
                                          html_content_rendered)

        if logo_rel_path and os.path.exists(os.path.join(invoice_dir, logo_rel_path)):
            html_content_rendered = re.sub(r'\{\{\s*logo\s*\}\}',
                                          f'<img src="{logo_rel_path}" alt="Company Logo" style="max-height:100px; width:auto;" />',
                                          html_content_rendered)
        
        # Save rendered HTML
        rendered_html_path = os.path.join(invoice_dir, "rendered.html")
        with open(rendered_html_path, "w", encoding="utf-8") as f:
            f.write(html_content_rendered)

        # Generate PDF
        pdf_path = os.path.join(invoice_dir, "invoice.pdf")
        HTML(filename=rendered_html_path, base_url=f"file://{os.path.abspath(invoice_dir)}/").write_pdf(pdf_path)

        return {
            "id": invoice_id,
            "html": rendered_html_path,
            "pdf": pdf_path
        }

@app.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: int):
    with db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM invoices WHERE id=?", (invoice_id,))
        conn.commit()
        return {"ok": True}

@app.get("/invoices/{invoice_id}/pdf")
def get_invoice_pdf(invoice_id: int):
    pdf_path = os.path.join("results", f"invoice_{invoice_id}", "invoice.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(404, "PDF not found")
    return FileResponse(pdf_path, media_type="application/pdf")

