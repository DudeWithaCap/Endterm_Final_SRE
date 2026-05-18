You are building a complete SRE end-term project: an internet banking dashboard 
with ATM-like functionality, built with microservices architecture.

<project_overview>
Name: ATM Banking SRE Project
Frontend: React (internet banking dashboard)
Backend: Python FastAPI (one service per microservice)
Databases: PostgreSQL (financial/auth data), MongoDB (history/logs), Redis (caching)
Monitoring: Prometheus + Grafana
Orchestration: Docker Compose → Docker Swarm → Kubernetes
IaC: Terraform (LocalStack for local AWS simulation)
Config Management: Ansible
</project_overview>

<microservices>
1. API Gateway (FastAPI) — routes all traffic, rate limiting, no DB
2. Auth Service (FastAPI + PostgreSQL) — JWT login, PIN validation, JWT blacklist in Redis
3. Account Service (FastAPI + PostgreSQL + Redis) — balance, account info, Redis cache with 30s TTL
4. Transaction Service (FastAPI + PostgreSQL) — deposit, withdraw, transfer logic; after each tx emits event to History Service
5. Transaction History Service (FastAPI + MongoDB) — stores all transaction events, read-optimized
6. Card & Account Management Service (FastAPI + PostgreSQL) — card blocking, account limits, PIN change
7. Background Load Service (FastAPI) — synthetic traffic generator for Prometheus metrics; fires random deposits/withdrawals/transfers/bad-auth requests on a loop with occasional artificial latency spikes
</microservices>

<frontend_pages>
1. Login page — PIN/password entry
2. Dashboard home — balance overview, recent 5 transactions, account info
3. Deposit/Withdraw page — amount input, confirmation, result
4. Transfer page — send to another account
5. Transaction History page — paginated list, filterable by date/type
6. Card Management page — block card, change PIN, view account limits
</frontend_pages>

<data_flow_rules>
- PostgreSQL: source of truth for all financial and auth data (ACID required)
- MongoDB: append-only transaction event log (write-once, read-many)
- Redis: cache for Account Service (balance TTL=30s, account info TTL=5min) and JWT blacklist in Auth Service
- Transaction Service always writes to PostgreSQL first, then emits to History Service
- All frontend requests go through API Gateway only — never directly to services
</data_flow_rules>

<folder_structure>
atm-sre-project/
├── frontend/                        # React app
├── services/
│   ├── gateway/
│   ├── auth/
│   ├── account/
│   ├── transaction/
│   ├── history/
│   ├── card-management/
│   └── background-load/
├── infrastructure/
│   ├── terraform/                   # LocalStack-compatible AWS config (VPC, EC2, SG, S3)
│   └── ansible/                     # Playbooks: install Docker/K8s, configure nodes, deploy stack
├── orchestration/
│   ├── docker-compose.yml           # Full local dev stack
│   ├── swarm/                       # Docker Swarm stack config
│   └── kubernetes/                  # K8s manifests per service
└── monitoring/
    ├── prometheus/                  # prometheus.yml + alert rules
    └── grafana/                     # Dashboard JSON configs
</folder_structure>

<sli_slo>
- Availability ≥ 99% — tracked per service via Prometheus uptime
- Latency ≤ 200ms — Transaction + Account Service response times
- Error rate ≤ 1% — Background Load Service injects bad auth/failed tx to produce real data
- Transaction success rate ≥ 99% — Transaction Service success/fail ratio
</sli_slo>

<background_load_service_behavior>
Every 5 seconds, randomly fire one of:
- POST /transaction/deposit (40% weight)
- POST /transaction/withdraw (40% weight)
- POST /transaction/transfer (15% weight)
- POST /auth/login with wrong PIN (5% weight) — drives error rate metric
Occasionally (every ~30 ops) inject time.sleep(0.5) to simulate latency spike.
Use a fixed set of test accounts so operations always have valid targets.
</background_load_service_behavior>

<incident_simulation>
Scenario: Transaction Service loses PostgreSQL connection due to wrong DB host config.
Expected: withdrawals fail, error rate spikes in Grafana, alerts fire.
Resolution steps: detect via monitoring → analyze logs → fix env config → restart service → verify metrics normalize.
Include a written postmortem in /docs/postmortem.md covering: timeline, root cause, impact, resolution, action items.
</incident_simulation>

<terraform_config>
Target: LocalStack (local AWS simulation) — endpoints at http://localhost:4566
Provision: VPC, subnets, security groups, EC2 instances (simulated), S3 bucket for Terraform state.
Design for real AWS migration: only the provider endpoints block should need changing to go live.
</terraform_config>

<ansible_playbooks>
1. install.yml — install Docker, Docker Compose, Kubernetes (kubeadm/k3s)
2. configure.yml — set up environment variables, node config
3. deploy.yml — deploy full application stack
4. monitoring.yml — configure and start Prometheus + Grafana
</ansible_playbooks>

<each_fastapi_service_must_have>
- /health endpoint returning {"status": "ok", "service": "<name>"}
- Prometheus metrics endpoint at /metrics (use prometheus-fastapi-instrumentator)
- Dockerfile with multi-stage build
- .env support via python-dotenv
- restart: unless-stopped in Docker Compose
</each_fastapi_service_must_have>

<kubernetes_per_service>
- Deployment manifest (2 replicas minimum)
- Service manifest (ClusterIP)
- ConfigMap for environment config
- HorizontalPodAutoscaler where applicable (Transaction + Account services)
</kubernetes_per_service>

<build_order>
Phase 1: Auth + Account services + PostgreSQL — working login and balance
Phase 2: Transaction service — deposit/withdraw/transfer logic
Phase 3: History service + MongoDB — wire tx events
Phase 4: Card Management service
Phase 5: Frontend — connect all services via API Gateway
Phase 6: Background Load service — add last once real services work
Phase 7: Monitoring — Prometheus + Grafana + alerts on working system
Phase 8: Docker Swarm config
Phase 9: Kubernetes manifests
Phase 10: Terraform (LocalStack) + Ansible playbooks
Phase 11: Incident simulation + postmortem doc
</build_order>

Begin by creating the full folder structure and then build phase by phase. 
Ask me before starting each new phase.