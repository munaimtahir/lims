#!/bin/bash
set -e

# Create venv
if [ ! -d "venv" ]; then
    echo "Creating venv..."
    python3 -m venv venv
fi

source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
# We might fail on postgres adapters if libraries are missing. 
# We'll try to install binary version of psycopg2 if possible, or skip strict production.txt
echo "Installing dependencies..."

# Try installing base first
pip install -r lims-backend/requirements/base.txt

# Try installing psycopg2-binary instead of source to avoid build deps
pip install psycopg2-binary

# Install other prod reqs (filtering out psycopg2 if it's there)
grep -v "psycopg2" lims-backend/requirements/production.txt > lims-backend/requirements/production_no_psycopg2.txt
pip install -r lims-backend/requirements/production_no_psycopg2.txt

echo "Environment setup complete."
