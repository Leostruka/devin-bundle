---
parent: 02-Architecture
tags: [diagram, c4, context]
---

# System Context

```mermaid
graph TB
  User([User]) --> System[GoldenTest]
  System --> Email[Email Service]
  System --> Payment[Payment Gateway]
```

## Links
- [[02-Architecture]]
