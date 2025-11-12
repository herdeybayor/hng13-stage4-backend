# Getting Started - Distributed Notification System

Welcome to the HNG13 Stage 4 Backend Task! This guide will help you and your team get started quickly.

---

## 📋 What You'll Build

A distributed notification system that:

- Sends **email** and **push notifications**
- Uses **microservices architecture** (5 services)
- Processes notifications **asynchronously** with RabbitMQ
- Handles **1,000+ notifications per minute**
- Includes **circuit breaker**, **retry logic**, and **failure handling**

---

## 🚀 Quick Start (3 Steps)

### Option 1: Automated Setup (Recommended)

```bash
# Make the script executable
chmod +x quick-start.sh

# Run the quick start script
./quick-start.sh
```

The script will:

1. Check prerequisites (Docker, Docker Compose)
2. Set up environment files
3. Start all services
4. Run health checks
5. Show you access URLs

### Option 2: Manual Setup

```bash
# 1. Copy environment file
cp .env.example .env
# Edit .env with your settings (SMTP, FCM credentials, etc.)

# 2. Start infrastructure
docker-compose up -d postgres redis rabbitmq

# 3. Start all services
docker-compose up -d

# 4. Check status
docker-compose ps
```

### Option 3: Using Makefile

```bash
# Initialize project
make init

# Start services
make start

# View logs
make logs

# See all commands
make help
```

---

## 📚 Documentation Structure

Your team has access to comprehensive documentation:

### 1. **README.md** 📖

- Project overview
- Quick start guide
- API endpoints
- Docker commands
- Technology stack

👉 **Start here** for general project information.

---

### 2. **IMPLEMENTATION_GUIDE.md** 💻

- **Complete code examples** for all services
- Database schemas and models
- API specifications
- Circuit breaker implementation
- Retry logic with exponential backoff
- Testing strategies
- Deployment guide

👉 **Use this** when writing code for each service.

---

### 3. **SYSTEM_DESIGN.md** 🏗️

- High-level architecture diagrams (Mermaid)
- Service communication flows
- Queue structure diagrams
- Retry and failure flow diagrams
- Database relationship diagrams
- Scaling plan
- Complete end-to-end request flow

👉 **Submit this** as your system design document.

---

### 4. **PROJECT_ROADMAP.md** 🗺️

- Week-by-week implementation plan
- Daily tasks for 4 team members
- Role assignments
- Testing milestones
- Risk mitigation strategies
- Progress tracking checklist

👉 **Follow this** to stay on track with your team.

---

### 5. **task.txt** 📋

- Original task requirements
- Performance targets
- Sample request formats
- Learning outcomes

👉 **Reference this** to ensure you meet all requirements.

---

## 🎯 Your Team (4 Members)

Here's how to divide the work:

| Member       | Responsibilities                   | Services                               |
| ------------ | ---------------------------------- | -------------------------------------- |
| **Member 1** | Infrastructure, API Gateway, CI/CD | API Gateway, Docker, RabbitMQ setup    |
| **Member 2** | User management, Authentication    | User Service, JWT, Database            |
| **Member 3** | Templates, Email notifications     | Template Service, Email Worker, SMTP   |
| **Member 4** | Push notifications, Testing        | Push Service, Unit tests, Load testing |

📝 **Update your Airtable** with team member information!

---

## 🏃 4-Week Implementation Plan

### Week 1: Foundation (Days 1-7)

- ✅ Set up project structure
- ✅ Configure Docker infrastructure
- ✅ Create basic service skeletons
- ✅ Implement health checks
- 📦 **Deliverable**: All services running with health checks

### Week 2: Core Functionality (Days 8-14)

- ✅ Implement authentication
- ✅ Connect services via RabbitMQ
- ✅ Send first email notification
- ✅ Send first push notification
- 📦 **Deliverable**: End-to-end notification flow working

### Week 3: Reliability (Days 15-21)

- ✅ Add circuit breaker
- ✅ Implement retry logic
- ✅ Set up DLQ
- ✅ Write tests
- ✅ Run load tests
- 📦 **Deliverable**: System handles failures gracefully, passes load test

### Week 4: Deployment (Days 22-28)

- ✅ Complete documentation
- ✅ Set up CI/CD
- ✅ Deploy to production
- ✅ Create system design diagrams
- 📦 **Deliverable**: Production system + complete documentation

---

## 🔧 Essential Commands

### Development Workflow

```bash
# Start everything
make start

# View logs (all services)
make logs

# View logs (specific service)
make logs-api
make logs-email
make logs-rabbitmq

# Stop everything
make stop

# Restart after code changes
make restart

# Run tests
make test

# Check service health
make health
```

### Database Operations

```bash
# Run migrations
make db-migrate

# Open PostgreSQL shell
make db-shell

# Open Redis CLI
make redis-cli

# Reset database (WARNING: destroys data)
make db-reset
```

### Scaling Workers

```bash
# Scale email workers to 5 instances
make scale-email n=5

# Scale push workers to 3 instances
make scale-push n=3
```

---

## 🌐 Access Points

Once services are running, access them at:

| Service              | URL                          | Purpose                           |
| -------------------- | ---------------------------- | --------------------------------- |
| **API Gateway**      | http://localhost:8000/docs   | Main API, Swagger UI              |
| **User Service**     | http://localhost:8001/docs   | User management API               |
| **Template Service** | http://localhost:8002/docs   | Template management API           |
| **RabbitMQ UI**      | http://localhost:15672       | Queue monitoring (admin/admin123) |
| **Health Check**     | http://localhost:8000/health | System health status              |

---

## 📝 First Steps Checklist

- [ ] **Day 1 Morning**: All team members clone repository
- [ ] **Day 1 Morning**: Run `./quick-start.sh` to verify setup works
- [ ] **Day 1 Afternoon**: Each member reads their assigned sections in IMPLEMENTATION_GUIDE.md
- [ ] **Day 1 Afternoon**: Team meeting to discuss architecture and divide tasks
- [ ] **Day 2**: Member 1 sets up Docker infrastructure
- [ ] **Day 2-3**: Members 2, 3, 4 create their service skeletons
- [ ] **Day 4**: First team integration - connect services together
- [ ] **Day 5**: Review PROJECT_ROADMAP.md and adjust if needed

---

## 🧪 Testing Your Setup

### 1. Health Check Test

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "api-gateway",
  "timestamp": "2024-01-01T00:00:00"
}
```

### 2. Create User Test

```bash
curl -X POST http://localhost:8001/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "Test123!",
    "preferences": {"email": true, "push": true}
  }'
```

### 3. RabbitMQ Test

1. Open http://localhost:15672
2. Login: `admin` / `admin123`
3. Check "Queues" tab
4. Should see: `email.queue`, `push.queue`, `failed.queue`

---

## 🐛 Troubleshooting

### Services won't start?

```bash
# Check Docker is running
docker ps

# Check logs for errors
docker-compose logs

# Try rebuilding
make clean
make build
make start
```

### RabbitMQ connection errors?

```bash
# Restart RabbitMQ
docker-compose restart rabbitmq

# Wait 10 seconds then check
docker-compose logs rabbitmq
```

### Database errors?

```bash
# Reset database (WARNING: destroys data)
make db-reset

# Or just restart
docker-compose restart postgres
```

### Port already in use?

```bash
# Check what's using the port
lsof -i :8000   # For API Gateway
lsof -i :5672   # For RabbitMQ
lsof -i :5432   # For PostgreSQL

# Kill the process or change ports in docker-compose.yml
```

---

## 📊 Performance Targets

Your system must achieve:

| Metric           | Target                   | How to Test              |
| ---------------- | ------------------------ | ------------------------ |
| **Throughput**   | 1,000+ notifications/min | `make load-test`         |
| **API Response** | < 100ms (P95)            | Check Locust results     |
| **Success Rate** | 99.5%+                   | Monitor during load test |
| **Scalability**  | Horizontal scaling       | `make scale-email n=5`   |

---

## 🔐 Environment Configuration

### Required Environment Variables

Edit `.env` with these **essential** values:

```bash
# SMTP (for Email Service) - Choose one:

# Option 1: Gmail
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Generate at https://myaccount.google.com/apppasswords

# Option 2: SendGrid
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key

# FCM (for Push Service)
FCM_API_KEY=your-firebase-server-key  # Get from Firebase Console

# JWT Secret (generate a random string)
SECRET_KEY=your-super-secret-key-at-least-32-characters-long
```

---

## 🎥 Demo & Submission

Before submitting, prepare:

1. **System Design Diagram** ✅

   - Use SYSTEM_DESIGN.md (already has Mermaid diagrams)
   - Export or screenshot the diagrams
   - Show: services, queues, retry flow, scaling plan

2. **Explainer Video** 🎬

   - Record a walkthrough (5-10 minutes)
   - Show system running
   - Demonstrate key features
   - Explain architecture

3. **TikTok Video** 📱

   - Short version (< 60 seconds)
   - Show the working system
   - Highlight coolest features

4. **Code Repository** 💻
   - Push all code to GitHub
   - Ensure all team members have commits
   - Include README and documentation

---

## 🆘 Getting Help

### Documentation Order

1. Check this guide first
2. Read IMPLEMENTATION_GUIDE.md for code examples
3. Review SYSTEM_DESIGN.md for architecture
4. Follow PROJECT_ROADMAP.md for task breakdown

### Common Questions

**Q: Where do I start coding?**  
A: Read IMPLEMENTATION_GUIDE.md for complete code examples.

**Q: How do we divide work?**  
A: See PROJECT_ROADMAP.md for detailed role assignments.

**Q: What diagrams do we need?**  
A: SYSTEM_DESIGN.md has all required diagrams in Mermaid format.

**Q: How do we test load?**  
A: Run `make load-test` or `locust -f locustfile.py --host=http://localhost:8000`

**Q: Where do we deploy?**  
A: Request a server using `/request-server` command (see task.txt).

---

## 🎓 Learning Resources

- **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/
- **RabbitMQ Getting Started**: https://www.rabbitmq.com/getstarted.html
- **Docker Compose**: https://docs.docker.com/compose/
- **Circuit Breaker Pattern**: https://martinfowler.com/bliki/CircuitBreaker.html

---

## ✅ Success Checklist

Before submitting, ensure:

- [ ] All 5 services are running
- [ ] Email notifications work
- [ ] Push notifications work
- [ ] Circuit breaker prevents cascading failures
- [ ] Failed messages go to DLQ
- [ ] System handles 1,000+ notifications/min
- [ ] All tests pass (70%+ coverage)
- [ ] System deployed to server
- [ ] System design diagram submitted
- [ ] Documentation complete
- [ ] Code follows snake_case naming
- [ ] Response format matches specification
- [ ] CI/CD workflow configured
- [ ] Team info in Airtable

---

## 🎉 You're Ready!

Everything you need is here:

1. **GETTING_STARTED.md** (this file) - Start here
2. **IMPLEMENTATION_GUIDE.md** - Code examples
3. **SYSTEM_DESIGN.md** - Architecture diagrams
4. **PROJECT_ROADMAP.md** - Week-by-week plan
5. **README.md** - Project reference

### Next Steps:

```bash
# 1. Set up your environment
./quick-start.sh

# 2. Verify everything works
make health

# 3. Read the implementation guide
cat IMPLEMENTATION_GUIDE.md

# 4. Start coding!
```

---

**Good luck with your implementation! 🚀**

Questions? Check the documentation or ask your team!

---

**Version**: 1.0  
**Last Updated**: 2024  
**Status**: Ready to Start! ✨
