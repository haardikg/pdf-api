#Make sure port is set to public in codespaces
from pprint import pprint
from flask import Flask, request
import json
import requests
import threading
import psycopg2
import select
from peewee import PostgresqlDatabase, Model, IntegerField, CharField, DecimalField

# Step 1: Connect to your PostgreSQL database
db = PostgresqlDatabase(
    'main',
    user='postgres',
    password='@Hardu2005',
    host='172.105.15.152',
    port=5432
)

# Step 2: Define Models
class Deals(Model):
    id = IntegerField()
    AFM_ID = CharField()
    Interest_Amount_1 = DecimalField(null=True)

    class Meta:
        database = db
        table_name = 'Deals'

class LoanSummary(Model):
    Deals_id = IntegerField()
    Remaining_Principal = DecimalField(null=True)
    Remaining_Interest = DecimalField(null=True)
    Repayment_Progress = IntegerField()
    Remaining_Penalties = IntegerField()

    class Meta:
        database = db
        table_name = 'Loan_Summary'

class Payments(Model):
    id = IntegerField()
    Payment_Type = CharField()
    Amount = DecimalField()
    Loan_Summary_id = IntegerField()

    class Meta:
        database = db
        table_name = 'Payments'

# === Business Logic ===
def update_interest_amount(deal_id, new_interest_amount):
    db.connect()
    query = Deals.update(Interest_Amount_1=new_interest_amount).where(Deals.id == deal_id)
    rows_updated = query.execute()
    db.close()
    print(f"{rows_updated} row(s) updated.")
    return rows_updated

def create_loan_summary(deal_id, principal, interest):
    db.connect()
    record = LoanSummary.create(
        Deals_id=deal_id,
        Remaining_Principal=principal,
        Remaining_Interest=interest,
        Repayment_Progress=0,
        Remaining_Penalties=0
    )
    db.close()
    return record

def update_balances(summary_id):
    rows = Payments.select().where((Payments.Loan_Summary_id == summary_id) & (Payments.Payment_Type == 'Principal'))
    for row in rows:
        print(row.Payment_Type, row.Amount, 'hi')

def parse_webhook_bytes(raw_bytes):
    try:
        json_string = raw_bytes.decode('utf-8')
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to decode bytes: {e}")
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    return data

# === Flask App ===
app = Flask(__name__)

@app.route('/')
def hello_world():
    print("it worked")
    return 'Hello World!'

@app.route('/hooks/update_interest', methods=['POST'])
def update_interest():
    data = (parse_webhook_bytes(request.get_data())['data']['rows'][0])
    interest = (data['Interest_Rate'] / 100) * (data['Principal'] / 12)
    pprint(interest)
    pprint(data)
    update_interest_amount(data['id'], interest)
    return "OK", 200

@app.route('/hooks/add_loan_summary', methods=['POST'])
def add_loan_summary():
    data = (parse_webhook_bytes(request.get_data())['data']['rows'][0])
    pprint(data)
    create_loan_summary(data['id'], data['Principal'], data['Total_Interest'])
    return "OK", 200

@app.route('/hooks/process_payments', methods=['POST'])
def process_payments():
    data = (parse_webhook_bytes(request.get_data())['data']['rows'][0])
    pprint(data)
    update_balances(data['id'])
    return "OK", 200

# === Background Listener Thread ===
def listen_for_new_payments():
    try:
        conn = psycopg2.connect(
            dbname='main',
            user='postgres',
            password='@Hardu2005',
            host='172.105.15.152',
            port=5432
        )
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("LISTEN payment_inserted;")
        print("🔔 Listening for new payments in background...")

        while True:
            if select.select([conn], [], [], 5) == ([], [], []):
                continue
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                print(f"✅ New payment inserted! ID: {notify.payload}")
    except Exception as e:
        print("⚠️ Error in listener:", e)

# === Run Flask with Background Thread ===
if __name__ == '__main__':
    listener_thread = threading.Thread(target=listen_for_new_payments, daemon=True)
    listener_thread.start()
    app.run(host="0.0.0.0", port=5000)
