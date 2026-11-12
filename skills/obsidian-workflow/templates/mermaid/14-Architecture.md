---
parent: 02-Architecture
tags: [diagram, architecture, overview]
---

# Architecture Overview

```mermaid
graph TB
  subgraph DNS["DNS & CDN"]
    CF[Cloudflare<br/>DNS + SSL + WAF]
  end
  subgraph Server["Application Server"]
    Apache[Apache 2.4]
    PHP[PHP-FPM]
    App[{project_name}]
  end
  subgraph Data["Data Layer"]
    DB[(Database)]
    Cache[(Cache)]
  end
  CF --> Apache
  Apache --> PHP
  PHP --> App
  App --> DB
  App --> Cache
```

## Links
- [[02-Architecture]]
- [[11-C4Deployment]]
