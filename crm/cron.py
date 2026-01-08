from gql.transport.requests import RequestsHTTPTransport
from gql import gql, Client
from datetime import datetime
import requests

LOG_FILE = "/tmp/crm_heartbeat_log.txt"
GRAPHQL_URL = "http://localhost:8000/graphql"

def log_crm_heartbeat():
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    message = f"{timestamp} CRM is alive"

    try:
        query = {"query": "{ hello }"}
        response = requests.post(GRAPHQL_URL, json=query, timeout=5)
        if response.status_code != 200:
            message += " - GraphQL not responding"
    except Exception:
        message += " - GraphQL error"

    with open(LOG_FILE, "a") as file:
        file.write(message + "\n")
def update_low_stock():
    response = requests.post(
        GRAPHQL_URL,
        json={"query": MUTATION},
        headers={"Content-Type": "application/json"},
        timeout=30
    )

    data = response.json()

    result = data.get("data", {}).get("updateLowStockProducts", {})
    products = result.get("products", [])

    log_file = "/tmp/low_stock_updates_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "a") as f:
        f.write(f"\n[{timestamp}] Low stock restock job executed\n")
        for product in products:
            f.write(f" - {product['name']} -> New Stock: {product['stock']}\n")
