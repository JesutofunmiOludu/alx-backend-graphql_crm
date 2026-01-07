#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
MANAGE_PY="$PROJECT_DIR/manage.py"
LOG_FILE="/tmp/customer_cleanup_log.txt"

DELETED_COUNT=$(python3 "$MANAGE_PY" shell -c "
from datetime import timedelta
from django.utils import timezone
from crm.models import Customer

one_year_ago = timezone.now() - timedelta(days=365)

inactive_customers = Customer.objects.filter(
    order__isnull=True,
    created_at__lt=one_year_ago
)

count = inactive_customers.count()
inactive_customers.delete()
print(count)
")

echo \"\$(date '+%Y-%m-%d %H:%M:%S') - Deleted \$DELETED_COUNT inactive customers\" >> \"$LOG_FILE\"
