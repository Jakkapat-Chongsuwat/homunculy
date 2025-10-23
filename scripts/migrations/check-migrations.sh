#!/bin/bash
# Liquibase migration status check script

echo "Checking Liquibase migration status..."

# Check if liquibase.properties exists
if [ ! -f "liquibase.properties" ]; then
    echo "Error: liquibase.properties not found!"
    exit 1
fi

# Run liquibase status
liquibase --defaultsFile=liquibase.properties status

echo "Migration status check completed."