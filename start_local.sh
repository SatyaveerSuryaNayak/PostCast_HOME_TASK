#!/bin/bash

echo "Starting Portcast Home Task API locally..."
echo ""

# Activate venv and start API
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

