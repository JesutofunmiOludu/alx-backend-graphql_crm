import requests
from celery import shared_task
from datetime import datetime

GRAPHQL_URL = "http://127.0.0.1:8000/graphql/"

QUERY = """
query {
  allCustomers {
    id
  }
  allOrders {
    id
    totalAmount
  }
}
"""
@shared_task
def generate_crm_report():
    response = requests.post(
        GRAPHQL_URL,
        json={"query": QUERY},
        headers={"Content-Type": "application/json"},
        timeout=30
    )

    data = response.json().get("data", {})

    customers = data.get("allCustomers", [])
    orders = data.get("allOrders", [])

    total_customers = len(customers)
    total_orders = len(orders)
    total_revenue = sum(
        order.get("totalAmount", 0) for order in orders
    )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = (
        f"{timestamp} - Report: "
        f"{total_customers} customers, "
        f"{total_orders} orders, "
        f"{total_revenue} revenue\n"
    )

    with open("/tmp/crm_report_log.txt", "a") as f:
        f.write(log_line)