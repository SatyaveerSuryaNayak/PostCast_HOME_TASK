#!/bin/bash

echo "Starting Portcast Home Task Celery worker..."
echo ""

# Activate venv and start Celery
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info

