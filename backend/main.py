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
        c.execute('''CREATE TABLE IF NOT EXISTS recurring_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            amount REAL,
            currency TEXT DEFAULT 'CHF',
            frequency TEXT,
            start_date TEXT,
            description TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS payment_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            recurring_fee_id INTEGER,
            amount REAL,
            currency TEXT DEFAULT 'CHF',
            due_date TEXT,
            description TEXT,
            status TEXT DEFAULT 'not_sent',
            invoice_id INTEGER,
            paid_date TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (recurring_fee_id) REFERENCES recurring_fees(id),
            FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            default_share REAL DEFAULT 50.0,
            telegram_chat_id TEXT,
            color TEXT DEFAULT '#4a90e2'
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'CHF',
            category TEXT NOT NULL,
            expense_type TEXT NOT NULL,
            paid_by INTEGER NOT NULL,
            split_ratio_a REAL DEFAULT 50.0,
            split_ratio_b REAL DEFAULT 50.0,
            receipt_path TEXT,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (paid_by) REFERENCES partners(id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS settlements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_partner_id INTEGER NOT NULL,
            to_partner_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'CHF',
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_partner_id) REFERENCES partners(id),
            FOREIGN KEY (to_partner_id) REFERENCES partners(id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS telegram_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            bot_token TEXT,
            enabled INTEGER DEFAULT 0,
            notify_renewals_7d INTEGER DEFAULT 1,
            notify_renewals_14d INTEGER DEFAULT 1,
            notify_renewals_30d INTEGER DEFAULT 0,
            notify_overdue INTEGER DEFAULT 1
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS notifications_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            reference_id INTEGER,
            sent_at TEXT NOT NULL,
            chat_id TEXT NOT NULL
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            client_id INTEGER,
            invoice_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            start_datetime TEXT NOT NULL,
            end_datetime TEXT,
            all_day INTEGER DEFAULT 0,
            event_type TEXT DEFAULT 'appointment',
            client_id INTEGER,
            color TEXT DEFAULT '#4a90e2',
            reminder_minutes INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )''')

        c.execute("SELECT COUNT(*) FROM bank_details")
        if c.fetchone()[0] == 0:
            c.execute('''INSERT INTO bank_details
                (iban, bank_name, bank_address, bic, creditor_name, creditor_street, creditor_postalcode, creditor_city, creditor_country)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                ("CH5800791123000889012", "My Bank", "Bankstrasse 1", "POFICHBEXXX",
                 "My Company AG", "My Street 1", "8000", "Zurich", "CH"))

        c.execute("SELECT COUNT(*) FROM partners")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO partners (name, default_share, color) VALUES (?, ?, ?)", ("Partner A", 50.0, "#4a90e2"))
            c.execute("INSERT INTO partners (name, default_share, color) VALUES (?, ?, ?)", ("Partner B", 50.0, "#10b981"))

        c.execute("SELECT COUNT(*) FROM telegram_config")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO telegram_config (id, enabled) VALUES (1, 0)")

        c.execute("PRAGMA table_info(invoices)")
        columns = [col[1] for col in c.fetchall()]
        if "invoice_number" not in columns:
            c.execute("ALTER TABLE invoices ADD COLUMN invoice_number TEXT")
            c.execute("SELECT id FROM invoices WHERE invoice_number IS NULL")
            for row in c.fetchall():
                invoice_id = row[0]
                while True:
                    new_invoice_number = generate_invoice_number()
                    c.execute("SELECT COUNT(*) FROM invoices WHERE invoice_number=?", (new_invoice_number,))
                    if c.fetchone()[0] == 0:
                        break
                c.execute("UPDATE invoices SET invoice_number=? WHERE id=?", (new_invoice_number, invoice_id))

        if "partner_a_share" not in columns:
            c.execute("ALTER TABLE invoices ADD COLUMN partner_a_share REAL DEFAULT 50.0")
        if "partner_b_share" not in columns:
            c.execute("ALTER TABLE invoices ADD COLUMN partner_b_share REAL DEFAULT 50.0")
        if "status" not in columns:
            c.execute("ALTER TABLE invoices ADD COLUMN status TEXT DEFAULT 'draft'")
        if "sent_date" not in columns:
            c.execute("ALTER TABLE invoices ADD COLUMN sent_date TEXT")
        if "paid_date" not in columns:
            c.execute("ALTER TABLE invoices ADD COLUMN paid_date TEXT")
        if "total_amount" not in columns:
            c.execute("ALTER TABLE invoices ADD COLUMN total_amount REAL")
        if "title" not in columns:
            c.execute("ALTER TABLE invoices ADD COLUMN title TEXT")
        if "description" not in columns:
            c.execute("ALTER TABLE invoices ADD COLUMN description TEXT")

        c.execute("PRAGMA table_info(recurring_fees)")
        rf_columns = [col[1] for col in c.fetchall()]
        if "service_type" not in rf_columns:
            c.execute("ALTER TABLE recurring_fees ADD COLUMN service_type TEXT DEFAULT 'other'")

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

@app.get("/clients/{client_id}/stats")
def get_client_stats(client_id: int):
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM invoices WHERE client_id=?", (client_id,))
        invoices = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]

        total_invoiced = sum(i.get("total_amount", 0) or 0 for i in invoices)
        paid_invoices = [i for i in invoices if i.get("status") == "paid"]
        total_paid = sum(i.get("total_amount", 0) or 0 for i in paid_invoices)
        outstanding_invoices = [i for i in invoices if i.get("status") in ("draft", "sent")]
        total_outstanding = sum(i.get("total_amount", 0) or 0 for i in outstanding_invoices)

        c.execute("SELECT * FROM recurring_fees WHERE client_id=?", (client_id,))
        recurring_fees = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
        annual_recurring = sum(
            (f.get("amount", 0) or 0) * (12 if f.get("frequency") == "monthly" else 1)
            for f in recurring_fees if f.get("frequency") != "one-time"
        )

        return {
            "total_invoices": len(invoices),
            "total_invoiced": total_invoiced,
            "paid_invoices": len(paid_invoices),
            "total_paid": total_paid,
            "outstanding_invoices": len(outstanding_invoices),
            "total_outstanding": total_outstanding,
            "recurring_fees": len(recurring_fees),
            "annual_recurring": annual_recurring
        }

@app.get("/clients/{client_id}/recurring-fees")
def get_recurring_fees(client_id: int):
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM recurring_fees WHERE client_id=?", (client_id,))
        rows = c.fetchall()
        return [dict(zip([col[0] for col in c.description], row)) for row in rows]

@app.post("/clients/{client_id}/recurring-fees")
def add_recurring_fee(client_id: int, fee: dict):
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    with db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO recurring_fees (client_id, amount, currency, frequency, start_date, description) VALUES (?, ?, ?, ?, ?, ?)",
            (client_id, fee["amount"], fee.get("currency", "CHF"), fee["frequency"], fee["start_date"], fee.get("description", ""))
        )
        conn.commit()
        recurring_fee_id = c.lastrowid

        # Auto-generate payment events from start date to next future occurrence
        start_date_str = fee["start_date"]
        try:
            if "." in start_date_str:
                parts = start_date_str.split(".")
                start_date = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            elif "/" in start_date_str:
                parts = start_date_str.split("/")
                start_date = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            else:
                start_date = datetime.fromisoformat(start_date_str[:10])
        except:
            return {"id": recurring_fee_id}

        current_date = datetime.now()
        next_date = start_date

        # Generate all events from start_date until the next future occurrence
        if fee["frequency"] == "monthly":
            while next_date <= current_date:
                # Create event for this date
                due_date_str = next_date.strftime("%Y-%m-%d")
                c.execute("SELECT COUNT(*) FROM payment_events WHERE recurring_fee_id=? AND due_date=?",
                         (recurring_fee_id, due_date_str))
                if c.fetchone()[0] == 0:
                    c.execute(
                        "INSERT INTO payment_events (client_id, recurring_fee_id, amount, currency, due_date, description, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (client_id, recurring_fee_id, fee["amount"], fee.get("currency", "CHF"),
                         due_date_str, fee.get("description", ""), "not_sent")
                    )
                next_date = next_date + relativedelta(months=1)
            # Add one more future occurrence
            due_date_str = next_date.strftime("%Y-%m-%d")
            c.execute(
                "INSERT INTO payment_events (client_id, recurring_fee_id, amount, currency, due_date, description, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (client_id, recurring_fee_id, fee["amount"], fee.get("currency", "CHF"),
                 due_date_str, fee.get("description", ""), "not_sent")
            )
        elif fee["frequency"] == "yearly":
            while next_date <= current_date:
                due_date_str = next_date.strftime("%Y-%m-%d")
                c.execute("SELECT COUNT(*) FROM payment_events WHERE recurring_fee_id=? AND due_date=?",
                         (recurring_fee_id, due_date_str))
                if c.fetchone()[0] == 0:
                    c.execute(
                        "INSERT INTO payment_events (client_id, recurring_fee_id, amount, currency, due_date, description, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (client_id, recurring_fee_id, fee["amount"], fee.get("currency", "CHF"),
                         due_date_str, fee.get("description", ""), "not_sent")
                    )
                next_date = next_date + relativedelta(years=1)
            # Add one more future occurrence
            due_date_str = next_date.strftime("%Y-%m-%d")
            c.execute(
                "INSERT INTO payment_events (client_id, recurring_fee_id, amount, currency, due_date, description, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (client_id, recurring_fee_id, fee["amount"], fee.get("currency", "CHF"),
                 due_date_str, fee.get("description", ""), "not_sent")
            )
        elif fee["frequency"] == "one-time":
            due_date_str = start_date.strftime("%Y-%m-%d")
            c.execute(
                "INSERT INTO payment_events (client_id, recurring_fee_id, amount, currency, due_date, description, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (client_id, recurring_fee_id, fee["amount"], fee.get("currency", "CHF"),
                 due_date_str, fee.get("description", ""), "not_sent")
            )

        conn.commit()
        return {"id": recurring_fee_id}

@app.put("/recurring-fees/{fee_id}")
def update_recurring_fee(fee_id: int, fee: dict):
    with db() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE recurring_fees SET amount=?, currency=?, frequency=?, start_date=?, description=? WHERE id=?",
            (fee["amount"], fee.get("currency", "CHF"), fee["frequency"], fee["start_date"], fee.get("description", ""), fee_id)
        )
        conn.commit()
        return {"ok": True}

@app.delete("/recurring-fees/{fee_id}")
def delete_recurring_fee(fee_id: int):
    with db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM recurring_fees WHERE id=?", (fee_id,))
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

@app.get("/payment-events")
def get_payment_events(client_id: int = None, status: str = None):
    with db() as conn:
        c = conn.cursor()
        query = "SELECT * FROM payment_events"
        params = []
        conditions = []

        if client_id is not None:
            conditions.append("client_id=?")
            params.append(client_id)

        if status is not None:
            conditions.append("status=?")
            params.append(status)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY due_date ASC"

        c.execute(query, params)
        rows = c.fetchall()
        events = [dict(zip([col[0] for col in c.description], row)) for row in rows]

        # Add client name to each event
        for event in events:
            c.execute("SELECT name FROM clients WHERE id=?", (event["client_id"],))
            client = c.fetchone()
            event["client_name"] = client[0] if client else "Unknown"

        return events

@app.post("/payment-events")
def create_payment_event(event: dict):
    with db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO payment_events (client_id, recurring_fee_id, amount, currency, due_date, description, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (event["client_id"], event.get("recurring_fee_id"), event["amount"], event.get("currency", "CHF"),
             event["due_date"], event.get("description", ""), event.get("status", "not_sent"))
        )
        conn.commit()
        return {"id": c.lastrowid}

@app.post("/payment-events/generate")
def generate_payment_events(params: dict = Body(...)):
    """Generate payment events from recurring fees"""
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta

    client_id = params.get("client_id")
    recurring_fee_id = params.get("recurring_fee_id")

    with db() as conn:
        c = conn.cursor()

        # Get recurring fees to process
        if recurring_fee_id:
            c.execute("SELECT * FROM recurring_fees WHERE id=?", (recurring_fee_id,))
        elif client_id:
            c.execute("SELECT * FROM recurring_fees WHERE client_id=?", (client_id,))
        else:
            c.execute("SELECT * FROM recurring_fees")

        fees = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]

        generated_count = 0
        for fee in fees:
            # Parse start date (DD.MM.YYYY, DD/MM/YYYY or YYYY-MM-DD)
            start_date_str = fee["start_date"]
            try:
                if "." in start_date_str:
                    parts = start_date_str.split(".")
                    start_date = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
                elif "/" in start_date_str:
                    parts = start_date_str.split("/")
                    start_date = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
                else:
                    start_date = datetime.fromisoformat(start_date_str[:10])
            except:
                continue

            # Calculate next occurrences
            current_date = datetime.now()
            next_date = start_date

            # Find the next occurrence after today
            if fee["frequency"] == "monthly":
                while next_date < current_date:
                    next_date = next_date + relativedelta(months=1)
            elif fee["frequency"] == "yearly":
                while next_date < current_date:
                    next_date = next_date + relativedelta(years=1)
            elif fee["frequency"] == "one-time":
                next_date = start_date

            # Check if event already exists for this date
            due_date_str = next_date.strftime("%Y-%m-%d")
            c.execute("SELECT COUNT(*) FROM payment_events WHERE recurring_fee_id=? AND due_date=?",
                     (fee["id"], due_date_str))

            if c.fetchone()[0] == 0:
                # Create the event
                c.execute(
                    "INSERT INTO payment_events (client_id, recurring_fee_id, amount, currency, due_date, description, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (fee["client_id"], fee["id"], fee["amount"], fee["currency"],
                     due_date_str, fee["description"], "pending")
                )
                generated_count += 1

        conn.commit()
        return {"generated": generated_count}

@app.put("/payment-events/{event_id}")
def update_payment_event(event_id: int, event: dict):
    from datetime import datetime

    with db() as conn:
        c = conn.cursor()

        # Build update query based on provided fields
        updates = []
        params = []

        if "amount" in event:
            updates.append("amount=?")
            params.append(event["amount"])

        if "currency" in event:
            updates.append("currency=?")
            params.append(event["currency"])

        if "due_date" in event:
            updates.append("due_date=?")
            params.append(event["due_date"])

        if "description" in event:
            updates.append("description=?")
            params.append(event["description"])

        if "status" in event:
            updates.append("status=?")
            params.append(event["status"])

            # If marking as paid, record the date
            if event["status"] == "paid" and "paid_date" not in event:
                updates.append("paid_date=?")
                params.append(datetime.now().strftime("%Y-%m-%d"))
            elif event["status"] != "paid":
                updates.append("paid_date=?")
                params.append(None)

        if "paid_date" in event:
            updates.append("paid_date=?")
            params.append(event["paid_date"])

        if "invoice_id" in event:
            updates.append("invoice_id=?")
            params.append(event["invoice_id"])

        if not updates:
            return {"ok": True}

        params.append(event_id)
        query = f"UPDATE payment_events SET {', '.join(updates)} WHERE id=?"

        c.execute(query, params)
        conn.commit()
        return {"ok": True}

@app.delete("/payment-events/{event_id}")
def delete_payment_event(event_id: int):
    with db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM payment_events WHERE id=?", (event_id,))
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

@app.get("/templates/{template_id}/content")
def get_template_content(template_id: int):
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT template_dir, html_filename, css_filename FROM templates WHERE id=?", (template_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(404, "Template not found")
        template_dir, html_filename, css_filename = row
        template_path = os.path.join(TEMPLATE_DIR, template_dir)

        html_content = ""
        css_content = ""

        html_path = os.path.join(template_path, html_filename)
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()

        css_path = os.path.join(template_path, css_filename)
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()

        return {"html": html_content, "css": css_content}

@app.put("/templates/{template_id}/content")
def update_template_content(template_id: int, content: dict):
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT template_dir, html_filename, css_filename FROM templates WHERE id=?", (template_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(404, "Template not found")
        template_dir, html_filename, css_filename = row
        template_path = os.path.join(TEMPLATE_DIR, template_dir)

        if "html" in content:
            html_path = os.path.join(template_path, html_filename)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(content["html"])
            fields = extract_jinja_fields(content["html"])
            c.execute("UPDATE templates SET fields=? WHERE id=?", (json.dumps(fields), template_id))

        if "css" in content:
            css_path = os.path.join(template_path, css_filename)
            with open(css_path, "w", encoding="utf-8") as f:
                f.write(content["css"])

        conn.commit()
        return {"ok": True}

@app.post("/templates/{template_id}/preview")
def preview_template(template_id: int, preview_data: dict = None):
    from jinja2 import Environment, FileSystemLoader, UndefinedError

    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT template_dir, html_filename, css_filename FROM templates WHERE id=?", (template_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(404, "Template not found")
        template_dir, html_filename, css_filename = row
        template_path = os.path.join(TEMPLATE_DIR, template_dir)

        css_path = os.path.join(template_path, css_filename)
        css_content = ""
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()

        sample_data = preview_data or {
            "invoice_number": "INV-2024-001",
            "invoice_date": "19.12.2024",
            "date": "19.12.2024",
            "logo": "",
            "logo_box_width": 120,
            "logo_box_height": 60,
            "customer": {
                "name": "Sample Client AG",
                "address": "Musterstrasse 123",
                "city": "Zurich",
                "zip": "8000",
                "country": "Switzerland"
            },
            "client": {
                "name": "Sample Client AG",
                "address": "Musterstrasse 123",
                "cap": "8000",
                "city": "Zurich",
                "nation": "CH",
                "email": "client@example.com"
            },
            "items": [
                {"desc": "Web Development", "price": "1'500.00", "qty": 1, "total": "1'500.00"},
                {"desc": "Hosting (annual)", "price": "300.00", "qty": 1, "total": "300.00"}
            ],
            "subtotal": "1'800.00",
            "total": "1'800.00",
            "notes": "Payment due within 30 days.",
            "thank_you_message": "Thank you for your business!",
            "qr_image": ""
        }

        try:
            env = Environment(loader=FileSystemLoader(template_path))
            template = env.get_template(html_filename)
            rendered_html = template.render(**sample_data)

            full_html = f"""<!DOCTYPE html>
<html>
<head>
<style>{css_content}</style>
</head>
<body>{rendered_html}</body>
</html>"""

            return {"html": full_html}
        except UndefinedError as e:
            return {"html": f"<p style='color:red;padding:20px;'>Template error: Missing variable - {str(e)}</p>"}
        except Exception as e:
            return {"html": f"<p style='color:red;padding:20px;'>Preview error: {str(e)}</p>"}

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
def get_invoices(client_id: int = None):
    with db() as conn:
        c = conn.cursor()
        if client_id:
            c.execute("SELECT * FROM invoices WHERE client_id=?", (client_id,))
        else:
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
    logo_file: UploadFile = File(None),
    partner_a_share: float = Form(50.0),
    partner_b_share: float = Form(50.0),
    title: str = Form(""),
    description: str = Form("")
):
    RESULTS_DIR = "results"
    os.makedirs(RESULTS_DIR, exist_ok=True)

    with db() as conn:
        c = conn.cursor()
        while True:
            invoice_number = generate_invoice_number()
            c.execute("SELECT COUNT(*) FROM invoices WHERE invoice_number=?", (invoice_number,))
            if c.fetchone()[0] == 0:
                break

        invoice_data = json.loads(data)
        items = invoice_data.get("items", [])
        total_amount = sum(float(item.get("price", 0)) * float(item.get("qty", 1)) for item in items)

        c.execute("""INSERT INTO invoices (invoice_number, client_id, template_id, data, partner_a_share, partner_b_share, status, total_amount, title, description)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (invoice_number, client_id, template_id, data, partner_a_share, partner_b_share, "draft", total_amount, title, description))
        conn.commit()
        invoice_id = c.lastrowid

        from datetime import datetime
        c.execute(
            "SELECT id FROM payment_events WHERE client_id=? AND status IN ('not_sent', 'sent') ORDER BY due_date ASC LIMIT 1",
            (client_id,)
        )
        event_row = c.fetchone()
        if event_row:
            payment_event_id = event_row[0]
            c.execute("UPDATE payment_events SET invoice_id=?, status=? WHERE id=?",
                     (invoice_id, "sent", payment_event_id))
            conn.commit()

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
    logo_file: UploadFile = File(None),
    partner_a_share: float = Form(50.0),
    partner_b_share: float = Form(50.0),
    title: str = Form(""),
    description: str = Form("")
):
    RESULTS_DIR = "results"
    os.makedirs(RESULTS_DIR, exist_ok=True)

    with db() as conn:
        c = conn.cursor()

        c.execute("SELECT invoice_number FROM invoices WHERE id=?", (invoice_id,))
        existing = c.fetchone()
        if not existing:
            raise HTTPException(404, "Invoice not found")
        invoice_number = existing[0]

        invoice_data_parsed = json.loads(data)
        items = invoice_data_parsed.get("items", [])
        total_amount = sum(float(item.get("price", 0)) * float(item.get("qty", 1)) for item in items)

        c.execute("""UPDATE invoices SET client_id=?, template_id=?, data=?, partner_a_share=?, partner_b_share=?, total_amount=?, title=?, description=? WHERE id=?""",
                  (client_id, template_id, data, partner_a_share, partner_b_share, total_amount, title, description, invoice_id))
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

@app.put("/invoices/{invoice_id}/status")
def update_invoice_status(invoice_id: int, data: dict = Body(...)):
    from datetime import datetime
    with db() as conn:
        c = conn.cursor()
        status = data.get("status")
        if status not in ["draft", "sent", "paid"]:
            raise HTTPException(400, "Invalid status")

        updates = ["status=?"]
        params = [status]

        if status == "sent":
            updates.append("sent_date=?")
            params.append(data.get("sent_date") or datetime.now().strftime("%Y-%m-%d"))
        elif status == "paid":
            updates.append("paid_date=?")
            params.append(data.get("paid_date") or datetime.now().strftime("%Y-%m-%d"))

        params.append(invoice_id)
        c.execute(f"UPDATE invoices SET {', '.join(updates)} WHERE id=?", params)
        conn.commit()
        return {"ok": True}

@app.get("/partners")
def get_partners():
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM partners")
        rows = c.fetchall()
        return [dict(zip([col[0] for col in c.description], row)) for row in rows]

@app.put("/partners/{partner_id}")
def update_partner(partner_id: int, partner: dict = Body(...)):
    with db() as conn:
        c = conn.cursor()
        updates = []
        params = []
        if "name" in partner:
            updates.append("name=?")
            params.append(partner["name"])
        if "default_share" in partner:
            updates.append("default_share=?")
            params.append(partner["default_share"])
        if "telegram_chat_id" in partner:
            updates.append("telegram_chat_id=?")
            params.append(partner["telegram_chat_id"])
        if "color" in partner:
            updates.append("color=?")
            params.append(partner["color"])
        if not updates:
            return {"ok": True}
        params.append(partner_id)
        c.execute(f"UPDATE partners SET {', '.join(updates)} WHERE id=?", params)
        conn.commit()
        return {"ok": True}

@app.get("/expenses")
def get_expenses(category: str = None, expense_type: str = None, status: str = None, date_from: str = None, date_to: str = None):
    with db() as conn:
        c = conn.cursor()
        query = "SELECT * FROM expenses"
        conditions = []
        params = []
        if category:
            conditions.append("category=?")
            params.append(category)
        if expense_type:
            conditions.append("expense_type=?")
            params.append(expense_type)
        if status:
            conditions.append("status=?")
            params.append(status)
        if date_from:
            conditions.append("date>=?")
            params.append(date_from)
        if date_to:
            conditions.append("date<=?")
            params.append(date_to)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY date DESC"
        c.execute(query, params)
        rows = c.fetchall()
        expenses = [dict(zip([col[0] for col in c.description], row)) for row in rows]
        for exp in expenses:
            c.execute("SELECT name FROM partners WHERE id=?", (exp["paid_by"],))
            partner = c.fetchone()
            exp["paid_by_name"] = partner[0] if partner else "Unknown"
        return expenses

@app.post("/expenses")
def create_expense(expense: dict = Body(...)):
    with db() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO expenses (date, description, amount, currency, category, expense_type, paid_by, split_ratio_a, split_ratio_b, receipt_path, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (expense["date"], expense["description"], expense["amount"], expense.get("currency", "CHF"),
             expense["category"], expense["expense_type"], expense["paid_by"],
             expense.get("split_ratio_a", 50.0), expense.get("split_ratio_b", 50.0),
             expense.get("receipt_path"), expense.get("notes"))
        )
        conn.commit()
        return {"id": c.lastrowid}

@app.put("/expenses/{expense_id}")
def update_expense(expense_id: int, expense: dict = Body(...)):
    with db() as conn:
        c = conn.cursor()
        updates = []
        params = []
        for field in ["date", "description", "amount", "currency", "category", "expense_type", "paid_by", "split_ratio_a", "split_ratio_b", "receipt_path", "status", "notes"]:
            if field in expense:
                updates.append(f"{field}=?")
                params.append(expense[field])
        if not updates:
            return {"ok": True}
        params.append(expense_id)
        c.execute(f"UPDATE expenses SET {', '.join(updates)} WHERE id=?", params)
        conn.commit()
        return {"ok": True}

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):
    with db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        conn.commit()
        return {"ok": True}

@app.get("/expenses/balance")
def get_expense_balance():
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM partners ORDER BY id")
        partners = [row[0] for row in c.fetchall()]
        if len(partners) < 2:
            return {"balance": 0, "owes_to": None, "owes_from": None}
        partner_a, partner_b = partners[0], partners[1]

        c.execute("SELECT * FROM expenses WHERE status='pending'")
        expenses = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]

        a_owes_b = 0.0
        b_owes_a = 0.0

        for exp in expenses:
            amount = exp["amount"]
            split_a = exp["split_ratio_a"] / 100.0
            split_b = exp["split_ratio_b"] / 100.0
            paid_by = exp["paid_by"]

            a_share = amount * split_a
            b_share = amount * split_b

            if paid_by == partner_a:
                b_owes_a += b_share
            else:
                a_owes_b += a_share

        net_balance = b_owes_a - a_owes_b

        c.execute("SELECT name FROM partners WHERE id=?", (partner_a,))
        name_a = c.fetchone()[0]
        c.execute("SELECT name FROM partners WHERE id=?", (partner_b,))
        name_b = c.fetchone()[0]

        if net_balance > 0:
            return {"balance": abs(net_balance), "owes_from": name_b, "owes_to": name_a, "owes_from_id": partner_b, "owes_to_id": partner_a}
        elif net_balance < 0:
            return {"balance": abs(net_balance), "owes_from": name_a, "owes_to": name_b, "owes_from_id": partner_a, "owes_to_id": partner_b}
        else:
            return {"balance": 0, "owes_from": None, "owes_to": None}

@app.get("/settlements")
def get_settlements():
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM settlements ORDER BY date DESC")
        rows = c.fetchall()
        settlements = [dict(zip([col[0] for col in c.description], row)) for row in rows]
        for s in settlements:
            c.execute("SELECT name FROM partners WHERE id=?", (s["from_partner_id"],))
            s["from_partner_name"] = c.fetchone()[0]
            c.execute("SELECT name FROM partners WHERE id=?", (s["to_partner_id"],))
            s["to_partner_name"] = c.fetchone()[0]
        return settlements

@app.post("/settlements")
def create_settlement(settlement: dict = Body(...)):
    from datetime import datetime
    with db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO settlements (from_partner_id, to_partner_id, amount, currency, date, description) VALUES (?, ?, ?, ?, ?, ?)",
            (settlement["from_partner_id"], settlement["to_partner_id"], settlement["amount"],
             settlement.get("currency", "CHF"), settlement.get("date") or datetime.now().strftime("%Y-%m-%d"),
             settlement.get("description", ""))
        )
        if settlement.get("settle_pending", True):
            c.execute("UPDATE expenses SET status='settled' WHERE status='pending'")
        conn.commit()
        return {"id": c.lastrowid}

@app.get("/dashboard/stats")
def get_dashboard_stats(period: str = "all"):
    from datetime import datetime, timedelta
    with db() as conn:
        c = conn.cursor()

        date_filter = ""
        if period == "month":
            start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            date_filter = f" AND i.paid_date >= '{start}'"
        elif period == "year":
            start = datetime.now().replace(month=1, day=1).strftime("%Y-%m-%d")
            date_filter = f" AND i.paid_date >= '{start}'"

        c.execute(f"""
            SELECT COALESCE(SUM(total_amount), 0) as total_revenue,
                   COALESCE(SUM(total_amount * partner_a_share / 100.0), 0) as partner_a_revenue,
                   COALESCE(SUM(total_amount * partner_b_share / 100.0), 0) as partner_b_revenue
            FROM invoices i WHERE status = 'paid' {date_filter}
        """)
        revenue = c.fetchone()

        c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE status IN ('draft', 'sent')")
        outstanding = c.fetchone()[0]

        expense_date_filter = ""
        if period == "month":
            expense_date_filter = f" AND date >= '{start}'"
        elif period == "year":
            expense_date_filter = f" AND date >= '{start}'"

        c.execute(f"SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE 1=1 {expense_date_filter}")
        total_expenses = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM invoices WHERE status='draft'")
        draft_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM invoices WHERE status='sent'")
        sent_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM invoices WHERE status='paid'")
        paid_count = c.fetchone()[0]

        return {
            "total_revenue": revenue[0] or 0,
            "partner_a_revenue": revenue[1] or 0,
            "partner_b_revenue": revenue[2] or 0,
            "outstanding": outstanding or 0,
            "total_expenses": total_expenses or 0,
            "net_profit": (revenue[0] or 0) - (total_expenses or 0),
            "invoice_counts": {"draft": draft_count, "sent": sent_count, "paid": paid_count}
        }

@app.get("/dashboard/renewals")
def get_dashboard_renewals(days: int = 30):
    from datetime import datetime, timedelta
    with db() as conn:
        c = conn.cursor()
        today = datetime.now().date()
        end_date = today + timedelta(days=days)

        c.execute("""
            SELECT pe.*, c.name as client_name, rf.service_type
            FROM payment_events pe
            LEFT JOIN clients c ON pe.client_id = c.id
            LEFT JOIN recurring_fees rf ON pe.recurring_fee_id = rf.id
            WHERE pe.status != 'paid'
            AND pe.due_date >= ? AND pe.due_date <= ?
            ORDER BY pe.due_date ASC
        """, (today.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        rows = c.fetchall()
        renewals = [dict(zip([col[0] for col in c.description], row)) for row in rows]

        for r in renewals:
            due = datetime.strptime(r["due_date"], "%Y-%m-%d").date()
            r["days_until"] = (due - today).days
            if r["days_until"] <= 7:
                r["urgency"] = "critical"
            elif r["days_until"] <= 14:
                r["urgency"] = "warning"
            else:
                r["urgency"] = "normal"
        return renewals

@app.get("/dashboard/outstanding")
def get_dashboard_outstanding():
    with db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT i.*, c.name as client_name
            FROM invoices i
            LEFT JOIN clients c ON i.client_id = c.id
            WHERE i.status IN ('draft', 'sent')
            ORDER BY i.status DESC, i.id DESC
        """)
        rows = c.fetchall()
        return [dict(zip([col[0] for col in c.description], row)) for row in rows]

@app.get("/dashboard/partner-earnings")
def get_partner_earnings(period: str = "all"):
    from datetime import datetime
    with db() as conn:
        c = conn.cursor()

        date_filter = ""
        if period == "month":
            start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            date_filter = f" AND paid_date >= '{start}'"
        elif period == "year":
            start = datetime.now().replace(month=1, day=1).strftime("%Y-%m-%d")
            date_filter = f" AND paid_date >= '{start}'"

        c.execute(f"""
            SELECT
                COALESCE(SUM(total_amount * partner_a_share / 100.0), 0) as partner_a,
                COALESCE(SUM(total_amount * partner_b_share / 100.0), 0) as partner_b
            FROM invoices WHERE status = 'paid' {date_filter}
        """)
        earnings = c.fetchone()

        c.execute("SELECT id, name, color FROM partners ORDER BY id")
        partners = [dict(zip(["id", "name", "color"], row)) for row in c.fetchall()]

        if len(partners) >= 2:
            partners[0]["earnings"] = earnings[0] or 0
            partners[1]["earnings"] = earnings[1] or 0

        return {"partners": partners, "period": period}

@app.get("/telegram/config")
def get_telegram_config():
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM telegram_config WHERE id=1")
        row = c.fetchone()
        if row:
            return dict(zip([col[0] for col in c.description], row))
        return {}

@app.put("/telegram/config")
def update_telegram_config(config: dict = Body(...)):
    with db() as conn:
        c = conn.cursor()
        updates = []
        params = []
        for field in ["bot_token", "enabled", "notify_renewals_7d", "notify_renewals_14d", "notify_renewals_30d", "notify_overdue"]:
            if field in config:
                updates.append(f"{field}=?")
                params.append(config[field])
        if not updates:
            return {"ok": True}
        c.execute(f"UPDATE telegram_config SET {', '.join(updates)} WHERE id=1", params)
        conn.commit()
        return {"ok": True}

@app.post("/telegram/test")
async def test_telegram():
    import httpx
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT bot_token FROM telegram_config WHERE id=1")
        row = c.fetchone()
        if not row or not row[0]:
            raise HTTPException(400, "Telegram bot token not configured")
        bot_token = row[0]

        c.execute("SELECT telegram_chat_id FROM partners WHERE telegram_chat_id IS NOT NULL")
        chat_ids = [r[0] for r in c.fetchall() if r[0]]
        if not chat_ids:
            raise HTTPException(400, "No Telegram chat IDs configured for partners")

        async with httpx.AsyncClient() as client:
            for chat_id in chat_ids:
                await client.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={"chat_id": chat_id, "text": "Test notification from Invoice Manager", "parse_mode": "HTML"}
                )
        return {"ok": True, "sent_to": len(chat_ids)}

@app.post("/telegram/check")
async def check_and_send_notifications():
    import httpx
    from datetime import datetime, timedelta

    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM telegram_config WHERE id=1")
        config_row = c.fetchone()
        if not config_row:
            return {"sent": 0}
        config = dict(zip([col[0] for col in c.description], config_row))

        if not config.get("enabled") or not config.get("bot_token"):
            return {"sent": 0}

        bot_token = config["bot_token"]
        c.execute("SELECT telegram_chat_id FROM partners WHERE telegram_chat_id IS NOT NULL")
        chat_ids = [r[0] for r in c.fetchall() if r[0]]
        if not chat_ids:
            return {"sent": 0}

        today = datetime.now().date()
        sent_count = 0

        async def send_message(chat_id, text, ref_type, ref_id):
            nonlocal sent_count
            c.execute("SELECT COUNT(*) FROM notifications_log WHERE type=? AND reference_id=? AND DATE(sent_at)=?",
                     (ref_type, ref_id, today.strftime("%Y-%m-%d")))
            if c.fetchone()[0] > 0:
                return
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
                )
            c.execute("INSERT INTO notifications_log (type, reference_id, sent_at, chat_id) VALUES (?, ?, ?, ?)",
                     (ref_type, ref_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), chat_id))
            sent_count += 1

        for days, config_key in [(7, "notify_renewals_7d"), (14, "notify_renewals_14d"), (30, "notify_renewals_30d")]:
            if config.get(config_key):
                target_date = today + timedelta(days=days)
                c.execute("""
                    SELECT pe.id, pe.description, pe.amount, pe.currency, pe.due_date, c.name as client_name
                    FROM payment_events pe
                    LEFT JOIN clients c ON pe.client_id = c.id
                    WHERE pe.status != 'paid' AND pe.due_date = ?
                """, (target_date.strftime("%Y-%m-%d"),))
                for row in c.fetchall():
                    pe = dict(zip(["id", "description", "amount", "currency", "due_date", "client_name"], row))
                    msg = f"Renewal in {days} days:\n{pe['client_name']} - {pe['description']}\n{pe['amount']} {pe['currency']} (due: {pe['due_date']})"
                    for chat_id in chat_ids:
                        await send_message(chat_id, msg, f"renewal_{days}d", pe["id"])

        if config.get("notify_overdue"):
            c.execute("""
                SELECT pe.id, pe.description, pe.amount, pe.currency, pe.due_date, c.name as client_name
                FROM payment_events pe
                LEFT JOIN clients c ON pe.client_id = c.id
                WHERE pe.status != 'paid' AND pe.due_date < ?
            """, (today.strftime("%Y-%m-%d"),))
            for row in c.fetchall():
                pe = dict(zip(["id", "description", "amount", "currency", "due_date", "client_name"], row))
                msg = f"OVERDUE: {pe['client_name']} - {pe['description']}\n{pe['amount']} {pe['currency']} (was due: {pe['due_date']})"
                for chat_id in chat_ids:
                    await send_message(chat_id, msg, "overdue", pe["id"])

        conn.commit()
        return {"sent": sent_count}

@app.post("/recurring-fees/{fee_id}/generate-invoice")
def generate_invoice_from_recurring(fee_id: int):
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM recurring_fees WHERE id=?", (fee_id,))
        fee_row = c.fetchone()
        if not fee_row:
            raise HTTPException(404, "Recurring fee not found")
        fee = dict(zip([col[0] for col in c.description], fee_row))

        c.execute("SELECT id FROM templates LIMIT 1")
        template_row = c.fetchone()
        if not template_row:
            raise HTTPException(400, "No templates available")
        template_id = template_row[0]

        c.execute("SELECT id FROM partners ORDER BY id LIMIT 2")
        partners = c.fetchall()
        partner_a_share = 50.0
        partner_b_share = 50.0
        if len(partners) >= 2:
            c.execute("SELECT default_share FROM partners WHERE id=?", (partners[0][0],))
            partner_a_share = c.fetchone()[0]
            partner_b_share = 100.0 - partner_a_share

        from datetime import datetime
        invoice_data = json.dumps({
            "items": [{"desc": fee["description"] or "Service", "price": fee["amount"], "qty": 1}],
            "date": datetime.now().strftime("%d.%m.%Y"),
            "notes": ""
        })

        while True:
            invoice_number = generate_invoice_number()
            c.execute("SELECT COUNT(*) FROM invoices WHERE invoice_number=?", (invoice_number,))
            if c.fetchone()[0] == 0:
                break

        total = fee["amount"]
        c.execute(
            """INSERT INTO invoices (invoice_number, client_id, template_id, data, partner_a_share, partner_b_share, status, total_amount)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (invoice_number, fee["client_id"], template_id, invoice_data, partner_a_share, partner_b_share, "draft", total)
        )
        invoice_id = c.lastrowid

        c.execute("""
            SELECT id FROM payment_events
            WHERE recurring_fee_id=? AND status IN ('not_sent', 'sent')
            ORDER BY due_date ASC LIMIT 1
        """, (fee_id,))
        pe_row = c.fetchone()
        if pe_row:
            c.execute("UPDATE payment_events SET invoice_id=? WHERE id=?", (invoice_id, pe_row[0]))

        conn.commit()
        return {"invoice_id": invoice_id, "invoice_number": invoice_number}

@app.get("/todos")
def get_todos(status: str = None, priority: str = None, client_id: int = None):
    with db() as conn:
        c = conn.cursor()
        query = """
            SELECT t.*, c.name as client_name
            FROM todos t
            LEFT JOIN clients c ON t.client_id = c.id
            WHERE 1=1
        """
        params = []
        if status:
            query += " AND t.status = ?"
            params.append(status)
        if priority:
            query += " AND t.priority = ?"
            params.append(priority)
        if client_id:
            query += " AND t.client_id = ?"
            params.append(client_id)
        query += " ORDER BY CASE t.priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, t.due_date ASC NULLS LAST, t.created_at DESC"
        c.execute(query, params)
        rows = c.fetchall()
        cols = [desc[0] for desc in c.description]
        return [dict(zip(cols, row)) for row in rows]

@app.post("/todos")
def create_todo(todo: dict = Body(...)):
    with db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO todos (title, description, due_date, priority, status, client_id, invoice_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            todo.get("title"),
            todo.get("description"),
            todo.get("due_date"),
            todo.get("priority", "medium"),
            todo.get("status", "pending"),
            todo.get("client_id"),
            todo.get("invoice_id")
        ))
        conn.commit()
        return {"id": c.lastrowid, "ok": True}

@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, todo: dict = Body(...)):
    from datetime import datetime
    with db() as conn:
        c = conn.cursor()
        completed_at = None
        if todo.get("status") == "completed":
            c.execute("SELECT completed_at FROM todos WHERE id=?", (todo_id,))
            row = c.fetchone()
            if row and not row[0]:
                completed_at = datetime.now().isoformat()
            elif row:
                completed_at = row[0]
        c.execute("""
            UPDATE todos SET title=?, description=?, due_date=?, priority=?, status=?, client_id=?, invoice_id=?, completed_at=?
            WHERE id=?
        """, (
            todo.get("title"),
            todo.get("description"),
            todo.get("due_date"),
            todo.get("priority"),
            todo.get("status"),
            todo.get("client_id"),
            todo.get("invoice_id"),
            completed_at,
            todo_id
        ))
        conn.commit()
        return {"ok": True}

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    with db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM todos WHERE id=?", (todo_id,))
        conn.commit()
        return {"ok": True}

@app.get("/calendar/events")
def get_calendar_events(start: str = None, end: str = None, client_id: int = None):
    with db() as conn:
        c = conn.cursor()
        query = """
            SELECT e.*, c.name as client_name
            FROM calendar_events e
            LEFT JOIN clients c ON e.client_id = c.id
            WHERE 1=1
        """
        params = []
        if start:
            query += " AND e.start_datetime >= ?"
            params.append(start)
        if end:
            query += " AND e.start_datetime <= ?"
            params.append(end)
        if client_id:
            query += " AND e.client_id = ?"
            params.append(client_id)
        query += " ORDER BY e.start_datetime ASC"
        c.execute(query, params)
        rows = c.fetchall()
        cols = [desc[0] for desc in c.description]
        return [dict(zip(cols, row)) for row in rows]

@app.post("/calendar/events")
def create_calendar_event(event: dict = Body(...)):
    with db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO calendar_events (title, description, start_datetime, end_datetime, all_day, event_type, client_id, color, reminder_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.get("title"),
            event.get("description"),
            event.get("start_datetime"),
            event.get("end_datetime"),
            1 if event.get("all_day") else 0,
            event.get("event_type", "appointment"),
            event.get("client_id"),
            event.get("color", "#4a90e2"),
            event.get("reminder_minutes")
        ))
        conn.commit()
        return {"id": c.lastrowid, "ok": True}

@app.put("/calendar/events/{event_id}")
def update_calendar_event(event_id: int, event: dict = Body(...)):
    with db() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE calendar_events SET title=?, description=?, start_datetime=?, end_datetime=?, all_day=?, event_type=?, client_id=?, color=?, reminder_minutes=?
            WHERE id=?
        """, (
            event.get("title"),
            event.get("description"),
            event.get("start_datetime"),
            event.get("end_datetime"),
            1 if event.get("all_day") else 0,
            event.get("event_type"),
            event.get("client_id"),
            event.get("color"),
            event.get("reminder_minutes"),
            event_id
        ))
        conn.commit()
        return {"ok": True}

@app.delete("/calendar/events/{event_id}")
def delete_calendar_event(event_id: int):
    with db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM calendar_events WHERE id=?", (event_id,))
        conn.commit()
        return {"ok": True}

