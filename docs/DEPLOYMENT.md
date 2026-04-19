# SAARTHI Deployment Guide

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- API Keys: Groq (required), Jina AI (optional), ElevenLabs (optional)

---

## Environment Setup

### 1. Core Services (Docker)

```bash
# Start all infrastructure
docker-compose up -d

# Verify services
docker-compose ps

# Expected services:
# - postgres:5432
# - redis:6379
# - neo4j:7687, 7474
# - qdrant:6333
# - minio:9000
```

### 2. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
GROQ_API_KEY=<your-groq-key>           # Get from console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_WHISPER_MODEL=whisper-large-v3

# Optional (for production)
JINA_API_KEY=<jina-key>                # For embeddings
ELEVENLABS_API_KEY=<elevenlabs-key>   # For TTS (use TTS_PROVIDER=mock in dev)

# Database URLs (default for local Docker)
DATABASE_URL=postgresql://saarthi:saarthi@localhost:5432/saarthi
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=saarthi_neo4j
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379/0
```

### 3. Initialize Data

```bash
# Populate Neo4j with eligibility rules
docker-compose exec neo4j cypher-shell -u neo4j -p saarthi_neo4j < packages/eligibility/init_kg.cypher

# Ingest product brochures into Qdrant (optional)
uv run python -m rag.ingest
```

---

## Running Locally

### Development Mode

```bash
# Terminal 1: API server
cd apps/api
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Web UI
cd apps/web
pnpm dev

# Terminal 3: Watch logs
docker-compose logs -f
```

**Access:**
- Web UI: http://localhost:3000
- API docs: http://localhost:8000/docs
- Dashboard: http://localhost:3000/dashboard
- Neo4j browser: http://localhost:7474
- Qdrant UI: http://localhost:6333/dashboard

---

## Production Deployment

### 1. Build Docker Images

```bash
# API
docker build -t saarthi-api:latest -f apps/api/Dockerfile .

# Web
docker build -t saarthi-web:latest -f apps/web/Dockerfile .
```

### 2. Production docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    image: saarthi-api:latest
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - DATABASE_URL=postgresql://saarthi:${DB_PASSWORD}@postgres:5432/saarthi
    depends_on:
      - postgres
      - redis
      - neo4j
      - qdrant
    restart: unless-stopped

  web:
    image: saarthi-web:latest
    environment:
      - NEXT_PUBLIC_API_URL=https://api.yourdomain.com
    ports:
      - "3000:3000"
    restart: unless-stopped

  postgres:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

  neo4j:
    image: neo4j:5.20
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
    volumes:
      - neo4j_data:/data
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  pgdata:
  neo4j_data:
  qdrant_data:
```

### 3. Reverse Proxy (Nginx)

```nginx
# /etc/nginx/sites-available/saarthi

upstream api {
    server localhost:8000;
}

upstream web {
    server localhost:3000;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /api {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /ws {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        proxy_pass http://web;
        proxy_set_header Host $host;
    }
}
```

---

## Scaling Considerations

### Horizontal Scaling

- **API:** Stateless, can run multiple instances behind load balancer
- **WebSocket:** Requires sticky sessions or Redis pub/sub
- **Database:** Use managed PostgreSQL (AWS RDS, GCP Cloud SQL)
- **Neo4j:** Use Neo4j Aura for managed graph database
- **Qdrant:** Use Qdrant Cloud or self-hosted cluster

### Performance Tuning

```python
# apps/api/main.py
app = FastAPI(
    workers=4,              # 2x CPU cores
    timeout_keep_alive=120,
    limit_concurrency=100
)

# Connection pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

### Monitoring

```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Key metrics to track:
# - saarthi_latency_ms{hop="asr"} (p50, p95)
# - saarthi_latency_ms{hop="llm"}
# - saarthi_latency_ms{hop="tts"}
# - saarthi_latency_ms{hop="e2e"}
```

---

## Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database connectivity
curl http://localhost:8000/api/analytics/summary

# Neo4j
echo "RETURN 1" | docker-compose exec -T neo4j cypher-shell -u neo4j -p saarthi_neo4j

# Qdrant
curl http://localhost:6333/collections
```

---

## Troubleshooting

### Common Issues

**1. WebSocket connection failed**
- Check NEXT_PUBLIC_API_URL in .env
- Verify API is running on port 8000
- Check browser console for CORS errors

**2. No audio playback**
- Browser autoplay policy blocks audio
- Click "Start Call" button (user interaction required)
- Check TTS_PROVIDER setting (use "mock" for testing)

**3. Eligibility always uses fallback**
- Verify Neo4j is running: `docker-compose ps neo4j`
- Check Neo4j logs: `docker-compose logs neo4j`
- Reinitialize: `docker-compose exec neo4j cypher-shell < init_kg.cypher`

**4. High latency (p50 > 1000ms)**
- Check Groq API status
- Verify network connectivity
- Review TTS provider response time
- Check database query performance

---

## Security Checklist

- [ ] Change all default passwords in .env
- [ ] Enable SSL/TLS for production
- [ ] Restrict Neo4j/Postgres access (firewall rules)
- [ ] Enable authentication on Redis
- [ ] Use secrets manager (AWS Secrets, HashiCorp Vault)
- [ ] Enable CORS only for trusted origins
- [ ] Set up rate limiting on API endpoints
- [ ] Enable Presidio for PII redaction in logs

---

## Backup & Recovery

```bash
# Backup Postgres
docker-compose exec postgres pg_dump -U saarthi saarthi > backup.sql

# Backup Neo4j
docker-compose exec neo4j neo4j-admin database dump neo4j --to=/backups/neo4j.dump

# Backup Qdrant
curl -X POST http://localhost:6333/collections/saarthi_knowledge/snapshots

# Restore
docker-compose exec postgres psql -U saarthi -d saarthi < backup.sql
```

---

**Support:** See `docs/` for additional guides or open an issue on GitHub.
