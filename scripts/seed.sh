#!/bin/bash

# Database seeding script for healthcare planning system
# This script initializes the database with provinces, districts, and facilities

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEED_SCRIPT="$SCRIPT_DIR/seed_data.py"
JSON_FILE="$SCRIPT_DIR/province_district_hospitals.json"

# Default database configuration
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"5432"}
DB_NAME=${DB_NAME:-"hivtracker"}
DB_USER=${DB_USER:-"postgres"}
DB_PASSWORD=${DB_PASSWORD:-"postgres"}

# Export environment variables for Python script
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

print_status "Starting database seeding process..."
print_status "Database: $DB_NAME at $DB_HOST:$DB_PORT"

# Check if required files exist
if [ ! -f "$SEED_SCRIPT" ]; then
    print_error "Seed script not found: $SEED_SCRIPT"
    exit 1
fi

if [ ! -f "$JSON_FILE" ]; then
    print_error "JSON data file not found: $JSON_FILE"
    exit 1
fi

# Determine which Python command to use
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v py &> /dev/null; then
    PYTHON_CMD="py"
else
    print_error "Python is not installed or not in PATH"
    exit 1
fi

print_status "Using Python command: $PYTHON_CMD"

# Check if psycopg2 is available
print_status "Checking for required Python packages..."
if ! $PYTHON_CMD -c "import psycopg2" 2>/dev/null; then
    print_error "psycopg2 package is not installed"
    print_warning "Please install it with: pip install psycopg2-binary"
    exit 1
fi

print_success "Required packages are available"

# Check database connectivity
print_status "Testing database connection..."
CONNECTION_TEST=$($PYTHON_CMD -c "
import psycopg2
import sys
try:
    conn = psycopg2.connect(
        host='$DB_HOST',
        port='$DB_PORT',
        dbname='$DB_NAME',
        user='$DB_USER',
        password='$DB_PASSWORD'
    )
    conn.close()
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1)

if [[ $CONNECTION_TEST == *"SUCCESS"* ]]; then
    print_success "Database connection established"
else
    print_error "Cannot connect to database: $CONNECTION_TEST"
    print_warning "Make sure the database is running and credentials are correct."
    print_warning "You can test the connection manually with:"
    print_warning "psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
    exit 1
fi

# Run the seeding script
print_status "Running database seeding script..."
if $PYTHON_CMD "$SEED_SCRIPT"; then
    print_success "Database seeding completed successfully!"
    print_status "Your database has been initialized with:"
    print_status "- Provinces and districts from Rwanda"
    print_status "- Hospital facilities"
    print_status "- Basic account types and programs"
    print_status "- Default fiscal year"
else
    print_error "Database seeding failed!"
    exit 1
fi

print_success "Seeding process completed!"