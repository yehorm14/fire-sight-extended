# Deploying and configuration

## Environment variables

| Variable | Where | Purpose |
| --- | --- | --- |
| `VITE_BACKEND_URL` | frontend `.env.local` | API base URL, default `http://localhost:8000` |
| `VITE_EVENTS_API_URL` | frontend, optional | External events feed. Unset means built-in sample events |
| `CORS_ORIGINS` | backend | Comma-separated allowed origins, default `http://localhost:5173,http://127.0.0.1:5173` |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | backend, optional | Live explanations, model defaults to `gpt-4o-mini` |

Copy `backend/.env.example` to `backend/.env` and `frontend/fire_website/.env.example` to `.env.local`.

## Backend on Render

`render.yaml` defines the service. Set `CORS_ORIGINS` to your frontend URL, for example `https://fire-sight.vercel.app`. If it is unset, the API only accepts requests from localhost, the browser blocks the deployed frontend, and the API logs a startup warning.

## Frontend on Vercel

Set the project root to `frontend/fire_website` and `VITE_BACKEND_URL` to the Render URL, then redeploy.
