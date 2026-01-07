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
