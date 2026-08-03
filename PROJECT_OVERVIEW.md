# Project Overview: LeadGen AI (Lead Generation Agent)

LeadGen AI is a B2B Lead Generation and Market Intelligence application designed specifically to scan, discover, extract, validate, and enrich B2B business leads in the **GCC (Gulf Cooperation Council) region**, with a focus on the **UAE (Dubai, Abu Dhabi, etc.)** market.

This document serves as a complete reference for the project's architecture, technology stack, directory structure, data pipeline, and setup.

---

## 🏗️ Architecture & Technology Stack

The application is built using a modern, split-architecture stack running the frontend and backend concurrently:

### 1. Frontend
* **Framework**: React 19 (via Vite 6 & TypeScript)
* **Styling**: Tailwind CSS, Class Variance Authority (CVA), Lucide React, and Motion animations.
* **UI Components**: Modern dark-themed dashboard elements built using Shadcn/UI (Button, Card, Input, Label, Sonner toasts, Table, Tabs).

### 2. Backend
* **Framework**: Python FastAPI
* **Development Server**: Uvicorn (running with hot reload on port `8000`)
* **Real-time Communication**: **Server-Sent Events (SSE)** via FastAPI's `StreamingResponse` to push pipeline progress logs to the frontend.

### 3. Database
* **Engine**: PostgreSQL
* **Driver**: `asyncpg` (Python) and `pg` (Node/TypeScript utilities)
* **Features**: Smart record syncing and deduplication based on website/domain, email, and company name overlaps.

### 4. AI & Search Integrations
* **LLM Engine**: Configured to work with multiple model SDKs (Anthropic Claude, Google Gemini, OpenAI, Groq Llama, and xAI Grok).
* **Search Engine**: **Serper.dev API** (Google Organic Search and Google Maps Places API) to source live website links and location markers.

---

## 📂 Project Directory Structure

```text
Lead_Generation_Agent/
├── backend/                    # FastAPI Python Backend
│   ├── api/
│   │   └── routes/
│   │       └── leads.py        # Lead generation routes (endpoints & SSE pipeline stream)
│   ├── database/
│   │   └── connection.py       # PostgreSQL pool lifecycle management
│   ├── models/
│   │   └── lead_models.py      # Pydantic schemas for request validation
│   ├── services/
│   │   ├── database.py         # DB tables initialization and query helpers
│   │   ├── product_analyzer.py # AI keywords & target audience analyzer
│   │   ├── company_discovery.py# Google/Serper.dev searches
│   │   ├── lead_extractor.py   # AI structured entity extraction from web text
│   │   ├── lead_enricher.py    # Follow-up contact data search
│   │   └── lead_validator.py   # Rules-based lead sanitization and screening
│   └── main.py                 # FastAPI application root & static files server
├── components/                 # Shared base UI Components (Shadcn layout elements)
│   └── ui/                     # Button, Card, Input, Label, Sonner, Table, Tabs
├── src/                        # Vite React Frontend
│   ├── components/
│   │   ├── EmailOutreach.tsx   # Email campaign templates, sandbox, and Google Apps Script connection
│   │   └── GenerateLeads.tsx   # Search input configuration, Excel file parser, and stream logs
│   ├── lib/
│   │   ├── claude.ts           # Dropdown list logic & legacy Anthropic lead client
│   │   ├── db.ts               # Local PostgreSQL query scripts (Node-based)
│   │   ├── gemini.ts           # Gemini SDK wrapper
│   │   ├── groq.ts             # Groq SDK wrapper
│   │   ├── leadEnricher.ts     # Enrichment crawler scripts
│   │   ├── leadExtractor.ts    # Content extraction logic
│   │   ├── leadValidator.ts    # Filtering regex rules
│   │   ├── openai.ts           # OpenAI SDK wrapper
│   │   ├── productAnalyzer.ts  # Product prompt contexts
│   │   ├── searchService.ts    # Web search helpers
│   │   └── x.ts                # xAI Grok SDK integration
│   ├── App.tsx                 # Main SPA dashboard shell, tabs, and export-to-Excel logic
│   ├── index.css               # Global Tailwind CSS configurations & themes
│   └── main.tsx                # App entrypoint
├── bulk_mail_script.gs         # Google Apps Script script for bulk campaigns
├── check_db.cjs                # PostgreSQL connection tester script
├── package.json                # Frontend packages & concurrently run script
├── requirements.txt            # FastAPI backend dependencies
└── tsconfig.json               # TypeScript configurations
```

---

## ⚡ The 6-Stage Lead Generation Pipeline

When a user initiates lead generation (either through the target parameters dropdown or a bulk file upload), the backend initiates a Server-Sent Events stream that processes the leads through the following stages:

```mermaid
graph TD
    A[UI Parameter Selection / Excel Upload] --> B[Stage 1: Product Analysis]
    B -->|AI-Generated Search Keywords| C[Stage 2: Company Discovery]
    C -->|Websites & Places Listings| D[Stage 3: Lead Extraction]
    D -->|Initial Contact & Profile Details| E[Stage 4: Deep Enrichment]
    E -->|Enriched Phone & Mail data| F[Stage 5: Validation & Filtering]
    F -->|Sanitized Valid Leads| G[Stage 6: PostgreSQL Deduplication]
    G --> H[Interactive Grid UI & Excel Export]
    H --> I[Outreach Sandbox: Custom Mails & Apps Script Campaigns]
```

### 1. Product Analysis
Translates product names, descriptions, and brands into specific regional search terms, target buyer profiles, competitor lists, and market categories using AI.

### 2. Company Discovery
Fires concurrent queries to the **Serper.dev** API targeting the GCC region. It fetches organic Google search listings and Google Maps Places listings (providing phone numbers, street addresses, and website domains).

### 3. Lead Extraction
Takes the search text and snippets and parses them into structured JSON schemas. It maps contacts, positions (e.g., Procurement Manager, General Manager), segments, priority levels, and websites.

### 4. Deep Enrichment
For contacts with missing fields (such as missing email, LinkedIn profile, or phone number), the backend runs secondary search engine queries targeting the parsed domains to extract the remaining contact info.

### 5. Validation & Filtering
Cleans up the database records by:
* Checking domain formatting.
* Filtering out generic/placeholder data (e.g., `test.com`, `example.com`, `admin@domain.com`).
* Enforcing correct phone/GCC-standard phone configurations.

### 6. Deduplication & Save
Upserts records into PostgreSQL. If a lead matches an existing record's website or email, the database is partially updated with the newer/previously missing info instead of generating duplicate entries.

---

## 🗄️ Database Schema

### `leads` Table
Stores all the compiled and verified leads.
```sql
CREATE TABLE public.leads (
    id SERIAL PRIMARY KEY,
    name TEXT,
    title TEXT,
    company TEXT,
    email TEXT,
    phone TEXT,
    website TEXT,
    location TEXT,
    linkedin TEXT,
    segment TEXT,
    priority TEXT,
    channel TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    verified BOOLEAN DEFAULT TRUE
);
```

### `product_services` Table
Feeds target configuration parameters to the dashboard dropdowns.
```sql
CREATE TABLE public.product_services (
    id SERIAL PRIMARY KEY,
    category_type TEXT,        -- 'PACKAGE' or 'SERVICE'
    product_service_type TEXT, -- Software, Consulting, Maintenance, etc.
    product_service_name TEXT  -- Specific package or service name
);
```

---

## 🚀 Setting Up the Project Locally

### 1. Prerequisites
* **Node.js** (v18+)
* **Python** (v3.9+) with `pip`
* **PostgreSQL** running locally or hosted

### 2. Environment Configurations
Create a `.env` file in the root directory:
```ini
# Server Port
PORT=8000

# Database Connection URL
DATABASE_URL=postgres://username:password@localhost:5432/Lead_DB

# API Key for Google Search engine scraper
SERPER_API_KEY=your_serper_dev_api_key_here

# AI Model Provider Keys (Use any or all)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
XAI_API_KEY=your_xai_api_key_here
```

### 3. Install Dependencies
```bash
# Install Node packages for frontend
npm install

# Activate python environment & install backend packages
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Running the Development Server
Use the single NPM dev script to spin up the React frontend (Vite) and Python backend (FastAPI/Uvicorn) concurrently:
```bash
npm run dev
```
* **Frontend Dashboard**: `http://localhost:5173`
* **Backend API**: `http://localhost:8000`
* **Backend API Documentation (Swagger UI)**: `http://localhost:8000/docs`
