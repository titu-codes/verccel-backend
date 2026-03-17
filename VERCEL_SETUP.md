# Backend on Vercel – Data Persistence Required

## Why does my data vanish?

On Vercel serverless, **SQLite does NOT persist data**. Each API request can run on a different server instance. The `/tmp` folder is ephemeral and not shared. Data written in one request is gone in the next.

## Fix: Add a persistent database

### Option 1: Neon (PostgreSQL) – Recommended, free tier

1. Go to [neon.tech](https://neon.tech) and create a free account
2. Create a new project
3. Copy the connection string (e.g. `postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require`)
4. In **Vercel** → Your backend project → **Settings** → **Environment Variables**:
   - Add `POSTGRES_URL` = your Neon connection string
   - **Remove** `USE_SQLITE` or set `USE_SQLITE=0`
5. Redeploy

### Option 2: Supabase (PostgreSQL) – Free tier

1. Go to [supabase.com](https://supabase.com) and create a project
2. Settings → Database → Connection string (URI)
3. In Vercel: Add `DATABASE_URL` = the connection string
4. Remove `USE_SQLITE` or set `USE_SQLITE=0`
5. Redeploy

### Option 3: MySQL (Aiven, Railway, PlanetScale)

Add `DATABASE_URL=mysql+pymysql://user:pass@host:port/database` in Vercel env vars.

---

After adding the database, redeploy. Your data will persist across requests and page refreshes.
