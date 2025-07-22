#Make sure port is set to public in codespaces
from pprint import pprint
from flask import Flask, request
import json
import requests
from peewee import PostgresqlDatabase, Model, IntegerField, CharField, DecimalField

# Step 1: Connect to your PostgreSQL database
db = PostgresqlDatabase(
    'main',
    user='postgres',
    password='@Hardu2005',
    host='172.105.15.152',
    port=5432
)

# Step 2: Define your Deals model (example columns, adjust as needed)
class Deals(Model):
    id = IntegerField()
    AFM_ID = CharField()
    Interest_Amount_1 = DecimalField(null=True)

    class Meta:
        database = db
        table_name = 'Deals'

def update_interest_amount(deal_id, new_interest_amount):
    db.connect()
    query = Deals.update(Interest_Amount_1=new_interest_amount).where(Deals.id == deal_id)
    rows_updated = query.execute()
    db.close()
    print(f"{rows_updated} row(s) updated.")
    return rows_updated


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


app = Flask(__name__)

@app.route('/')
def hello_world():
    print("it worked")
    return 'Hello World!'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = (parse_webhook_bytes(request.get_data())['data']['rows'][0])
    interest = (data['Interest_Rate'] / 100) * (data['Principal'] / 12)
    pprint(interest)
    #print("Headers:", request.headers, flush=True)
    #print("Body:", request.get_data(as_text=True), flush=True)
    pprint(data)
    update_interest_amount(data['id'], interest)
    return "OK", 200

if __name__ == '__main__':
     app.run()


