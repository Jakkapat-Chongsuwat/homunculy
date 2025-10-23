#!/bin/bash
# Liquibase migration runner script

echo "Running Liquibase migrations..."

# Check if liquibase.properties exists
if [ ! -f "liquibase.properties" ]; then
    echo "Error: liquibase.properties not found!"
    exit 1
fi

# Run liquibase update
liquibase --defaultsFile=liquibase.properties update

echo "Migrations completed successfully."