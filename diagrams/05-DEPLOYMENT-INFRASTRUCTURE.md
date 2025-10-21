# PakLog Deployment and Infrastructure Diagrams

## Table of Contents
1. [Kubernetes Deployment Architecture](#kubernetes-deployment-architecture)
2. [Network Architecture](#network-architecture)
3. [Database Infrastructure](#database-infrastructure)
4. [Message Queue Infrastructure](#message-queue-infrastructure)
5. [Monitoring and Observability Stack](#monitoring-and-observability-stack)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Disaster Recovery Architecture](#disaster-recovery-architecture)
8. [Security Architecture](#security-architecture)
9. [Load Balancing and Scaling](#load-balancing-and-scaling)
10. [Service Mesh Architecture](#service-mesh-architecture)

---

## Kubernetes Deployment Architecture

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Ingress Layer"
            ING[NGINX Ingress Controller]
            CERT[Cert Manager]
        end

        subgraph "API Gateway"
            GW1[Spring Cloud Gateway Pod 1]
            GW2[Spring Cloud Gateway Pod 2]
            GW3[Spring Cloud Gateway Pod 3]
        end

        subgraph "WMS Namespace"
            subgraph "Wave Planning"
                WP1[Wave Planning Pod 1]
                WP2[Wave Planning Pod 2]
                WP3[Wave Planning Pod 3]
            end

            subgraph "Location Master"
                LM1[Location Master Pod 1]
                LM2[Location Master Pod 2]
            end

            subgraph "Workload Planning"
                WL1[Workload Planning Pod 1]
                WL2[Workload Planning Pod 2]
            end
        end

        subgraph "WES Namespace"
            subgraph "Task Execution"
                TE1[Task Execution Pod 1]
                TE2[Task Execution Pod 2]
                TE3[Task Execution Pod 3]
                TE4[Task Execution Pod 4]
                TE5[Task Execution Pod 5]
            end

            subgraph "Pick Execution"
                PE1[Pick Execution Pod 1]
                PE2[Pick Execution Pod 2]
                PE3[Pick Execution Pod 3]
                PE4[Pick Execution Pod 4]
                PE5[Pick Execution Pod 5]
            end

            subgraph "Pack Ship"
                PS1[Pack Ship Pod 1]
                PS2[Pack Ship Pod 2]
                PS3[Pack Ship Pod 3]
            end

            subgraph "Physical Tracking"
                PT1[Physical Tracking Pod 1]
                PT2[Physical Tracking Pod 2]
                PT3[Physical Tracking Pod 3]
            end
        end

        subgraph "Data Layer"
            subgraph "Kafka Namespace"
                KF1[Kafka Broker 1]
                KF2[Kafka Broker 2]
                KF3[Kafka Broker 3]
                ZK1[Zookeeper 1]
                ZK2[Zookeeper 2]
                ZK3[Zookeeper 3]
            end
        end

        subgraph "Monitoring Namespace"
            PROM[Prometheus]
            GRAF[Grafana]
            LOKI[Loki]
            TEMPO[Tempo]
            ALERT[AlertManager]
        end
    end

    subgraph "External Data Stores"
        subgraph "MongoDB Cluster"
            MONGO1[MongoDB Primary]
            MONGO2[MongoDB Secondary]
            MONGO3[MongoDB Secondary]
        end

        subgraph "PostgreSQL"
            PG1[PostgreSQL Primary]
            PG2[PostgreSQL Standby]
        end

        subgraph "Redis Cluster"
            REDIS1[Redis Master]
            REDIS2[Redis Slave]
            REDIS3[Redis Slave]
        end
    end

    ING --> GW1
    ING --> GW2
    ING --> GW3

    GW1 --> WP1
    GW2 --> LM1
    GW3 --> TE1
```

---

## Network Architecture

```mermaid
graph TB
    subgraph "Internet"
        USERS[Users]
        MOBILE[Mobile Devices]
        EXTERNAL[External Systems]
    end

    subgraph "CDN Layer"
        CF[CloudFlare/CDN]
    end

    subgraph "Load Balancer Layer"
        subgraph "Application Load Balancers"
            ALB1[ALB - Web Traffic]
            ALB2[ALB - API Traffic]
            ALB3[ALB - Mobile Traffic]
        end

        subgraph "Network Load Balancers"
            NLB1[NLB - Kafka]
            NLB2[NLB - Database]
        end
    end

    subgraph "VPC - 10.0.0.0/16"
        subgraph "Public Subnets"
            subgraph "AZ-1 - 10.0.1.0/24"
                NAT1[NAT Gateway 1]
                BASTION1[Bastion Host 1]
            end

            subgraph "AZ-2 - 10.0.2.0/24"
                NAT2[NAT Gateway 2]
                BASTION2[Bastion Host 2]
            end
        end

        subgraph "Private Subnets - Application"
            subgraph "AZ-1 - 10.0.10.0/24"
                APP1[App Servers AZ-1]
            end

            subgraph "AZ-2 - 10.0.11.0/24"
                APP2[App Servers AZ-2]
            end

            subgraph "AZ-3 - 10.0.12.0/24"
                APP3[App Servers AZ-3]
            end
        end

        subgraph "Private Subnets - Data"
            subgraph "AZ-1 - 10.0.20.0/24"
                DATA1[Databases AZ-1]
                CACHE1[Cache AZ-1]
            end

            subgraph "AZ-2 - 10.0.21.0/24"
                DATA2[Databases AZ-2]
                CACHE2[Cache AZ-2]
            end

            subgraph "AZ-3 - 10.0.22.0/24"
                DATA3[Databases AZ-3]
                CACHE3[Cache AZ-3]
            end
        end

        subgraph "Security Groups"
            SG_WEB[SG: Web Tier - 443, 80]
            SG_APP[SG: App Tier - 8080-8090]
            SG_DATA[SG: Data Tier - 27017, 5432, 6379]
            SG_KAFKA[SG: Kafka - 9092]
        end
    end

    USERS --> CF
    MOBILE --> CF
    EXTERNAL --> ALB2

    CF --> ALB1
    ALB1 --> APP1
    ALB1 --> APP2
    ALB1 --> APP3

    APP1 --> DATA1
    APP2 --> DATA2
    APP3 --> DATA3
```

---

## Database Infrastructure

```mermaid
graph TB
    subgraph "MongoDB Replica Set"
        subgraph "Primary Region"
            MONGO_P[MongoDB Primary<br/>Writes]
            MONGO_S1[MongoDB Secondary<br/>Reads]
            MONGO_S2[MongoDB Secondary<br/>Reads]
            MONGO_ARB[MongoDB Arbiter]
        end

        subgraph "DR Region"
            MONGO_DR[MongoDB Secondary<br/>DR Standby]
        end
    end

    subgraph "PostgreSQL Cluster"
        subgraph "Primary"
            PG_MASTER[PostgreSQL Primary<br/>Read/Write]
            PGBOUNCER1[PgBouncer<br/>Connection Pooling]
        end

        subgraph "Replicas"
            PG_REPLICA1[PostgreSQL Replica 1<br/>Read Only]
            PG_REPLICA2[PostgreSQL Replica 2<br/>Read Only]
            PGBOUNCER2[PgBouncer<br/>Connection Pooling]
        end

        subgraph "Backup"
            PG_BACKUP[Backup Server<br/>WAL Archive]
        end
    end

    subgraph "Redis Cluster"
        subgraph "Master Nodes"
            REDIS_M1[Redis Master 1<br/>Slots 0-5460]
            REDIS_M2[Redis Master 2<br/>Slots 5461-10922]
            REDIS_M3[Redis Master 3<br/>Slots 10923-16383]
        end

        subgraph "Slave Nodes"
            REDIS_S1[Redis Slave 1]
            REDIS_S2[Redis Slave 2]
            REDIS_S3[Redis Slave 3]
        end

        REDIS_SENTINEL[Redis Sentinel<br/>Failover Management]
    end

    subgraph "Application Services"
        WMS[WMS Services]
        WES[WES Services]
        ANALYTICS[Analytics Services]
    end

    WMS --> MONGO_P
    WMS --> MONGO_S1
    WES --> MONGO_S2

    WMS --> PGBOUNCER1
    WES --> PGBOUNCER2

    WMS --> REDIS_M1
    WES --> REDIS_M2
    ANALYTICS --> REDIS_M3

    MONGO_P -.->|Replication| MONGO_S1
    MONGO_P -.->|Replication| MONGO_S2
    MONGO_P -.->|Replication| MONGO_DR

    PG_MASTER -.->|Streaming Replication| PG_REPLICA1
    PG_MASTER -.->|Streaming Replication| PG_REPLICA2
    PG_MASTER -.->|WAL Archive| PG_BACKUP

    REDIS_M1 -.->|Replication| REDIS_S1
    REDIS_M2 -.->|Replication| REDIS_S2
    REDIS_M3 -.->|Replication| REDIS_S3
```

---

## Message Queue Infrastructure

```mermaid
graph TB
    subgraph "Kafka Cluster"
        subgraph "Brokers"
            BROKER1[Broker 1<br/>Leader Partitions]
            BROKER2[Broker 2<br/>Leader Partitions]
            BROKER3[Broker 3<br/>Leader Partitions]
        end

        subgraph "Zookeeper Ensemble"
            ZK1[Zookeeper 1<br/>Leader]
            ZK2[Zookeeper 2<br/>Follower]
            ZK3[Zookeeper 3<br/>Follower]
        end

        subgraph "Topics"
            subgraph "WMS Topics"
                T1[wave-events<br/>Partitions: 6<br/>Replication: 3]
                T2[order-events<br/>Partitions: 6<br/>Replication: 3]
                T3[inventory-events<br/>Partitions: 12<br/>Replication: 3]
            end

            subgraph "WES Topics"
                T4[task-events<br/>Partitions: 12<br/>Replication: 3]
                T5[pick-events<br/>Partitions: 12<br/>Replication: 3]
                T6[pack-events<br/>Partitions: 6<br/>Replication: 3]
            end

            subgraph "Integration Topics"
                T7[external-events<br/>Partitions: 3<br/>Replication: 3]
                T8[error-events<br/>Partitions: 3<br/>Replication: 3]
            end
        end
    end

    subgraph "Producers"
        P1[Wave Planning Service]
        P2[Task Execution Service]
        P3[Pick Execution Service]
        P4[Integration Service]
    end

    subgraph "Consumers"
        subgraph "Consumer Group 1"
            C1A[Task Service Instance 1]
            C1B[Task Service Instance 2]
            C1C[Task Service Instance 3]
        end

        subgraph "Consumer Group 2"
            C2A[Pick Service Instance 1]
            C2B[Pick Service Instance 2]
        end
    end

    subgraph "Kafka Connect"
        KC1[MongoDB Sink Connector]
        KC2[Elasticsearch Sink Connector]
        KC3[S3 Sink Connector]
    end

    subgraph "Schema Registry"
        SR[Confluent Schema Registry<br/>Avro Schemas]
    end

    P1 --> T1
    P1 --> T2
    P2 --> T4
    P3 --> T5
    P4 --> T7

    T1 --> C1A
    T1 --> C1B
    T4 --> C2A
    T4 --> C2B

    T1 --> KC1
    T4 --> KC2
    T7 --> KC3

    BROKER1 -.->|Metadata| ZK1
    BROKER2 -.->|Metadata| ZK1
    BROKER3 -.->|Metadata| ZK1

    P1 -.->|Schema| SR
    C1A -.->|Schema| SR
```

---

## Monitoring and Observability Stack

```mermaid
graph TB
    subgraph "Application Layer"
        APP1[Wave Planning<br/>Micrometer]
        APP2[Task Execution<br/>Micrometer]
        APP3[Pick Execution<br/>Micrometer]
        APP4[Pack Ship<br/>Micrometer]
    end

    subgraph "Collection Layer"
        subgraph "Metrics"
            PROM[Prometheus<br/>Metrics Storage]
            PUSHGW[Prometheus<br/>Push Gateway]
        end

        subgraph "Logs"
            FLUENTD[Fluentd<br/>Log Collector]
            LOKI[Loki<br/>Log Storage]
        end

        subgraph "Traces"
            OTEL[OpenTelemetry<br/>Collector]
            TEMPO[Tempo<br/>Trace Storage]
        end
    end

    subgraph "Storage Layer"
        CORTEX[Cortex<br/>Long-term Metrics]
        S3[S3 Bucket<br/>Archive Storage]
    end

    subgraph "Visualization Layer"
        GRAFANA[Grafana<br/>Dashboards]
        ALERT[AlertManager<br/>Alert Routing]
    end

    subgraph "Dashboards"
        D1[System Overview]
        D2[Service Health]
        D3[Business Metrics]
        D4[Error Analysis]
        D5[Performance Metrics]
        D6[Custom Alerts]
    end

    subgraph "Alert Channels"
        SLACK[Slack]
        PAGER[PagerDuty]
        EMAIL[Email]
        WEBHOOK[Webhooks]
    end

    APP1 -->|Metrics| PROM
    APP2 -->|Metrics| PROM
    APP3 -->|Metrics| PUSHGW
    APP4 -->|Metrics| PUSHGW

    APP1 -->|Logs| FLUENTD
    APP2 -->|Logs| FLUENTD
    APP3 -->|Logs| FLUENTD
    APP4 -->|Logs| FLUENTD

    APP1 -->|Traces| OTEL
    APP2 -->|Traces| OTEL
    APP3 -->|Traces| OTEL
    APP4 -->|Traces| OTEL

    PUSHGW --> PROM
    FLUENTD --> LOKI
    OTEL --> TEMPO

    PROM --> CORTEX
    LOKI --> S3
    TEMPO --> S3

    PROM --> GRAFANA
    LOKI --> GRAFANA
    TEMPO --> GRAFANA
    CORTEX --> GRAFANA

    GRAFANA --> D1
    GRAFANA --> D2
    GRAFANA --> D3
    GRAFANA --> D4
    GRAFANA --> D5

    PROM --> ALERT
    ALERT --> D6

    ALERT --> SLACK
    ALERT --> PAGER
    ALERT --> EMAIL
    ALERT --> WEBHOOK
```

---

## CI/CD Pipeline

```mermaid
graph LR
    subgraph "Development"
        DEV[Developer]
        IDE[IDE/Local]
    end

    subgraph "Source Control"
        GIT[GitHub/GitLab]
        BRANCH[Feature Branch]
        PR[Pull Request]
        MAIN[Main Branch]
    end

    subgraph "CI Pipeline"
        subgraph "Build Stage"
            MAVEN[Maven Build]
            TEST[Unit Tests]
            SONAR[SonarQube Analysis]
        end

        subgraph "Security Scan"
            SAST[SAST Scan]
            DEPS[Dependency Check]
            SECRETS[Secret Scanning]
        end

        subgraph "Container Stage"
            DOCKER[Docker Build]
            SCAN[Container Scan]
            PUSH[Push to Registry]
        end
    end

    subgraph "Artifact Storage"
        NEXUS[Nexus Repository]
        ECR[ECR/Docker Registry]
        HELM[Helm Charts]
    end

    subgraph "CD Pipeline"
        subgraph "Dev Environment"
            DEV_DEPLOY[Deploy to Dev]
            DEV_TEST[Smoke Tests]
        end

        subgraph "Staging Environment"
            STAGE_DEPLOY[Deploy to Staging]
            INTEGRATION[Integration Tests]
            PERF[Performance Tests]
        end

        subgraph "Production"
            APPROVAL[Manual Approval]
            PROD_DEPLOY[Blue-Green Deploy]
            HEALTH[Health Checks]
            ROLLBACK[Rollback if Failed]
        end
    end

    subgraph "Infrastructure as Code"
        TERRAFORM[Terraform]
        ANSIBLE[Ansible]
        K8S_MANIFESTS[K8s Manifests]
    end

    DEV --> IDE
    IDE --> GIT
    GIT --> BRANCH
    BRANCH --> PR
    PR --> MAIN

    MAIN --> MAVEN
    MAVEN --> TEST
    TEST --> SONAR

    SONAR --> SAST
    SAST --> DEPS
    DEPS --> SECRETS

    SECRETS --> DOCKER
    DOCKER --> SCAN
    SCAN --> PUSH

    PUSH --> NEXUS
    PUSH --> ECR
    PUSH --> HELM

    ECR --> DEV_DEPLOY
    HELM --> DEV_DEPLOY
    DEV_DEPLOY --> DEV_TEST

    DEV_TEST --> STAGE_DEPLOY
    STAGE_DEPLOY --> INTEGRATION
    INTEGRATION --> PERF

    PERF --> APPROVAL
    APPROVAL --> PROD_DEPLOY
    PROD_DEPLOY --> HEALTH
    HEALTH -.->|Failed| ROLLBACK

    TERRAFORM --> DEV_DEPLOY
    TERRAFORM --> STAGE_DEPLOY
    TERRAFORM --> PROD_DEPLOY

    ANSIBLE --> DEV_DEPLOY
    K8S_MANIFESTS --> DEV_DEPLOY
```

---

## Disaster Recovery Architecture

```mermaid
graph TB
    subgraph "Primary Region - US-East-1"
        subgraph "Production Cluster"
            PROD_K8S[Kubernetes Cluster]
            PROD_APP[Application Services]
            PROD_DB[Databases]
            PROD_KAFKA[Kafka Cluster]
        end

        subgraph "Data Replication"
            SYNC1[Sync Replication]
            ASYNC1[Async Replication]
        end
    end

    subgraph "DR Region - US-West-2"
        subgraph "Standby Cluster"
            DR_K8S[Kubernetes Cluster<br/>Warm Standby]
            DR_APP[Application Services<br/>Scaled Down]
            DR_DB[Database Replicas]
            DR_KAFKA[Kafka MirrorMaker]
        end
    end

    subgraph "Backup Storage"
        S3_BACKUP[S3 Cross-Region<br/>Backup Storage]
        GLACIER[Glacier<br/>Long-term Archive]
    end

    subgraph "DR Orchestration"
        DR_MANAGER[DR Controller]
        HEALTH_CHECK[Health Monitor]
        FAILOVER[Failover Automation]
        DNS_SWITCH[Route53 DNS]
    end

    subgraph "Recovery Procedures"
        RTO[RTO: 4 hours]
        RPO[RPO: 15 minutes]
        RUNBOOK[DR Runbook]
        TESTING[Quarterly DR Test]
    end

    PROD_DB -.->|Sync| SYNC1
    PROD_KAFKA -.->|Async| ASYNC1
    SYNC1 --> DR_DB
    ASYNC1 --> DR_KAFKA

    PROD_DB --> S3_BACKUP
    S3_BACKUP --> GLACIER

    HEALTH_CHECK --> PROD_K8S
    HEALTH_CHECK --> DR_K8S
    HEALTH_CHECK --> FAILOVER

    FAILOVER --> DNS_SWITCH
    DNS_SWITCH --> DR_K8S

    DR_MANAGER --> RTO
    DR_MANAGER --> RPO
    DR_MANAGER --> RUNBOOK
    DR_MANAGER --> TESTING
```

---

## Security Architecture

```mermaid
graph TB
    subgraph "Edge Security"
        WAF[Web Application Firewall]
        DDOS[DDoS Protection]
        CDN_SEC[CDN Security]
    end

    subgraph "Network Security"
        subgraph "Perimeter"
            FW[Firewall Rules]
            NSG[Network Security Groups]
            NACL[Network ACLs]
        end

        subgraph "Internal"
            MESH[Service Mesh<br/>mTLS]
            SEGMENT[Network Segmentation]
            PRIVATELINK[Private Endpoints]
        end
    end

    subgraph "Identity & Access"
        subgraph "Authentication"
            OIDC[OIDC Provider]
            MFA[Multi-Factor Auth]
            SSO[Single Sign-On]
        end

        subgraph "Authorization"
            RBAC[Role-Based Access]
            POLICIES[IAM Policies]
            SVC_ACCOUNTS[Service Accounts]
        end
    end

    subgraph "Data Security"
        subgraph "Encryption"
            TLS[TLS in Transit]
            AES[AES-256 at Rest]
            KMS[Key Management Service]
        end

        subgraph "Data Protection"
            DLP[Data Loss Prevention]
            MASKING[Data Masking]
            TOKENIZATION[Tokenization]
        end
    end

    subgraph "Application Security"
        subgraph "Code Security"
            SAST_SEC[SAST Scanning]
            DAST[DAST Testing]
            IAST[IAST Monitoring]
        end

        subgraph "Runtime Security"
            RASP[Runtime Protection]
            CONTAINER_SEC[Container Security]
            SECRETS_MGR[Secrets Manager]
        end
    end

    subgraph "Compliance & Audit"
        AUDIT[Audit Logging]
        SIEM[SIEM Platform]
        COMPLIANCE[Compliance Checks]
        FORENSICS[Forensics Tools]
    end

    WAF --> FW
    DDOS --> NSG
    CDN_SEC --> NACL

    FW --> MESH
    NSG --> SEGMENT
    NACL --> PRIVATELINK

    OIDC --> RBAC
    MFA --> POLICIES
    SSO --> SVC_ACCOUNTS

    TLS --> DLP
    AES --> MASKING
    KMS --> TOKENIZATION

    SAST_SEC --> RASP
    DAST --> CONTAINER_SEC
    IAST --> SECRETS_MGR

    AUDIT --> SIEM
    SIEM --> COMPLIANCE
    COMPLIANCE --> FORENSICS
```

---

## Load Balancing and Scaling

```mermaid
graph TB
    subgraph "Load Balancing Layers"
        subgraph "Global Load Balancer"
            GLB[Global Load Balancer<br/>GeoDNS]
        end

        subgraph "Regional Load Balancers"
            RLB1[Region 1 ALB]
            RLB2[Region 2 ALB]
        end

        subgraph "Service Load Balancers"
            SLB1[Wave Service LB]
            SLB2[Task Service LB]
            SLB3[Pick Service LB]
        end
    end

    subgraph "Auto Scaling Groups"
        subgraph "Wave Planning ASG"
            WP_MIN[Min: 2 Pods]
            WP_TARGET[Target: 5 Pods]
            WP_MAX[Max: 10 Pods]
        end

        subgraph "Task Execution ASG"
            TE_MIN[Min: 3 Pods]
            TE_TARGET[Target: 8 Pods]
            TE_MAX[Max: 20 Pods]
        end

        subgraph "Pick Execution ASG"
            PE_MIN[Min: 3 Pods]
            PE_TARGET[Target: 8 Pods]
            PE_MAX[Max: 20 Pods]
        end
    end

    subgraph "Scaling Metrics"
        CPU[CPU Utilization > 70%]
        MEM[Memory > 80%]
        QUEUE[Queue Depth > 100]
        LATENCY[P95 Latency > 500ms]
        CUSTOM[Custom Metrics]
    end

    subgraph "Scaling Policies"
        HPA[Horizontal Pod Autoscaler]
        VPA[Vertical Pod Autoscaler]
        CA[Cluster Autoscaler]
        PREDICTIVE[Predictive Scaling]
    end

    GLB --> RLB1
    GLB --> RLB2

    RLB1 --> SLB1
    RLB1 --> SLB2
    RLB1 --> SLB3

    SLB1 --> WP_TARGET
    SLB2 --> TE_TARGET
    SLB3 --> PE_TARGET

    CPU --> HPA
    MEM --> VPA
    QUEUE --> HPA
    LATENCY --> HPA
    CUSTOM --> PREDICTIVE

    HPA --> WP_TARGET
    HPA --> TE_TARGET
    HPA --> PE_TARGET

    VPA --> WP_TARGET
    CA --> WP_MAX
    CA --> TE_MAX
    CA --> PE_MAX
```

---

## Service Mesh Architecture

```mermaid
graph TB
    subgraph "Service Mesh - Istio"
        subgraph "Control Plane"
            ISTIOD[Istiod<br/>Control Plane]
            PILOT[Pilot<br/>Service Discovery]
            CITADEL[Citadel<br/>Security]
            GALLEY[Galley<br/>Configuration]
        end

        subgraph "Data Plane"
            subgraph "Service A"
                SA[Service A Container]
                EA[Envoy Proxy A]
            end

            subgraph "Service B"
                SB[Service B Container]
                EB[Envoy Proxy B]
            end

            subgraph "Service C"
                SC[Service C Container]
                EC[Envoy Proxy C]
            end
        end

        subgraph "Mesh Features"
            subgraph "Traffic Management"
                LB[Load Balancing]
                RETRY[Retry Logic]
                CIRCUIT[Circuit Breaker]
                TIMEOUT[Timeouts]
            end

            subgraph "Security"
                MTLS[Mutual TLS]
                AUTHZ[Authorization Policies]
                JWT[JWT Validation]
            end

            subgraph "Observability"
                METRICS[Metrics Collection]
                TRACING[Distributed Tracing]
                LOGGING[Access Logging]
            end
        end

        subgraph "Ingress/Egress"
            IGW[Istio Ingress Gateway]
            EGW[Istio Egress Gateway]
        end
    end

    subgraph "External"
        CLIENT[External Client]
        EXTERNAL_SVC[External Service]
    end

    CLIENT --> IGW
    IGW --> EA

    SA <--> EA
    SB <--> EB
    SC <--> EC

    EA <--> EB
    EB <--> EC
    EC --> EGW
    EGW --> EXTERNAL_SVC

    ISTIOD --> EA
    ISTIOD --> EB
    ISTIOD --> EC

    EA --> METRICS
    EB --> TRACING
    EC --> LOGGING

    PILOT --> EA
    CITADEL --> MTLS
    GALLEY --> AUTHZ
```