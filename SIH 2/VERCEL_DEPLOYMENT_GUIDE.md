# THERMOSHELTER — Vercel Deployment Guide

This guide provides step-by-step instructions for deploying the **THERMOSHELTER** Digital Twin & ANSYS Enterprise Validation Bridge to [Vercel](https://vercel.com).

---

## 🏛 Architecture Overview

THERMOSHELTER deploys as a hybrid full-stack application on Vercel:

1. **Static Frontend (Root)**:
   - High-fidelity interactive digital twin interface (`index.html`, `style.css`, `script.js`).
   - High-resolution textures, diagrams, and photographic assets (`assets/`).
   - Served directly by Vercel's global edge CDN with cache-control headers.
2. **Serverless Python Microservice (`api/index.py`)**:
   - FastAPI microservice running on AWS Lambda via Vercel Serverless Functions.
   - Bundles institutional engineering modules: `ansys_export_service.py`, `ansys_models.py`, and `backend/`.
   - Generates ANSYS JSON payloads, Fluent `.dat` boundary conditions, transient load CSVs, and complete validation ZIP archives.

---

## 🚀 Deployment Methods

### Method 1: Deploy via Vercel Web Dashboard (Recommended)

This method provides automated deployments on every `git push`.

1. **Push your code to GitHub / GitLab / Bitbucket**:
   ```bash
   git add .
   git commit -m "Configure project for Vercel deployment"
   git push origin main
   ```

2. **Import into Vercel**:
   - Go to [vercel.com/new](https://vercel.com/new).
   - Connect your Git provider and select the **SIH / THERMOSHELTER** repository.

3. **Project Settings**:
   - **Framework Preset**: Select `Other` (or leave default auto-detect).
   - **Root Directory**: `./` (Default).
   - **Build & Development Settings**:
     - *Build Command*: Leave empty (Overridden by `vercel.json`).
     - *Output Directory*: `.` (Handled automatically by `vercel.json`).
     - *Install Command*: Leave empty or default.
   - **Environment Variables**: None required by default.

4. **Deploy**:
   - Click **Deploy**. Vercel will install dependencies from `requirements.txt`, bundle the Python API, configure static routes, and publish your site in seconds.

---

### Method 2: Deploy via Vercel CLI

If you prefer terminal-based deployment:

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm install -g vercel
   ```

2. **Authenticate with Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy Preview / Staging**:
   ```bash
   vercel
   ```
   Follow the interactive prompts (accept defaults by pressing Enter).

4. **Deploy Directly to Production**:
   ```bash
   vercel --prod
   ```

---

## 🌐 Deployed Endpoints & Testing

Once deployed, your project URL (`https://<project-name>.vercel.app`) exposes the following endpoints:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Main Digital Twin Dashboard & 3D Visualizer |
| `/api` | `GET` | API status, kernel version, and standard compliance info |
| `/api/health` | `GET` | Service health status check |
| `/api/ansys/payload` | `GET` | Complete ANSYS FEA simulation payload (JSON) |
| `/api/ansys/export/json` | `GET` | Download formatted ANSYS payload `.json` file |
| `/api/ansys/export/fluent-dat` | `GET` | Download ANSYS Fluent `.dat` boundary condition script |
| `/api/ansys/export/transient-csv` | `GET` | Download transient thermal loads `.csv` |
| `/api/ansys/export/zip` | `GET` | Download complete institutional ANSYS validation ZIP package |
| `/api/ansys/validate` | `GET` | Preflight compliance and design rule audit result |

> **Query Parameters**: For simulation endpoints, you can optionally pass `altitude` (in meters MSL, e.g. `?altitude=4200`) and `sim_id` (e.g. `?sim_id=TS-LAD-2026-0042`).

---

## ⚙️ Key Configuration Files

- **`vercel.json`**:
  - Specifies `"outputDirectory": "."` for static files.
  - Declares `"includeFiles"` for `api/index.py` so backend Python modules are bundled in serverless execution containers.
  - Sets security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`) and static asset caching.
- **`.python-version`**:
  - Pins the serverless Python environment to `3.12`.
- **`requirements.txt`**:
  - Declares Python dependencies (`fastapi`, `pydantic`, `uvicorn`).
- **`.vercelignore`**:
  - Excludes raw duplicate image files and local development artifacts from being uploaded, speeding up deployments.

---

## 🛠 Local Development Verification

You can continue testing locally at any time:

- **Run Static Dashboard**:
  ```bash
  npm run dev
  ```
- **Run Full Python Backend + Static Server**:
  ```bash
  python backend/main.py
  ```
