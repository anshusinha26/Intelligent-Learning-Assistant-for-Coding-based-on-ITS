# ILA Coding Frontend

## Vercel Deployment

Use these Vercel project settings:

```text
Framework Preset: Vite
Root Directory: frontend
Install Command: npm install
Build Command: npm run build
Output Directory: dist
```

Set this environment variable in Vercel:

```text
VITE_API_URL=https://your-backend-host/api
```

For local development:

```bash
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Local API default:

```text
http://localhost:8001/api
```
