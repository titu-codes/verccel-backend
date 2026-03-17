# Railway Setup – Persistent Data (Required)

## Why does my data disappear on Railway?

Railway uses **ephemeral storage**. SQLite stores data in a file on the container filesystem. When your app restarts or redeploys, that file is wiped. Your data is lost.

**Solution:** Use **PostgreSQL** – Railway provides it and data persists.

---

## Step-by-Step: Add PostgreSQL to Railway

### 1. Add PostgreSQL Database

1. Go to [railway.app](https://railway.app) → your project
2. Click **+ New** (or **Add Service**)
3. Select **Database** → **Add PostgreSQL**
4. Railway will create a PostgreSQL service

### 2. Connect Backend to PostgreSQL

1. Click your **backend service** (the one running the FastAPI app)
2. Go to the **Variables** tab
3. Click **+ New Variable** or **Add Variable**
4. In the variable dropdown, select **Add Reference**
5. Choose your **PostgreSQL** service
6. Select **DATABASE_URL** – Railway will auto-fill the connection string
7. Save

### 3. Set USE_SQLITE (Optional)

Add a variable to explicitly use the database:

- **Name:** `USE_SQLITE`
- **Value:** `0`

(If `DATABASE_URL` is set, the app will use PostgreSQL even without this.)

### 4. Redeploy

1. Go to **Deployments**
2. Click **⋮** on the latest deployment → **Redeploy**

Or push a new commit to trigger a deploy.

---

## Verify

After redeploying:

1. Add an employee
2. Refresh the page – data should persist
3. Check the root URL – you should see `"HRMS Lite API is live on Railway! 🚀"`

---

## Using External PostgreSQL (Neon, Supabase)

If you prefer Neon or Supabase instead of Railway PostgreSQL:

1. Create a database at [neon.tech](https://neon.tech) or [supabase.com](https://supabase.com)
2. Copy the connection string
3. In Railway → your backend service → Variables:
   - Add `DATABASE_URL` = your connection string
   - Or `POSTGRES_URL` = your connection string
4. Redeploy
