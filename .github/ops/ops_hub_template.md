# 🧭 Ops Hub — Fonte única da verdade

## Checklist de implantação (robôs marcam conforme forem concluindo)
- [ ] (1) Manifesto clínico `docs/ops/manifest.yaml` publicado
- [ ] (2) Tríade (CI + Watcher + Verificador E2E) ativa
- [ ] (3) u-ETG blindado (TZ, retry, idempotência, parser horário)
- [ ] (4) Inventário/Linter de Templates Meta ativo
- [ ] (5) Webhooks resilientes (ACK+fila, idempotência, retry/429/5xx/4xx)
- [ ] (6) Monitores sintéticos da Admin (UI + APIs)
- [ ] (7) Relatórios Admin (sorteios/envios/confirmados + CSV)
- [ ] (8) Canário + promoção automatizada
- [ ] (9) Digest WhatsApp + Issue semanal
- [ ] (10) Autonomia configurável (auto-merge trivial, fallback template→texto)
