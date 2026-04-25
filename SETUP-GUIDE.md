# SAARTHI Setup & Data Population Guide

## Issues Fixed

### 1. ✅ All Products Now Live
- **Before**: Only Personal Loan was live; 9 products showed "Coming Soon"
- **After**: All 10 products are now marked as `live: true` and available for demo calls
- **File**: `apps/web/app/page.tsx`

### 2. ✅ Analytics API Fixed
- **Before**: API returned all 10 products even when no calls existed (showing 0 for everything)
- **After**: API only returns products that have actual call data
- **File**: `apps/api/routes/analytics.py`

### 3. ✅ Database Seeding Script Created
- **New**: Added seed script to populate database with realistic test data
- **File**: `apps/api/seed_data.py`

---

## Quick Start

### Step 1: Start Database Services

Make sure Docker Desktop is running, then:

```bash
make up
```

This starts:
- PostgreSQL (calls database)
- Redis (pub/sub)
- Qdrant (vector DB for RAG)
- Neo4j (knowledge graph)
- MinIO (object storage)

### Step 2: Seed the Database

Populate the database with test call data:

```bash
make seed
```

This will create:
- **80-150 total calls** across all 10 products
- **5-15 calls per product** with varied outcomes
- Realistic data: durations (30-300s), turn counts, latency stats
- Calls distributed over the last 7 days

**Expected Output:**
```
🌱 Seeding database with test data...
  Creating 12 calls for personal_loan...
  Creating 8 calls for home_loan...
  Creating 15 calls for education_loan...
  ...
✅ Successfully created 103 test calls across 10 products!
```

### Step 3: Start the Application

In separate terminals:

**Terminal 1 - API Server:**
```bash
make api
```

**Terminal 2 - Web Dashboard:**
```bash
make web
```

### Step 4: View the Dashboard

Open your browser to:
- **Homepage**: http://localhost:3000
- **Dashboard**: http://localhost:3000/dashboard

---

## What You'll See Now

### Homepage (/)
- ✅ All 10 products visible with "LIVE" badges
- ✅ No more "Coming Soon" labels
- ✅ Stats show "10 Live Products"

### Dashboard (/dashboard)
- ✅ **Total Calls**: Actual count (e.g., 103)
- ✅ **Qualified Rate**: Real percentage (e.g., 42.7%)
- ✅ **Avg Duration**: Realistic values (e.g., 156.3s)
- ✅ **p95 Latency**: Calculated from test data (e.g., 285ms)
- ✅ **Latency Profile Chart**: Shows p50/p95 bars
- ✅ **Qualification Snapshot**: Green progress bar with real data

### Call History (/dashboard/calls)
- ✅ Table populated with calls
- ✅ Filters work (by product, outcome)
- ✅ Shows: Call ID, Product, Outcome, Duration, Turns, Timestamp
- ✅ "0 matching calls" message replaced with actual data

### Product Performance (/dashboard/products)
- ✅ Bar chart shows calls by product
- ✅ Table with all products that have calls
- ✅ Columns: Product, Calls, Qualified Rate, Avg Duration
- ✅ No empty products displayed

---

## Seed Script Details

### Generate More Data

Want more test calls? Run seed again after clearing:

```bash
make seed-clear  # Clear existing data
make seed        # Generate fresh data
```

### Manual Seeding

```bash
# Default: create test data
uv run python apps/api/seed_data.py

# Clear all calls
uv run python apps/api/seed_data.py --clear
```

### What the Seed Creates

Each test call includes:
- **Unique IDs**: `call_id`, `customer_id`
- **Product**: Random from all 10 products
- **Outcome**: `qualified`, `not_qualified`, `dropped`, `no_consent`, `callback_requested`
- **Status**: `completed` or `dropped`
- **Timestamps**: Distributed over last 7 days
- **Duration**: 30-300s for completed, 5-30s for dropped
- **Turn Count**: 3-25 for completed, 1-5 for dropped
- **Latency Stats**: Realistic p50/p95 for ASR, LLM, TTS, E2E
- **Redacted Transcript**: Sample conversation
- **Agent/Lender Names**: Randomized from pools

---

## Troubleshooting

### Docker Not Running
```
Error: cannot find file specified
```
**Solution**: Start Docker Desktop, wait for it to fully initialize, then run `make up`

### Database Already Has Data
```
⚠️  Database already has X calls. Skipping seed.
```
**Solution**: This is intentional to prevent duplicates. Use `make seed-clear` then `make seed` to refresh.

### Port Already in Use
```
Error: address already in use
```
**Solution**: Stop any existing instances:
```bash
make down
make up
```

### Import Errors
```
ModuleNotFoundError: No module named 'sqlmodel'
```
**Solution**: Run `make setup` to install all dependencies

---

## Summary of Changes

| Component | File | Change |
|-----------|------|--------|
| Homepage | `apps/web/app/page.tsx` | Added `live: true` to all 10 products |
| Analytics API | `apps/api/routes/analytics.py` | Returns only products with calls (not all 10) |
| Seed Script | `apps/api/seed_data.py` | **NEW** - Populates database with test data |
| Makefile | `Makefile` | Added `make seed` and `make seed-clear` commands |

---

## Next Steps

1. ✅ Start Docker: `make up`
2. ✅ Seed database: `make seed`
3. ✅ Run API: `make api`
4. ✅ Run web: `make web`
5. ✅ Visit: http://localhost:3000

Now you have a fully populated dashboard with realistic test data across all 10 products! 🎉
