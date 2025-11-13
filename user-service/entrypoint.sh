#!/bin/sh
# Entrypoint script for User Service with automatic migrations

set -e

echo "🚀 Starting User Service..."

# Function to wait for database
wait_for_db() {
    echo "⏳ Waiting for PostgreSQL to be ready..."
    
    max_retries=30
    retry_count=0
    
    # Extract database connection details from DATABASE_URL
    # Format: postgresql+asyncpg://user:pass@host:port/dbname
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\(.*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\(.*\)/\1/p')
    DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\(.*\):.*/\1/p')
    
    while [ $retry_count -lt $max_retries ]; do
        if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
            echo "✅ Database is ready!"
            return 0
        fi
        
        retry_count=$((retry_count + 1))
        echo "⏳ Attempt $retry_count/$max_retries - Database not ready yet..."
        sleep 2
    done
    
    echo "❌ Database connection timeout!"
    exit 1
}

# Function to run migrations
run_migrations() {
    echo "🔄 Running database migrations..."
    
    if alembic current > /dev/null 2>&1; then
        echo "📊 Current migration status:"
        alembic current
        
        echo "⬆️ Applying pending migrations..."
        alembic upgrade head
        
        if [ $? -eq 0 ]; then
            echo "✅ Migrations completed successfully!"
        else
            echo "❌ Migration failed!"
            exit 1
        fi
    else
        echo "⚠️ No migrations found yet. Skipping migration step."
        echo "💡 Run 'alembic revision --autogenerate -m \"Initial migration\"' to create your first migration."
    fi
}

# Main execution
echo "================================="
echo "User Service Initialization"
echo "================================="

# Wait for database to be ready
wait_for_db

# Run migrations automatically
run_migrations

echo "================================="
echo "🎉 User Service Ready!"
echo "================================="

# Start the application
exec "$@"

