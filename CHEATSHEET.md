# 🚀 Command Cheatsheet - Quick Reference

## ⚡ Most Important Commands

```bash
make deploy      # 🎯 Deploy everything (first time or updates)
make start       # ▶️  Start all services
make stop        # ⏸️  Stop all services
make logs        # 📋 View all logs
make health      # 💚 Check service health
make help        # ❓ Show all commands
```

---

## 🚀 Deployment

| Command          | What It Does                                    |
| ---------------- | ----------------------------------------------- |
| `make deploy`    | **Complete automated deployment** (recommended) |
| `make first-run` | Setup + deploy (for first time)                 |
| `make all`       | Clean, build, and start everything              |
| `make quick`     | Quick start for development                     |

---

## 🐳 Docker Operations

| Command        | What It Does                             |
| -------------- | ---------------------------------------- |
| `make build`   | Build all Docker images                  |
| `make start`   | Start all services                       |
| `make stop`    | Stop all services                        |
| `make restart` | Restart all services                     |
| `make down`    | Stop and remove containers               |
| `make status`  | Show status of all services              |
| `make clean`   | Clean up containers, volumes, and caches |

---

## 💾 Database Operations

| Command                     | What It Does                       |
| --------------------------- | ---------------------------------- |
| `make db-status`            | **Show current migration status**  |
| `make db-migrate`           | Run migrations (usually automatic) |
| `make db-rollback`          | Rollback last migration            |
| `make db-reset`             | Reset database (⚠️ destroys data!) |
| `make db-shell`             | Open PostgreSQL shell              |
| `make db-create-migrations` | Create initial migrations          |

---

## 📊 Monitoring & Logs

| Command              | What It Does                   |
| -------------------- | ------------------------------ |
| `make logs`          | View all service logs          |
| `make logs-api`      | View API Gateway logs          |
| `make logs-user`     | View User Service logs         |
| `make logs-template` | View Template Service logs     |
| `make logs-email`    | View Email Worker logs         |
| `make logs-push`     | View Push Worker logs          |
| `make health`        | Check health of all services   |
| `make queue-stats`   | Show RabbitMQ queue statistics |

---

## 🔧 Development

| Command               | What It Does                             |
| --------------------- | ---------------------------------------- |
| `make dev`            | Start in development mode                |
| `make shell-user`     | Open shell in User Service container     |
| `make shell-template` | Open shell in Template Service container |
| `make shell-api`      | Open shell in API Gateway container      |

---

## 📈 Scaling

| Command                | What It Does                       |
| ---------------------- | ---------------------------------- |
| `make scale-email n=5` | Scale email workers to 5 instances |
| `make scale-push n=3`  | Scale push workers to 3 instances  |

---

## 🧪 Testing

| Command          | What It Does               |
| ---------------- | -------------------------- |
| `make test`      | Run all tests              |
| `make test-cov`  | Run tests with coverage    |
| `make load-test` | Run load tests with Locust |

---

## 💿 Backup & Restore

| Command                        | What It Does           |
| ------------------------------ | ---------------------- |
| `make backup`                  | Create database backup |
| `make restore file=backup.sql` | Restore from backup    |

---

## 📍 Service URLs

| Service              | URL                        | Description                       |
| -------------------- | -------------------------- | --------------------------------- |
| **API Gateway**      | http://localhost:8000/docs | Main API                          |
| **User Service**     | http://localhost:8001/docs | User management                   |
| **Template Service** | http://localhost:8002/docs | Template management               |
| **RabbitMQ UI**      | http://localhost:15672     | Queue management (admin/admin123) |

---

## 🔑 Docker Compose Commands (Alternative)

```bash
# Direct Docker Compose usage
docker-compose up -d                    # Start services
docker-compose down                     # Stop services
docker-compose ps                       # View status
docker-compose logs -f user-service    # View specific logs
docker-compose restart user-service    # Restart specific service
docker-compose exec user-service bash  # Enter container
```

---

## 🗂️ Important Files

| File                                 | Purpose                                            |
| ------------------------------------ | -------------------------------------------------- |
| `.env`                               | Environment variables (create from `env.template`) |
| `docker-compose.yml`                 | Service orchestration                              |
| `Makefile`                           | Automation commands                                |
| `user-service/alembic/versions/`     | User service migrations                            |
| `template-service/alembic/versions/` | Template service migrations                        |

---

## 🆘 Troubleshooting Quick Fixes

```bash
# Services won't start?
make logs                    # Check what's wrong
make clean && make deploy    # Nuclear option

# Database issues?
make db-status               # Check migration state
make db-reset                # Reset database (⚠️ destroys data)

# Port conflicts?
make down                    # Stop everything
# Edit docker-compose.yml ports
make start                   # Start again

# Can't connect to services?
make health                  # Check health status
docker-compose ps            # See if containers are up

# Migration issues?
make logs-user               # Check user service logs
make logs-template           # Check template service logs
make db-status               # See migration status

# Want to start fresh?
make clean                   # Clean everything
make deploy                  # Deploy fresh
```

---

## 📖 Documentation Quick Links

- **QUICKSTART.md** - Get started in 3 commands
- **DEPLOYMENT.md** - Complete deployment guide
- **AUTOMATION_SUMMARY.md** - What's automated and why
- **ALEMBIC_SETUP_GUIDE.md** - Deep dive into migrations
- **README.md** - Project overview

---

## 💡 Pro Tips

1. **First time?** Just run `make deploy`
2. **Check status often:** `make health` and `make status`
3. **Read the logs:** Most issues show up in `make logs`
4. **Migrations are automatic:** No need to run them manually
5. **Use Make commands:** They're easier than Docker Compose
6. **Check help anytime:** `make help` shows all commands

---

## 🎯 Common Workflows

### Daily Development

```bash
make start       # Start services
make logs        # Check if everything's ok
# ... make code changes ...
make restart     # Restart to see changes
```

### Adding New Model Field

```bash
# 1. Edit model file
vim user-service/app/models/user.py

# 2. Create migration
docker-compose exec user-service alembic revision --autogenerate -m "Add field"

# 3. Restart (migration applies automatically)
make restart
```

### Deploying Updates

```bash
git pull              # Get latest code
make deploy           # Redeploy everything
make health           # Verify deployment
```

### Debugging Issues

```bash
make logs             # See all logs
make health           # Check health
make db-status        # Check migrations
make status           # Check containers
```

---

**🎉 Bookmark this page for quick reference!**

Run `make help` anytime to see all available commands.
