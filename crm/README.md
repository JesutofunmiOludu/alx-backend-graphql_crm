# CRM Weekly Report with Celery

## Setup

### 1. Install Redis

Ubuntu:
sudo apt install redis-server

Mac:
brew install redis

Start Redis:
redis-server

### 2. Install dependencies

pip install -r requirements.txt

### 3. Run migrations

python manage.py migrate

### 4. Start Celery Worker

celery -A crm worker -l info

### 5. Start Celery Beat

celery -A crm beat -l info

### 6. Verify

Check the log file:

cat /tmp/crm_report_log.txt
