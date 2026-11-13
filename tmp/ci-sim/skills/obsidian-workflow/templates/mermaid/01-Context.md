---
parent: 02-Architecture
tags: [diagram, c4, context]
---

# System Context

```mermaid
graph TB
  User([User]) --> System[{project_name}]
  System --> Email[Email Service]
  System --> Payment[Payment Gateway]
```

## Links
- [[02-Architecture]]
