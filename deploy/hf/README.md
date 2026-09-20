---
title: Urban Flood Nowcast
emoji: 🌊
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# Urban Flood Nowcasting — Delhi V2 + Mumbai V1

Evidence-constrained urban flood nowcasting (SIH 2026).

- **Delhi V2** — Kushak–Barapullah catchment digital twin: live NWP-driven 0–3h
  forecast, what-if model scenarios, historical event replay, flood-aware routing.
- **Mumbai V1** — Kurla pilot legacy system.

Every modelled output is labeled with provenance (MODELLED / OBSERVED /
SYNTHETIC_FALLBACK). Health: `/ready`.
