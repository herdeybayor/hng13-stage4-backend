# ⚡ Quick Start - 3 Commands

Get your notification system running in under 5 minutes!

## 🎯 The Fastest Way

```bash
# 1. Navigate to project
cd /path/to/hng13-stage4-backend

# 2. Create .env file (update with your values)
cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/notifications
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://admin:admin123@rabbitmq:5672/
SECRET_KEY=change-me-to-something-very-secure-and-random-min-32-chars
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourapp.com
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO
EOF

# 3. Deploy everything!
make deploy
```

## ✅ That's It!

The `make deploy` command automatically:

- ✅ Builds all Docker images
- ✅ Starts PostgreSQL, Redis, and RabbitMQ
- ✅ Starts all application services
- ✅ Runs database migrations automatically
- ✅ Verifies everything is working

## 🌐 Access Your Services

Once complete (takes ~2-3 minutes):

| Service              | URL                        | Description                       |
| -------------------- | -------------------------- | --------------------------------- |
| **API Gateway**      | http://localhost:8000/docs | Main API endpoint                 |
| **User Service**     | http://localhost:8001/docs | User management                   |
| **Template Service** | http://localhost:8002/docs | Template management               |
| **RabbitMQ UI**      | http://localhost:15672     | Queue monitoring (admin/admin123) |

## 🔄 Common Commands

```bash
make status     # Check if everything is running
make logs       # View all logs
make health     # Health check all services
make stop       # Stop all services
make restart    # Restart all services
make help       # Show all available commands
```

## 🎓 How It Works

### Automatic Migrations

**You don't need to run migrations manually!** Each service automatically:

1. Waits for the database to be ready
2. Checks for pending migrations
3. Applies them automatically
4. Starts the application

This happens every time services start, so your database is always up to date.

### What's Running

After deployment, you'll have:

```
Infrastructure:
  • PostgreSQL (database)
  • Redis (caching)
  • RabbitMQ (message queue)

Application Services:
  • API Gateway (port 8000)
  • User Service (port 8001)
  • Template Service (port 8002)
  • Email Workers (2 instances)
  • Push Workers (2 instances)
```

## 🐛 Troubleshooting

### Services won't start?

```bash
make logs
```

### Port already in use?

```bash
# Stop any conflicting services first
make clean
make deploy
```

### Need to reset everything?

```bash
make clean
make deploy
```

## 📚 Need More Info?

- **Complete guide**: See `DEPLOYMENT.md`
- **Migration details**: See `ALEMBIC_SETUP_GUIDE.md`
- **Architecture**: See `SYSTEM_DESIGN.md`
- **All commands**: Run `make help`

## 🎉 Test It Out

Once services are running, create a test user:

```bash
curl -X POST http://localhost:8001/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "securepass123"
  }'
```

---

**That's it! You're ready to build amazing notifications! 🚀**
