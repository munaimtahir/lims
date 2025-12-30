# Frontend-Backend Connection Guide

## Simple Beginner-Friendly Guide

This document explains how the frontend and backend talk to each other, and how to check if everything is working correctly.

---

## 📍 Understanding the Setup

### Development Mode (Your Local Computer)

When you run the application on your computer for development:

1. **Frontend** runs on: `http://localhost:5173` (Vite dev server)
2. **Backend** runs on: `http://localhost:8000` (Django server)
3. **How they connect**: Frontend makes requests directly to `http://localhost:8000/auth/login/`, etc.

### Production Mode (VPS Server at 172.237.71.40)

When the application runs on the production server:

1. **Frontend** is served by nginx on: `http://172.237.71.40`
2. **Backend** runs inside Docker on: `http://backend:8000` (internal)
3. **How they connect**: 
   - Frontend makes requests to `/api/auth/login/`
   - Nginx sees the `/api` prefix and forwards the request to backend
   - Backend receives the request at `/api/auth/login/`

---

## 🔧 How the API URL Works

### Environment Variable: VITE_API_URL

This variable tells the frontend where to find the backend.

**In Development** (file: `frontend/.env.development`):
```
VITE_API_URL=http://localhost:8000
```

**In Production** (file: `frontend/.env.production`):
```
VITE_API_URL=/api
```

### How URLs Are Built

The frontend combines the base URL with the endpoint path:

**Development Example:**
- Base URL: `http://localhost:8000`
- Endpoint: `/auth/login/`
- Final URL: `http://localhost:8000/auth/login/` ✅

**Production Example:**
- Base URL: `/api`
- Endpoint: `/auth/login/`
- Final URL: `/api/auth/login/` → nginx forwards to backend ✅

### ⚠️ What Was Wrong Before

**The Problem:**
- Endpoint constants had `/api/auth/login/` (with `/api` prefix)
- In production: `/api` + `/api/auth/login/` = `/api/api/auth/login/` ❌
- Result: 404 error because backend doesn't have `/api/api/...` routes

**The Fix:**
- Removed `/api` prefix from all endpoint constants
- Now endpoints are: `/auth/login/`, `/patients/`, etc.
- In production: `/api` + `/auth/login/` = `/api/auth/login/` ✅

---

## 🚀 How to Deploy and Test on the Server

### Step 1: Log Into the Server

```bash
ssh root@172.237.71.40
```

### Step 2: Go to the Project Folder

```bash
cd /opt/lab
```
*(Replace `/opt/lab` with wherever you cloned the repository)*

### Step 3: Pull the Latest Code

```bash
git pull origin main
```

This downloads the latest changes from GitHub.

### Step 4: Rebuild the Application

```bash
docker compose build
```

This rebuilds the Docker images with your new code. It takes 2-3 minutes.

### Step 5: Start the Application

```bash
docker compose up -d
```

The `-d` means "run in the background". This command starts all the services:
- nginx (frontend server)
- backend (Django API)
- db (PostgreSQL database)
- redis (cache)

### Step 6: Wait for Services to Start

```bash
sleep 30
```

Wait 30 seconds for all services to fully start up.

### Step 7: Check If Services Are Running

```bash
docker compose ps
```

You should see 4 containers running:
- `lab_nginx_1` or similar
- `lab_backend_1`
- `lab_db_1`
- `lab_redis_1`

All should show "Up" status.

### Step 8: Test the Health Endpoint

```bash
curl http://172.237.71.40/api/health/
```

You should see something like:
```json
{"status":"healthy","timestamp":"...","database":"ok","redis":"ok"}
```

If you see this, the backend is working! ✅

### Step 9: Open the Website in a Browser

Open your web browser and go to:
```
http://172.237.71.40
```

You should see the login page.

### Step 10: Test Login

1. Open the login page: `http://172.237.71.40/login`
2. Enter username: `admin`
3. Enter password: `admin123` (or whatever password you set)
4. Click "Login"

**If login works:** You'll be redirected to the dashboard. Success! ✅

**If login fails:** Follow the troubleshooting steps below.

---

## 🐛 Troubleshooting: Check for Double /api/api/

### How to Check in Browser

1. Open the login page: `http://172.237.71.40/login`
2. Press F12 to open Developer Tools
3. Click on the "Network" tab
4. Try to log in
5. Look at the list of network requests

Find the request that says "login" and click on it.

Check the "Request URL" - it should look like:
```
✅ CORRECT: http://172.237.71.40/api/auth/login/
❌ WRONG:   http://172.237.71.40/api/api/auth/login/
```

If you see `/api/api/`, that's the double API bug.

### What Each Error Means

| URL | Status | What It Means |
|-----|--------|---------------|
| `/api/auth/login/` | 200 OK | ✅ Everything working! Login successful |
| `/api/auth/login/` | 401 Unauthorized | ✅ Backend is working, but username/password is wrong |
| `/api/auth/login/` | 404 Not Found | ❌ Backend route not found - check backend URLs |
| `/api/api/auth/login/` | 404 Not Found | ❌ Double API bug - endpoint constants have `/api` prefix |

### If You Still See /api/api/ After the Fix

This means the frontend wasn't rebuilt properly. Try:

```bash
# On the server
cd /opt/lab
docker compose down
docker compose build --no-cache nginx
docker compose up -d
```

The `--no-cache` forces Docker to rebuild everything from scratch.

---

## 📝 Key Files Reference

### Environment Files

| File | Purpose | VITE_API_URL Value |
|------|---------|-------------------|
| `frontend/.env.development` | Local development | `http://localhost:8000` |
| `frontend/.env.production` | Production build | `/api` |
| `.env` (root) | Docker Compose production | `VITE_API_URL=/api` |

### Code Files

| File | What It Does |
|------|-------------|
| `frontend/src/utils/constants.ts` | Defines all API endpoints (like `/auth/login/`) |
| `frontend/src/services/api.ts` | Makes HTTP requests to backend |
| `nginx/nginx.conf` | Configures nginx to proxy `/api` to backend |

### Config Logic

```
API Request Flow:
  Frontend Code → uses endpoint from constants.ts
  Example: AUTH_ENDPOINTS.LOGIN = '/auth/login/'
  
  API Client → prepends API_BASE_URL
  Production: '/api' + '/auth/login/' = '/api/auth/login/'
  Development: 'http://localhost:8000' + '/auth/login/' = 'http://localhost:8000/auth/login/'
  
  Browser → sends request
  Production: http://172.237.71.40/api/auth/login/
  
  Nginx → receives request, sees /api prefix
  Forwards to: http://backend:8000/api/auth/login/
  
  Backend → processes request at /api/auth/login/
  Returns: JSON response with token or error
```

---

## 🔍 Checking Logs

If something isn't working, check the logs to see what's happening.

### See All Logs

```bash
docker compose logs -f
```

Press Ctrl+C to stop viewing logs.

### See Only Backend Logs

```bash
docker compose logs -f backend
```

Look for lines that say:
- ✅ `"GET /api/health/ HTTP/1.1" 200` - means request succeeded
- ❌ `"GET /api/api/auth/login/ HTTP/1.1" 404` - means double API bug
- ✅ `"POST /api/auth/login/ HTTP/1.1" 200` - means login succeeded
- ⚠️ `"POST /api/auth/login/ HTTP/1.1" 401` - means wrong password

### See Only Nginx Logs

```bash
docker compose logs -f nginx
```

This shows what requests nginx received from browsers.

---

## ✅ Verification Checklist

After deployment, verify these work:

### 1. Health Check
```bash
curl http://172.237.71.40/api/health/
```
Expected: `{"status":"healthy",...}`

### 2. Frontend Loads
Open browser: `http://172.237.71.40`
Expected: See the login page

### 3. Login Works
- Username: `admin`
- Password: `admin123`
- Expected: Successfully log in and see dashboard

### 4. API Requests Don't Have /api/api/
- Open browser DevTools → Network tab
- Try to log in
- Check the login request URL
- Expected: `/api/auth/login/` (not `/api/api/auth/login/`)

### 5. No Console Errors
- Open browser DevTools → Console tab
- Expected: No red errors about failed requests

---

## 📞 Common Questions

**Q: Why do we use `/api` in production but `http://localhost:8000` in development?**

A: In production, nginx and backend are on the same server, so we use a relative path (`/api`). In development, they run on different ports, so frontend needs the full URL with port number.

**Q: What does nginx do?**

A: Nginx is a web server. It serves the frontend files (HTML, CSS, JavaScript) and forwards API requests to the backend. Think of it as a traffic director.

**Q: Why was there a double /api/api/ bug?**

A: The endpoint constants accidentally included `/api` prefix, so when combined with the base URL (`/api`), it doubled up. We fixed this by removing the `/api` prefix from the constants.

**Q: How do I test locally before deploying?**

A: Run these commands:
```bash
cd frontend
pnpm dev
```
Then in another terminal:
```bash
cd backend
python manage.py runserver
```
Open `http://localhost:5173` in your browser.

---

## 🎯 Summary

**Development:**
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Endpoints: `/auth/login/`, `/patients/`, etc.
- Full URL: `http://localhost:8000/auth/login/`

**Production:**
- Frontend: `http://172.237.71.40`
- Backend: internal, accessed through nginx
- Endpoints: `/auth/login/`, `/patients/`, etc.
- Full URL: `http://172.237.71.40/api/auth/login/`
- Nginx forwards `/api/*` to backend

**The Fix:**
- Removed `/api` prefix from all endpoint constants
- Now endpoints are relative to the base URL
- Production: `/api` + `/auth/login/` = `/api/auth/login/` ✅
- Development: `http://localhost:8000` + `/auth/login/` = `http://localhost:8000/auth/login/` ✅

---

*Last Updated: 2025-11-12*
