# Deployment Guide — Kenya & East Africa

## Recommended hosting for Kenyan users

### Option A — Hetzner (best price/performance from Kenya)
Hetzner EU servers have good latency to Nairobi (~50–80ms).
Significantly cheaper than AWS/GCP for the same specs.

```
Recommended spec (baseline model, up to ~500 req/min):
  CPX21 — 3 vCPU, 4GB RAM, 80GB SSD — €5.77/month

When you switch to transformer (AfroXLM-R):
  CPX41 — 8 vCPU, 16GB RAM, 240GB SSD — €21.71/month
  Or add a GPU node for training only (CCX33)
```

### Option B — Azure East Africa (Johannesburg region)
Closest major cloud to Nairobi — ~15ms latency.
More expensive but better SLA for enterprise customers.

```
Recommended: Standard_B2s (2 vCPU, 4GB) — ~$35/month
```

### Option C — DigitalOcean (simplest setup)
Good developer experience, Terraform support, easy managed databases.

```
Recommended: 2 vCPU, 4GB — $24/month (Bangalore or Frankfurt)
```

---

## First deploy — step by step

### 1. Provision a server

```bash
# Example: Hetzner CPX21 running Ubuntu 22.04
# SSH in once provisioned:
ssh root@YOUR_SERVER_IP
```

### 2. Install dependencies

```bash
apt update && apt upgrade -y
apt install -y git docker.io docker-compose-plugin nginx certbot python3-certbot-nginx

# Add your deploy user (don't run as root in production)
adduser sauti
usermod -aG docker sauti
su - sauti
```

### 3. Clone the repo

```bash
cd /opt
git clone https://github.com/your-org/sauti.git
cd sauti
cp .env.example .env
```

### 4. Configure your environment

```bash
nano .env
```

Fill in at minimum:
```
SAUTI_API_KEYS=<generate with: python3 -c "import secrets; print(secrets.token_urlsafe(32))">
ENV=production
ALLOWED_ORIGINS=https://sauti.africa,https://app.sauti.africa
```

### 5. Train the initial model

```bash
# Train from seed data — takes <30 seconds on CPU
docker-compose -f infra/docker-compose.yml --profile train run train

# Verify model exists
ls ml/runs/
# Should show: baseline_YYYYMMDD_HHMMSS.pkl
```

### 6. Start the API

```bash
docker-compose -f infra/docker-compose.prod.yml up -d

# Check it's running
curl http://localhost:8000/health
# Expected: {"status":"ok","model_loaded":true,...}
```

### 7. Configure DNS

Point these DNS records at your server IP:
```
A    api.sauti.africa    →  YOUR_SERVER_IP
A    sauti.africa        →  YOUR_SERVER_IP
```

### 8. Get SSL certificates

```bash
certbot --nginx -d api.sauti.africa -d sauti.africa \
  --email admin@sauti.africa --agree-tos --non-interactive
```

Then update `nginx.conf` to enable the HTTPS redirect (uncomment the `return 301` line).

### 9. Test the live API

```bash
curl -X POST https://api.sauti.africa/v1/analyze \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Wewe ni mjinga kabisa na hujui kitu"}'
```

---

## Ongoing operations

### Model updates
When you have new annotated data and a retrained model:
```bash
# On your local machine:
scp ml/runs/baseline_NEWDATE.pkl sauti@YOUR_SERVER:/opt/sauti/ml/runs/

# On the server — restart API to pick up new model:
docker-compose -f infra/docker-compose.prod.yml restart api
```

### Viewing logs
```bash
# API logs
docker logs sauti-api -f

# Nginx access logs
tail -f /opt/sauti/infra/nginx/logs/access.log

# Feedback submissions
tail -f /opt/sauti/data/feedback/feedback.jsonl
```

### Monitoring uptime (free)
Set up a free monitor at uptimerobot.com:
- Monitor type: HTTP(s)
- URL: `https://api.sauti.africa/health`
- Interval: 5 minutes
- Alert: email + SMS

### Backups
```bash
# Cron job — daily backup of models and feedback to object storage
crontab -e

# Add:
0 2 * * * tar -czf /tmp/sauti-backup-$(date +%Y%m%d).tar.gz \
  /opt/sauti/ml/runs/ /opt/sauti/data/feedback/ && \
  rclone copy /tmp/sauti-backup-*.tar.gz remote:sauti-backups/ && \
  rm /tmp/sauti-backup-*.tar.gz
```

---

## Cost estimate — Kenya launch

| Item | Provider | Cost/month |
|------|----------|-----------|
| VPS (baseline model) | Hetzner CPX21 | ~$7 |
| Domain (sauti.africa) | Namecheap/Porkbun | ~$1 |
| SSL | Let's Encrypt | Free |
| Uptime monitoring | UptimeRobot | Free |
| Email alerts | Gmail SMTP | Free |
| **Total** | | **~$8/month** |

When you upgrade to transformer model:
| VPS (transformer) | Hetzner CPX41 | ~$24 |

---

## Scaling beyond Kenya

When expanding to Uganda, Tanzania, Rwanda:
1. Add a CDN (Cloudflare free tier) in front of your API — reduces latency from $8/month server
2. Add language support for Luganda, Kinyarwanda in `cleaner.py` and annotation schema
3. Deploy a second annotation campaign with local annotators in each country
4. Consider a Cloudflare Worker for geographic routing once you have multi-region servers
