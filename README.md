# Sauti — Harmful Speech Detection for East Africa

> *Sauti* means "voice" in Swahili.

Sauti is an open, multilingual system for detecting harmful, distressing, and manipulative communication patterns in East African digital spaces — with first-class support for **Swahili**, **Sheng**, and **English/Swahili code-switching**.

---

## What it detects

| Category | Description |
|---|---|
| `hate_speech` | Content targeting ethnicity, religion, gender, or political group |
| `offensive_language` | Insults, vulgar abuse, dehumanizing language |
| `distress_trigger` | Language likely to cause fear, panic, or emotional harm |
| `gaslighting` | Patterns that deny reality or undermine someone's perception |
| `manipulation` | Coercive or emotionally exploitative language |
| `ambiguous` | Flagged for human review — context-dependent |

Each prediction returns: **label**, **severity** (1–5), **confidence**, and **rationale spans**.

---

## Monorepo structure

```
sauti/
├── data/           # Raw → processed → annotated datasets
├── ml/             # Python ML core (training, inference, explainability)
├── api/            # FastAPI REST service
├── web/            # Next.js dashboard
├── mobile/         # React Native app (Phase 4)
├── annotation/     # Label Studio config + annotation guide
├── infra/          # Docker Compose, Nginx
└── docs/           # API reference, data policy, linguistic guide
```

---

## Quickstart (local dev)

```bash
# Clone and enter
git clone https://github.com/your-org/sauti.git
cd sauti

# Start all services
docker-compose -f infra/docker-compose.yml up --build

# API will be at:   http://localhost:8000
# Web will be at:   http://localhost:3000
# Annotation tool:  http://localhost:8080
```

---

## Language support

| Language | Status |
|---|---|
| English | ✅ Supported |
| Swahili (KE) | ✅ Supported |
| Sheng | 🔄 In progress |
| Kikuyu | 🗓 Planned |
| Luo | 🗓 Planned |

---

## Contributing

See [docs/contributing.md](docs/contributing.md). We especially welcome:
- Kenyan community annotators (paid)
- Swahili / Sheng linguistic reviewers
- Mental health professionals for category validation

---

## License

Apache 2.0 — free to use, modify, and deploy. Attribution appreciated.
