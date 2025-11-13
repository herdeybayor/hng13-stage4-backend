-- Create separate databases for each service
-- This ensures proper isolation and allows each service to manage its own migrations

-- User Service Database
CREATE DATABASE user_service;
GRANT ALL PRIVILEGES ON DATABASE user_service TO postgres;

-- Template Service Database
CREATE DATABASE template_service;
GRANT ALL PRIVILEGES ON DATABASE template_service TO postgres;

-- Notifications Database (for shared data if needed)
-- This is already created as POSTGRES_DB=notifications
GRANT ALL PRIVILEGES ON DATABASE notifications TO postgres;

\echo 'Databases created successfully!'

