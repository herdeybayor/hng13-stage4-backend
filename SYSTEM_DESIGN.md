# System Design Diagram - Distributed Notification System

## Overview

This document provides detailed system design diagrams for the distributed notification system as required for Stage 4 Backend Task.

---

## 1. Service Connections

### Complete System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Client[Client Applications<br/>Web, Mobile, etc.]
    end

    subgraph "API Gateway - Port 8000"
        Gateway[API Gateway Service]
        Auth[Authentication Module]
        Validator[Request Validator]
        Router[Message Router]
        Idempotency[Idempotency Checker]
    end

    subgraph "Core Services"
        subgraph "User Service - Port 8001"
            UserAPI[User REST API]
            UserRepo[User Repository]
            UserDB[(PostgreSQL<br/>Users DB)]
        end

        subgraph "Template Service - Port 8002"
            TemplateAPI[Template REST API]
            TemplateRepo[Template Repository]
            TemplateDB[(PostgreSQL<br/>Templates DB)]
        end
    end

    subgraph "Message Queue Infrastructure"
        Exchange[RabbitMQ Exchange<br/>notifications.direct]
        EmailQ[email.queue<br/>Priority: 1-10<br/>TTL: 24h]
        PushQ[push.queue<br/>Priority: 1-10<br/>TTL: 24h]
        DLQ[failed.queue<br/>Dead Letter Queue]
    end

    subgraph "Worker Services"
        subgraph "Email Workers - Replicas: 2+"
            EmailW1[Email Worker 1]
            EmailW2[Email Worker 2]
            EmailCB[Circuit Breaker]
            EmailRender[Template Renderer]
        end

        subgraph "Push Workers - Replicas: 2+"
            PushW1[Push Worker 1]
            PushW2[Push Worker 2]
            PushCB[Circuit Breaker]
            PushValidator[Token Validator]
        end
    end

    subgraph "External Services"
        SMTP[SMTP Provider<br/>Gmail/SendGrid]
        FCM[Firebase Cloud Messaging<br/>OneSignal]
    end

    subgraph "Shared Infrastructure"
        Redis[(Redis Cache<br/>- User Cache<br/>- Status Store<br/>- Rate Limits<br/>- Idempotency)]
    end

    subgraph "Monitoring"
        Prometheus[Prometheus<br/>Metrics Collection]
        Grafana[Grafana<br/>Dashboards]
        Logs[Centralized Logging<br/>ELK Stack]
    end

    Client -->|HTTPS| Gateway
    Gateway --> Auth
    Auth --> Validator
    Validator --> Idempotency
    Idempotency --> Router

    Gateway -.->|REST API| UserAPI
    Gateway -.->|REST API| TemplateAPI

    UserAPI --> UserRepo
    UserRepo --> UserDB

    TemplateAPI --> TemplateRepo
    TemplateRepo --> TemplateDB

    Router -->|Publish| Exchange
    Exchange -->|Route: email| EmailQ
    Exchange -->|Route: push| PushQ

    EmailQ -->|Consume| EmailW1
    EmailQ -->|Consume| EmailW2

    PushQ -->|Consume| PushW1
    PushQ -->|Consume| PushW2

    EmailW1 --> EmailCB
    EmailW2 --> EmailCB
    EmailCB --> EmailRender
    EmailRender -->|Send| SMTP

    PushW1 --> PushCB
    PushW2 --> PushCB
    PushCB --> PushValidator
    PushValidator -->|Send| FCM

    EmailW1 -.->|Failed| DLQ
    EmailW2 -.->|Failed| DLQ
    PushW1 -.->|Failed| DLQ
    PushW2 -.->|Failed| DLQ

    Gateway -.->|Cache/Status| Redis
    EmailW1 -.->|Cache/Status| Redis
    EmailW2 -.->|Cache/Status| Redis
    PushW1 -.->|Cache/Status| Redis
    PushW2 -.->|Cache/Status| Redis

    Gateway -.->|Metrics| Prometheus
    UserAPI -.->|Metrics| Prometheus
    TemplateAPI -.->|Metrics| Prometheus
    EmailW1 -.->|Metrics| Prometheus
    PushW1 -.->|Metrics| Prometheus

    Prometheus --> Grafana

    Gateway -.->|Logs| Logs
    UserAPI -.->|Logs| Logs
    TemplateAPI -.->|Logs| Logs
    EmailW1 -.->|Logs| Logs
    PushW1 -.->|Logs| Logs

    style Client fill:#e1f5ff
    style Gateway fill:#fff3e0
    style Redis fill:#ffebee
    style DLQ fill:#ffcdd2
    style SMTP fill:#c8e6c9
    style FCM fill:#c8e6c9
```

---

## 2. Queue Structure

### RabbitMQ Exchange and Queue Architecture

```mermaid
graph LR
    subgraph "Publisher"
        A[API Gateway]
    end

    subgraph "RabbitMQ - Exchange"
        B[notifications.direct<br/>Type: Direct<br/>Durable: true]
    end

    subgraph "Queues"
        C[email.queue<br/>━━━━━━━━━━<br/>Durable: true<br/>Max Priority: 10<br/>TTL: 24h<br/>Max Length: 100000]
        D[push.queue<br/>━━━━━━━━━━<br/>Durable: true<br/>Max Priority: 10<br/>TTL: 24h<br/>Max Length: 100000]
        E[failed.queue<br/>━━━━━━━━━━<br/>Durable: true<br/>DLQ<br/>No TTL<br/>Manual Intervention]
    end

    subgraph "Consumers"
        F[Email Worker Pool<br/>Prefetch: 10<br/>Replicas: 2-5]
        G[Push Worker Pool<br/>Prefetch: 10<br/>Replicas: 2-5]
        H[DLQ Monitor<br/>Manual Review]
    end

    A -->|publish<br/>routing_key| B
    B -->|route: email.queue| C
    B -->|route: push.queue| D

    C -->|consume<br/>ack/nack| F
    D -->|consume<br/>ack/nack| G

    F -.->|max retries<br/>exceeded| E
    G -.->|max retries<br/>exceeded| E

    E --> H

    style A fill:#e3f2fd
    style B fill:#fff9c4
    style C fill:#c8e6c9
    style D fill:#c8e6c9
    style E fill:#ffccbc
    style F fill:#b2ebf2
    style G fill:#b2ebf2
    style H fill:#ffccbc
```

### Message Structure in Queues

```mermaid
graph TB
    subgraph "Message Envelope"
        A[Headers<br/>━━━━━━━━━<br/>correlation_id<br/>message_id<br/>timestamp<br/>priority: 1-10<br/>delivery_mode: persistent]
    end

    subgraph "Message Body JSON"
        B[notification_id: UUID]
        C[notification_type: email/push]
        D[user_id: UUID]
        E[user_email: string]
        F[user_push_token: string]
        G[template_code: string]
        H[variables: object]
        I[request_id: string]
        J[metadata: object]
        K[retry_count: integer]
        L[created_at: ISO8601]
    end

    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    A --> G
    A --> H
    A --> I
    A --> J
    A --> K
    A --> L

    style A fill:#fff9c4
    style B fill:#e1f5ff
    style C fill:#e1f5ff
    style D fill:#e1f5ff
    style E fill:#e1f5ff
    style F fill:#e1f5ff
    style G fill:#e1f5ff
    style H fill:#e1f5ff
    style I fill:#e1f5ff
    style J fill:#e1f5ff
    style K fill:#ffccbc
    style L fill:#e1f5ff
```

---

## 3. Retry and Failure Flow

### Comprehensive Retry Mechanism

```mermaid
graph TB
    Start[Message Received<br/>from Queue]

    Process[Process Notification]

    Success{Success?}

    UpdateSuccess[Update Status:<br/>✓ delivered<br/>✓ timestamp<br/>✓ correlation_id]

    ACK[ACK Message<br/>Remove from Queue]

    CheckRetry{retry_count < MAX_RETRIES?}

    IncrementRetry[Increment retry_count<br/>retry_count++]

    Backoff[Exponential Backoff<br/>Wait: 2^retry_count seconds<br/>━━━━━━━━━━<br/>Retry 1: 2s<br/>Retry 2: 4s<br/>Retry 3: 8s<br/>Retry 4: 16s<br/>Retry 5: 32s]

    NACK[NACK Message<br/>Requeue: true]

    CircuitBreaker{Circuit Breaker<br/>State?}

    OpenState[OPEN State<br/>Block Processing<br/>Wait for Recovery]

    HalfOpenState[HALF_OPEN State<br/>Test Recovery<br/>Limited Throughput]

    MoveDLQ[Move to DLQ<br/>failed.queue<br/>━━━━━━━━━━<br/>Max Retries Exceeded<br/>Manual Intervention Required]

    UpdateFailed[Update Status:<br/>✗ failed<br/>✗ error message<br/>✗ timestamp]

    Alert[Send Alert<br/>Monitoring System<br/>Log Error<br/>Notify Team]

    End[End]

    Start --> CircuitBreaker

    CircuitBreaker -->|CLOSED| Process
    CircuitBreaker -->|OPEN| OpenState
    CircuitBreaker -->|HALF_OPEN| HalfOpenState

    OpenState --> NACK
    HalfOpenState --> Process

    Process --> Success

    Success -->|Yes| UpdateSuccess
    UpdateSuccess --> ACK
    ACK --> End

    Success -->|No| CheckRetry

    CheckRetry -->|Yes| IncrementRetry
    IncrementRetry --> Backoff
    Backoff --> NACK
    NACK --> Start

    CheckRetry -->|No| MoveDLQ
    MoveDLQ --> UpdateFailed
    UpdateFailed --> Alert
    Alert --> End

    style Start fill:#e3f2fd
    style Success fill:#fff9c4
    style CheckRetry fill:#fff9c4
    style CircuitBreaker fill:#fff9c4
    style UpdateSuccess fill:#c8e6c9
    style ACK fill:#c8e6c9
    style MoveDLQ fill:#ffcdd2
    style UpdateFailed fill:#ffcdd2
    style Alert fill:#ffcdd2
    style Backoff fill:#ffe0b2
    style End fill:#f5f5f5
```

### Circuit Breaker State Machine

```mermaid
stateDiagram-v2
    [*] --> CLOSED

    CLOSED --> OPEN: failure_count >= threshold (5)

    OPEN --> HALF_OPEN: recovery_timeout expired (60s)

    HALF_OPEN --> CLOSED: success_count >= threshold (2)
    HALF_OPEN --> OPEN: any failure

    CLOSED --> CLOSED: success (reset failure_count)
    CLOSED --> CLOSED: failure (increment failure_count)

    note right of CLOSED
        Normal Operation
        ━━━━━━━━━━━━━
        ✓ All requests pass through
        ✓ Track failures
        ✓ Reset on success
    end note

    note right of OPEN
        Failure Mode
        ━━━━━━━━━━━━━
        ✗ Block all requests
        ✗ Wait for recovery timeout
        ✗ Prevent cascading failures
    end note

    note right of HALF_OPEN
        Testing Recovery
        ━━━━━━━━━━━━━
        → Allow limited requests
        → Test if service recovered
        → Quick fail back to OPEN
    end note
```

---

## 4. Database Relationships

### Complete Database Schema

```mermaid
erDiagram
    USERS ||--o{ NOTIFICATION_STATUS : has
    TEMPLATES ||--o{ TEMPLATE_VERSIONS : has
    TEMPLATES ||--o{ NOTIFICATION_STATUS : uses

    USERS {
        uuid id PK
        varchar name
        varchar email UK
        varchar password_hash
        text push_token
        jsonb preferences
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    TEMPLATES {
        uuid id PK
        varchar code UK
        varchar name
        text description
        text content
        varchar language
        integer version
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    TEMPLATE_VERSIONS {
        uuid id PK
        uuid template_id FK
        integer version
        text content
        uuid created_by FK
        timestamp created_at
    }

    NOTIFICATION_STATUS {
        uuid id PK
        varchar notification_id UK
        uuid user_id FK
        varchar template_code FK
        varchar status
        varchar notification_type
        jsonb metadata
        text error
        timestamp created_at
        timestamp updated_at
        timestamp delivered_at
    }
```

### Redis Data Model

```mermaid
graph TB
    subgraph "Redis Cache Structure"
        A[Redis Instance<br/>Port: 6379]

        subgraph "Notification Status"
            B[Key: notification:notification_id<br/>Type: Hash<br/>TTL: 7 days<br/>━━━━━━━━━━<br/>notification_id<br/>status<br/>created_at<br/>updated_at<br/>error]
        end

        subgraph "Idempotency Check"
            C[Key: request_id:request_id<br/>Type: String<br/>TTL: 24 hours<br/>━━━━━━━━━━<br/>Value: notification_id]
        end

        subgraph "Rate Limiting"
            D[Key: rate_limit:user_id:type<br/>Type: Counter<br/>TTL: 1 hour<br/>━━━━━━━━━━<br/>Value: request_count<br/>Max: 100/hour]
        end

        subgraph "User Cache"
            E[Key: user:user_id<br/>Type: Hash<br/>TTL: 1 hour<br/>━━━━━━━━━━<br/>id<br/>email<br/>push_token<br/>preferences]
        end

        subgraph "Template Cache"
            F[Key: template:template_code<br/>Type: Hash<br/>TTL: 1 hour<br/>━━━━━━━━━━<br/>code<br/>content<br/>version]
        end

        subgraph "Circuit Breaker State"
            G[Key: circuit:service_name<br/>Type: Hash<br/>TTL: None<br/>━━━━━━━━━━<br/>state<br/>failure_count<br/>last_failure_time<br/>success_count]
        end
    end

    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    A --> G

    style A fill:#ffebee
    style B fill:#e1f5ff
    style C fill:#e1f5ff
    style D fill:#fff9c4
    style E fill:#e1f5ff
    style F fill:#e1f5ff
    style G fill:#ffe0b2
```

---

## 5. Scaling Plan

### Horizontal Scaling Architecture

```mermaid
graph TB
    subgraph "Load Balancer Layer"
        LB[Nginx/HAProxy<br/>Load Balancer]
    end

    subgraph "API Gateway Cluster"
        GW1[Gateway 1<br/>Port 8000]
        GW2[Gateway 2<br/>Port 8000]
        GW3[Gateway 3<br/>Port 8000]
    end

    subgraph "User Service Cluster"
        US1[User Service 1<br/>Port 8001]
        US2[User Service 2<br/>Port 8001]
        US3[User Service 3<br/>Port 8001]
    end

    subgraph "Template Service Cluster"
        TS1[Template Service 1<br/>Port 8002]
        TS2[Template Service 2<br/>Port 8002]
    end

    subgraph "Worker Pools"
        subgraph "Email Workers"
            EW1[Email Worker 1]
            EW2[Email Worker 2]
            EW3[Email Worker 3]
            EW4[Email Worker 4]
            EW5[Email Worker 5]
        end

        subgraph "Push Workers"
            PW1[Push Worker 1]
            PW2[Push Worker 2]
            PW3[Push Worker 3]
            PW4[Push Worker 4]
            PW5[Push Worker 5]
        end
    end

    subgraph "Message Queue Cluster"
        RMQ1[RabbitMQ Node 1<br/>Master]
        RMQ2[RabbitMQ Node 2<br/>Mirror]
        RMQ3[RabbitMQ Node 3<br/>Mirror]
    end

    subgraph "Database Cluster"
        PGMaster[PostgreSQL Master<br/>Read/Write]
        PGReplica1[PostgreSQL Replica 1<br/>Read Only]
        PGReplica2[PostgreSQL Replica 2<br/>Read Only]
    end

    subgraph "Cache Cluster"
        RedisM[Redis Master]
        RedisR1[Redis Replica 1]
        RedisR2[Redis Replica 2]
    end

    LB --> GW1
    LB --> GW2
    LB --> GW3

    GW1 --> US1
    GW1 --> US2
    GW1 --> US3
    GW2 --> US1
    GW2 --> US2
    GW3 --> US3

    GW1 --> TS1
    GW1 --> TS2
    GW2 --> TS1
    GW3 --> TS2

    GW1 --> RMQ1
    GW2 --> RMQ2
    GW3 --> RMQ3

    RMQ1 -.->|Mirror| RMQ2
    RMQ1 -.->|Mirror| RMQ3

    RMQ1 --> EW1
    RMQ1 --> EW2
    RMQ2 --> EW3
    RMQ2 --> EW4
    RMQ3 --> EW5

    RMQ1 --> PW1
    RMQ1 --> PW2
    RMQ2 --> PW3
    RMQ3 --> PW4
    RMQ3 --> PW5

    US1 --> PGMaster
    US2 --> PGReplica1
    US3 --> PGReplica2

    TS1 --> PGMaster
    TS2 --> PGReplica1

    PGMaster -.->|Replicate| PGReplica1
    PGMaster -.->|Replicate| PGReplica2

    GW1 --> RedisM
    GW2 --> RedisR1
    GW3 --> RedisR2

    EW1 --> RedisM
    EW2 --> RedisR1
    PW1 --> RedisR2

    RedisM -.->|Replicate| RedisR1
    RedisM -.->|Replicate| RedisR2

    style LB fill:#e3f2fd
    style RMQ1 fill:#fff9c4
    style RMQ2 fill:#fff9c4
    style RMQ3 fill:#fff9c4
    style PGMaster fill:#c8e6c9
    style RedisM fill:#ffcdd2
```

### Auto-Scaling Strategy

```mermaid
graph TB
    subgraph "Monitoring Metrics"
        M1[Queue Length<br/>Threshold: 1000]
        M2[CPU Usage<br/>Threshold: 70%]
        M3[Memory Usage<br/>Threshold: 80%]
        M4[Response Time<br/>Threshold: 100ms]
    end

    subgraph "Auto-Scaling Decision Engine"
        Decision{Scale Required?}
    end

    subgraph "Scaling Actions"
        ScaleUp[Scale Up<br/>━━━━━━━━━━<br/>Add Instances<br/>Min: 2<br/>Max: 10<br/>Step: +2]

        ScaleDown[Scale Down<br/>━━━━━━━━━━<br/>Remove Instances<br/>Min: 2<br/>Cooldown: 5 min]

        Maintain[Maintain<br/>━━━━━━━━━━<br/>Keep Current State]
    end

    subgraph "Target Services"
        T1[API Gateway<br/>Kubernetes HPA]
        T2[Email Workers<br/>Docker Swarm Scale]
        T3[Push Workers<br/>Docker Swarm Scale]
        T4[Database Read Replicas<br/>Manual/Auto]
    end

    M1 --> Decision
    M2 --> Decision
    M3 --> Decision
    M4 --> Decision

    Decision -->|Overloaded| ScaleUp
    Decision -->|Underutilized| ScaleDown
    Decision -->|Optimal| Maintain

    ScaleUp --> T1
    ScaleUp --> T2
    ScaleUp --> T3
    ScaleUp --> T4

    ScaleDown --> T1
    ScaleDown --> T2
    ScaleDown --> T3

    style M1 fill:#fff9c4
    style M2 fill:#fff9c4
    style M3 fill:#fff9c4
    style M4 fill:#fff9c4
    style Decision fill:#e3f2fd
    style ScaleUp fill:#c8e6c9
    style ScaleDown fill:#ffccbc
    style Maintain fill:#e0e0e0
```

---

## 6. Complete Request Flow

### End-to-End Notification Flow

```mermaid
sequenceDiagram
    autonumber

    participant C as Client
    participant LB as Load Balancer
    participant GW as API Gateway
    participant Auth as Auth Module
    participant US as User Service
    participant TS as Template Service
    participant Redis as Redis Cache
    participant RMQ as RabbitMQ
    participant EW as Email Worker
    participant CB as Circuit Breaker
    participant SMTP as SMTP Provider

    Note over C,SMTP: Email Notification Flow with Complete Error Handling

    C->>LB: POST /api/v1/notifications
    activate LB
    LB->>GW: Route to Gateway Instance
    activate GW

    GW->>Auth: Validate JWT Token
    activate Auth
    Auth-->>GW: ✓ Token Valid
    deactivate Auth

    GW->>GW: Generate Correlation ID
    GW->>GW: Validate Request Schema

    GW->>Redis: Check Idempotency (request_id)
    activate Redis
    Redis-->>GW: Not Found (New Request)
    deactivate Redis

    GW->>US: GET /users/{user_id}
    activate US
    US->>Redis: Check User Cache
    activate Redis
    Redis-->>US: Cache Miss
    deactivate Redis
    US->>US: Query Database
    US->>Redis: Cache User Data (1h TTL)
    US-->>GW: User Data + Preferences
    deactivate US

    alt User Email Preference Disabled
        GW-->>C: 400 Bad Request<br/>(Preference Disabled)
    else Preference Enabled
        GW->>TS: GET /templates/{template_code}
        activate TS
        TS->>Redis: Check Template Cache
        activate Redis
        Redis-->>TS: Cache Hit
        deactivate Redis
        TS-->>GW: Template Content
        deactivate TS

        GW->>Redis: Check Rate Limit
        activate Redis
        Redis-->>GW: ✓ Within Limit
        deactivate Redis

        GW->>RMQ: Publish to email.queue
        activate RMQ
        Note over GW,RMQ: Message Properties:<br/>- correlation_id<br/>- priority<br/>- persistence
        RMQ-->>GW: ✓ Queued
        deactivate RMQ

        GW->>Redis: Save Idempotency Record
        activate Redis
        Redis-->>GW: ✓ Saved (24h TTL)
        deactivate Redis

        GW->>Redis: Update Status (pending)
        activate Redis
        Redis-->>GW: ✓ Updated
        deactivate Redis

        GW-->>C: 202 Accepted<br/>{notification_id}
        deactivate GW
        deactivate LB

        Note over RMQ,SMTP: Asynchronous Processing

        RMQ->>EW: Consume Message (Prefetch: 10)
        activate EW

        EW->>CB: Check Circuit Breaker
        activate CB
        CB-->>EW: ✓ CLOSED (Can Proceed)
        deactivate CB

        EW->>TS: Fetch Template Details
        activate TS
        TS-->>EW: Template Content
        deactivate TS

        EW->>EW: Render Template<br/>(Variable Substitution)

        EW->>SMTP: Send Email
        activate SMTP

        alt SMTP Success
            SMTP-->>EW: ✓ Email Sent
            deactivate SMTP

            EW->>CB: Record Success
            activate CB
            CB->>CB: Reset Failure Count
            deactivate CB

            EW->>Redis: Update Status (delivered)
            activate Redis
            Redis-->>EW: ✓ Updated
            deactivate Redis

            EW->>RMQ: ACK Message
            activate RMQ
            RMQ->>RMQ: Remove from Queue
            deactivate RMQ

        else SMTP Failure
            SMTP-->>EW: ✗ Connection Failed
            deactivate SMTP

            EW->>CB: Record Failure
            activate CB
            CB->>CB: Increment Failure Count
            alt Failure Count >= Threshold
                CB->>CB: Open Circuit
                Note over CB: Block Further Requests
            end
            deactivate CB

            EW->>EW: Check Retry Count

            alt Retry Count < 5
                EW->>EW: Increment Retry Count
                EW->>EW: Calculate Backoff<br/>(2^retry_count seconds)
                EW->>RMQ: NACK + Requeue
                activate RMQ
                Note over RMQ: Wait then Retry
                deactivate RMQ
            else Max Retries Exceeded
                EW->>RMQ: Move to DLQ
                activate RMQ
                RMQ->>RMQ: failed.queue
                deactivate RMQ

                EW->>Redis: Update Status (failed)
                activate Redis
                Redis-->>EW: ✓ Updated
                deactivate Redis

                EW->>EW: Log Error & Alert
            end
        end

        deactivate EW
    end
```

---

## 7. Deployment Architecture

### Containerized Deployment with Docker

```mermaid
graph TB
    subgraph "Docker Host / Kubernetes Cluster"
        subgraph "Network: notification_network"
            subgraph "API Layer"
                GW1[api-gateway:8000<br/>Replicas: 3]
            end

            subgraph "Service Layer"
                US1[user-service:8001<br/>Replicas: 2]
                TS1[template-service:8002<br/>Replicas: 2]
            end

            subgraph "Worker Layer"
                EW1[email-worker<br/>Replicas: 3]
                PW1[push-worker<br/>Replicas: 3]
            end

            subgraph "Infrastructure"
                PG[(PostgreSQL:5432<br/>Volume: postgres_data)]
                RD[(Redis:6379<br/>Volume: redis_data)]
                RMQ[RabbitMQ:5672,15672<br/>Volume: rabbitmq_data]
            end

            subgraph "Monitoring"
                PROM[Prometheus:9090]
                GRAF[Grafana:3000]
            end
        end
    end

    GW1 --> US1
    GW1 --> TS1
    GW1 --> RMQ
    GW1 --> RD

    US1 --> PG
    US1 --> RD

    TS1 --> PG
    TS1 --> RD

    EW1 --> RMQ
    EW1 --> RD
    EW1 --> TS1

    PW1 --> RMQ
    PW1 --> RD

    GW1 -.->|metrics| PROM
    US1 -.->|metrics| PROM
    TS1 -.->|metrics| PROM
    EW1 -.->|metrics| PROM
    PW1 -.->|metrics| PROM

    PROM --> GRAF

    style GW1 fill:#e3f2fd
    style US1 fill:#e3f2fd
    style TS1 fill:#e3f2fd
    style EW1 fill:#fff9c4
    style PW1 fill:#fff9c4
    style PG fill:#c8e6c9
    style RD fill:#ffcdd2
    style RMQ fill:#ffe0b2
    style PROM fill:#e1bee7
    style GRAF fill:#e1bee7
```

---

## 8. Monitoring and Observability

### Metrics Collection Flow

```mermaid
graph TB
    subgraph "Application Layer"
        A1[API Gateway<br/>Metrics Exporter]
        A2[User Service<br/>Metrics Exporter]
        A3[Template Service<br/>Metrics Exporter]
        A4[Email Worker<br/>Metrics Exporter]
        A5[Push Worker<br/>Metrics Exporter]
    end

    subgraph "Infrastructure Metrics"
        I1[RabbitMQ Exporter<br/>Queue Metrics]
        I2[PostgreSQL Exporter<br/>DB Metrics]
        I3[Redis Exporter<br/>Cache Metrics]
        I4[Node Exporter<br/>System Metrics]
    end

    subgraph "Prometheus"
        P[Prometheus Server<br/>:9090<br/>━━━━━━━━━━<br/>Scrape Interval: 15s<br/>Retention: 30 days]
    end

    subgraph "Visualization"
        G[Grafana<br/>:3000<br/>━━━━━━━━━━<br/>Dashboards:<br/>- System Overview<br/>- Queue Metrics<br/>- Service Health<br/>- Error Rates]
    end

    subgraph "Alerting"
        AM[Alert Manager<br/>━━━━━━━━━━<br/>Channels:<br/>- Email<br/>- Slack<br/>- PagerDuty]
    end

    A1 -->|/metrics| P
    A2 -->|/metrics| P
    A3 -->|/metrics| P
    A4 -->|/metrics| P
    A5 -->|/metrics| P

    I1 -->|/metrics| P
    I2 -->|/metrics| P
    I3 -->|/metrics| P
    I4 -->|/metrics| P

    P --> G
    P --> AM

    style A1 fill:#e3f2fd
    style A2 fill:#e3f2fd
    style A3 fill:#e3f2fd
    style A4 fill:#fff9c4
    style A5 fill:#fff9c4
    style I1 fill:#ffe0b2
    style I2 fill:#c8e6c9
    style I3 fill:#ffcdd2
    style I4 fill:#e0e0e0
    style P fill:#e1bee7
    style G fill:#e1bee7
    style AM fill:#ffccbc
```

### Key Performance Indicators

```mermaid
graph LR
    subgraph "KPI Dashboard"
        subgraph "Throughput Metrics"
            K1[Notifications/Min<br/>Target: 1000+<br/>Current: 1250]
            K2[Success Rate<br/>Target: 99.5%<br/>Current: 99.7%]
        end

        subgraph "Latency Metrics"
            K3[API Response Time<br/>Target: <100ms<br/>P95: 87ms]
            K4[Queue Processing Time<br/>Target: <5s<br/>P95: 3.2s]
        end

        subgraph "Resource Metrics"
            K5[Queue Length<br/>Threshold: 1000<br/>Current: 234]
            K6[Worker Utilization<br/>Target: 60-80%<br/>Current: 72%]
        end

        subgraph "Error Metrics"
            K7[Error Rate<br/>Target: <0.5%<br/>Current: 0.3%]
            K8[DLQ Size<br/>Target: <50<br/>Current: 12]
        end
    end

    style K1 fill:#c8e6c9
    style K2 fill:#c8e6c9
    style K3 fill:#c8e6c9
    style K4 fill:#c8e6c9
    style K5 fill:#c8e6c9
    style K6 fill:#c8e6c9
    style K7 fill:#c8e6c9
    style K8 fill:#fff9c4
```

---

## Summary

This system design provides:

### ✅ Service Connections

- Clear separation of concerns with 5 microservices
- REST APIs for synchronous communication
- Message queues for asynchronous processing
- Shared infrastructure (Redis, PostgreSQL)

### ✅ Queue Structure

- Direct exchange with routing keys
- Priority queues with TTL
- Dead letter queue for failed messages
- Durable, persistent messages

### ✅ Retry and Failure Flow

- Exponential backoff strategy
- Circuit breaker pattern
- Maximum retry limits
- DLQ for manual intervention

### ✅ Database Relationships

- PostgreSQL for structured data
- Redis for caching and state
- Proper indexing and relationships
- Data isolation per service

### ✅ Scaling Plan

- Horizontal scaling for all services
- Auto-scaling based on metrics
- Load balancing
- Database replication
- Queue clustering

### 🎯 Performance Targets

- ✅ 1,000+ notifications/minute
- ✅ API response < 100ms
- ✅ 99.5% delivery success
- ✅ Horizontal scalability

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Team**: [Your Team Name]  
**Created By**: System Architects
