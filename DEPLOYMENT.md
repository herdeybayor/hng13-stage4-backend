# 🚀 Automated Deployment Guide

This guide will help you deploy the Notification System with minimal manual steps. Everything is automated!

## 🎯 One-Command Deployment

For the absolute quickest start:

```bash
make deploy
```

That's it! This single command will:

- ✅ Set up your environment
- ✅ Build all Docker images
- ✅ Start all services
- ✅ Run database migrations automatically
- ✅ Verify everything is working

---

## 📋 Prerequisites

Before running the deployment, make sure you have:

1. **Docker & Docker Compose** installed

   ```bash
   docker --version
   docker-compose --version
   ```

2. **Make** installed (usually pre-installed on macOS/Linux)
   ```bash
   make --version
   ```

---

## 🏃 Quick Start (Recommended)

### Step 1: Clone and Navigate

```bash
cd /path/to/hng13-stage4-backend
```

### Step 2: Run Automated Deployment

```bash
make deploy
```

The script will:

1. Create `.env` file from `.env.example` (if it doesn't exist)
2. Ask you to configure environment variables
3. Build all Docker images
4. Start infrastructure (PostgreSQL, Redis, RabbitMQ)
5. Start application services
6. Run migrations automatically
7. Display service status and access URLs

### Step 3: Access Your Services

Once deployment completes, access:

- **API Gateway**: http://localhost:8000/docs
- **User Service**: http://localhost:8001/docs
- **Template Service**: http://localhost:8002/docs
- **RabbitMQ Management**: http://localhost:15672 (admin/admin123)

---

## 🔧 Configuration

### Environment Variables

The deployment script will create a `.env` file for you. Update these key values:

```env
# Database (Docker handles this automatically)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/notifications

# Security - CHANGE THIS!
SECRET_KEY=your-super-secret-key-min-32-characters-long

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourapp.com

# Optional: Push Notifications
FCM_API_KEY=your-fcm-api-key
FCM_PROJECT_ID=your-firebase-project
```

---

## 🎨 Alternative Commands

### First-Time Setup

```bash
make first-run
```

Combines setup and deployment in one command.

### Standard Operations

```bash
# Start services (migrations run automatically)
make start

# Stop services
make stop

# Restart services
make restart

# View logs
make logs

# Check service health
make health
```

### Database Operations

```bash
# Check migration status
make db-status

# Manually run migrations (usually not needed)
make db-migrate

# Rollback last migration
make db-rollback

# Reset database (WARNING: destroys all data)
make db-reset
```

### Rebuild Everything

```bash
make all
```

This will clean, build, and start everything fresh.

---

## 🔍 How Migrations Work (Automated!)

### What Happens Automatically

When services start, they **automatically**:

1. ✅ Wait for PostgreSQL to be ready
2. ✅ Check for pending migrations
3. ✅ Apply migrations if needed
4. ✅ Start the application

You don't need to run migrations manually!

### Behind the Scenes

Each service has an `entrypoint.sh` script that:

- Waits for the database connection
- Runs `alembic upgrade head` automatically
- Starts the FastAPI application

### Migration Files Location

Migrations are stored in:

- `user-service/alembic/versions/`
- `template-service/alembic/versions/`

These files are version-controlled and applied automatically.

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
make logs

# Check specific service
make logs-user      # User service logs
make logs-template  # Template service logs
make logs-rabbitmq  # RabbitMQ logs
```

### Migration Errors

```bash
# Check migration status
make db-status

# View service logs
make logs-user

# Reset and try again (destroys data!)
make db-reset
```

### Database Connection Issues

1. Ensure PostgreSQL container is running:

   ```bash
   docker-compose ps postgres
   ```

2. Check if PostgreSQL is healthy:

   ```bash
   docker-compose exec postgres pg_isready -U postgres
   ```

3. Restart infrastructure:
   ```bash
   docker-compose restart postgres
   ```

### "Command not found: alembic"

This shouldn't happen with Docker, but if it does:

```bash
# Rebuild the images
make build
```

### Port Already in Use

If ports are already taken:

1. Stop conflicting services
2. Or change ports in `docker-compose.yml`

---

## 🔄 Development Workflow

### Making Code Changes

1. **Edit code** in your service directories
2. **Restart service** to see changes:
   ```bash
   docker-compose restart user-service
   ```

Hot reload is enabled in development mode!

### Adding a New Model Field

1. **Edit the model** (e.g., `user-service/app/models/user.py`)
2. **Create migration** (inside container):
   ```bash
   docker-compose exec user-service alembic revision --autogenerate -m "Add new field"
   ```
3. **Migration applies automatically** on next restart!

### Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Load testing
make load-test
```

---

## 📊 Monitoring

### Service Health

```bash
# Quick health check
make health

# Detailed status
make status
```

### Queue Statistics

```bash
# View RabbitMQ stats
make queue-stats
```

### Logs

```bash
# All services
make logs

# Specific service
make logs-api
make logs-user
make logs-template
make logs-email
make logs-push
```

---

## 🚀 Production Deployment

### Build for Production

```bash
make deploy-prod
```

### Production Checklist

- [ ] Update `SECRET_KEY` with strong random value
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Configure real SMTP credentials
- [ ] Configure FCM/push credentials
- [ ] Set up SSL/TLS certificates
- [ ] Configure backup strategy
- [ ] Set up monitoring/alerting
- [ ] Review and restrict port access

### Backup & Restore

```bash
# Create backup
make backup

# Restore from backup
make restore file=backups/backup_20240101_120000.sql
```

---

## 🎓 Understanding the Architecture

### Services

1. **API Gateway** (Port 8000) - Main entry point
2. **User Service** (Port 8001) - User management
3. **Template Service** (Port 8002) - Template management
4. **Email Workers** - Process email notifications
5. **Push Workers** - Process push notifications

### Infrastructure

- **PostgreSQL** - Main database
- **Redis** - Caching layer
- **RabbitMQ** - Message queue

### Automatic Migration Flow

```
Service Starts
    ↓
Wait for Database
    ↓
Check Migrations (alembic current)
    ↓
Apply Pending Migrations (alembic upgrade head)
    ↓
Start Application (uvicorn)
```

---

## 📝 Common Tasks

### Scale Workers

```bash
# Scale email workers to 5 instances
make scale-email n=5

# Scale push workers to 3 instances
make scale-push n=3
```

### Access Containers

```bash
# User service shell
make shell-user

# Template service shell
make shell-template

# Database shell
make db-shell

# Redis CLI
make redis-cli
```

### Clean Up

```bash
# Stop and remove containers
make down

# Clean everything (containers, volumes, caches)
make clean

# Complete Docker cleanup (careful!)
make prune
```

---

## 🆘 Getting Help

### View All Commands

```bash
make help
```

This shows all available commands with descriptions.

### Check Service Status

```bash
make status
```

### Read the Logs

Most issues can be diagnosed from logs:

```bash
make logs
```

---

## ✅ Verification Checklist

After deployment, verify:

1. **Services Running**

   ```bash
   make status
   ```

   All services should show "Up"

2. **Health Checks Passing**

   ```bash
   make health
   ```

   All endpoints should return 200 OK

3. **Migrations Applied**

   ```bash
   make db-status
   ```

   Should show current migration version

4. **API Documentation Accessible**

   - http://localhost:8000/docs ✓
   - http://localhost:8001/docs ✓
   - http://localhost:8002/docs ✓

5. **RabbitMQ Running**
   - http://localhost:15672 ✓

---

## 🎉 Success!

If all checks pass, your notification system is ready to use!

Try creating a user through the API:

```bash
curl -X POST http://localhost:8001/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

**Need more details?** Check:

- `README.md` - Project overview
- `IMPLEMENTATION_GUIDE.md` - Detailed implementation docs
- `SYSTEM_DESIGN.md` - Architecture details
- `ALEMBIC_SETUP_GUIDE.md` - Migration deep-dive

---

Made with ❤️ for easy deployment!
