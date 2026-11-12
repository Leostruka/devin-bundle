---
parent: 02-Architecture
tags: [diagram, c4, dynamic]
---

# C4 Dynamic — Checkout Runtime Collaboration

<!-- Sources: src/controllers/CheckoutController.ts:1, src/services/PaymentService.ts:1, src/services/InventoryService.ts:1 -->

```mermaid
C4Dynamic
  User ->> API : POST /checkout
  API ->> Payment : charge()
  Payment ->> Gateway : authorize
  Gateway -->> Payment : approved
  API ->> Inventory : reserve items
  Inventory -->> API : reserved
  API -->> User : 200 OK
```

## Links
- [[02-Architecture]]
