#!/usr/bin/env python3

from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

GRAPHQL_URL = "http://localhost:8000/graphql"
LOG_FILE = "/tmp/order_reminders_log.txt"

transport = RequestsHTTPTransport(
    url=GRAPHQL_URL,
    verify=True,
    retries=3,
)

client = Client(transport=transport, fetch_schema_from_transport=True)

one_week_ago = (datetime.now() - timedelta(days=7)).isoformat()

query = gql("""
query GetRecentOrders($date: DateTime!) {
  orders(orderDate_Gte: $date, status: "PENDING") {
    id
    customer {
      email
    }
  }
}
""")

params = {"date": one_week_ago}

result = client.execute(query, variable_values=params)

with open(LOG_FILE, "a") as log:
    for order in result["orders"]:
        log.write(f"{datetime.now()} - Order ID: {order['id']}, Email: {order['customer']['email']}\n")

print("Order reminders processed!")
