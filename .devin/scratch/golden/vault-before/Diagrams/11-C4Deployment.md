---
parent: 02-Architecture
tags: [diagram, c4, deployment]
---

# C4 Deployment — Infrastructure Topology

<!-- Sources: infra/terraform/main.tf:1, docker-compose.yml:1, .env.example:1 -->

```mermaid
C4Deployment
  Developer ->> WebServer : HTTPS
  WebServer ->> AppContainer : Node.js
  AppContainer ->> DbContainer : PostgreSQL
  AppContainer ->> CacheContainer : Redis
  CacheContainer ->> QueueContainer : RabbitMQ
```

## Links
- [[02-Architecture]]
- [[07-Config]]
