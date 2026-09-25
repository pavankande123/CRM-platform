# Deploying Enermax CRM to Vercel

Enermax CRM consists of a **React + Vite Frontend** and a **FastAPI + PostgreSQL + Redis Backend**.

Because Vercel is specialized for frontend Single Page Applications (SPAs) and Serverless Edge functions, the recommended production architecture is:
* **Frontend**: Hosted on **Vercel** (Global Edge CDN, automatic preview branches, instant deployments).
* **Backend**: Hosted on a container platform such as **Render**, **Railway**, **Fly.io**, **DigitalOcean**, or **AWS ECS** where persistent PostgreSQL connection pools, Redis caching, and durable background workers operate seamlessly.

---

## 1. Quick Deploy via Vercel Web Dashboard (Recommended)

1. **Push your code to GitHub / GitLab / Bitbucket**:
   Ensure your repository has the latest commits.

2. **Log into [Vercel Dashboard](https://vercel.com/new)**:
   Click **"Add New..."** → **"Project"** and select your `CRM-ENERMAX` repository.

3. **Configure the Project**:
   * **Framework Preset**: `Vite`
   * **Root Directory**: Click *Edit* and select `frontend` (⚠️ **Critical**)
   * **Build Command**: `npm run build` (Default)
   * **Output Directory**: `dist` (Default)
   * **Install Command**: `npm install` (Default)

4. **Add Environment Variables**:
   Under the **Environment Variables** section, add:
   * **`VITE_API_URL`**: `https://api.yourdomain.com/api/v1` (URL of your live backend API)

5. **Deploy**:
   Click **Deploy**. Vercel will build the frontend bundle and assign a production URL (e.g. `https://enermax-crm.vercel.app`).

---

## 2. Deploy via Vercel CLI

You can also deploy directly from your local terminal:

1. Open your terminal in the `frontend` folder:
   ```bash
   cd frontend
   ```

2. Run Vercel deploy:
   ```bash
   npx vercel
   ```
   * Link to existing project? **No** (or **Yes** if created)
   * Project name: `enermax-crm`
   * In which directory is your code located? `./`
   * Override settings? **No**

3. When prompted, add the backend URL:
   ```bash
   npx vercel env add VITE_API_URL
   ```

4. For production deployment:
   ```bash
   npx vercel --prod
   ```

---

## 3. Client-Side Routing Configuration (`vercel.json`)

To ensure that direct page refreshes (e.g., navigating directly to `/dashboard` or `/projects`) do not return a `404 Not Found`, the [frontend/vercel.json](file:///c:/Users/Karuna%20K/Downloads/CRM%20ENERMAX/frontend/vercel.json) configuration has been placed in the `frontend` directory:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "cleanUrls": true,
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

---

## 4. Backend Pairing Options

Your Vercel frontend needs a live API URL to communicate with. Quick options for hosting the FastAPI backend:

| Provider | Free/Low Tier | Best For |
| :--- | :--- | :--- |
| **Railway** | $5/mo credit | 1-click Docker Compose deploy with managed Postgres & Redis |
| **Render** | Free tier available | Simple Web Service deployment for FastAPI |
| **Fly.io** | Generous tier | Global Docker containers close to Postgres |
| **DigitalOcean App Platform** | $5/mo | Production SLA with managed databases |
