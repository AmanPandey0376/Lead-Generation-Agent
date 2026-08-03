# Project Summary: LeadGen AI (Lead Generation Agent)

LeadGen AI is a B2B Lead Generation and Market Intelligence application designed specifically for scanning, discovering, extracting, validating, and enriching B2B business leads in the GCC (Gulf Cooperation Council) region, with a primary focus on the UAE (Dubai, Abu Dhabi, etc.) market. 

It provides an interactive React-based UI linked to a TypeScript/Express backend (and an alternate Python/FastAPI backend) to automate target market discovery and email outreach.

---

## 🏗️ Architecture & Workflow

The system operates on a multi-stage search, extract, enrich, and validate pipeline. Below is the workflow diagram:

```mermaid
graph TD
    A[User UI Input: Manual/File] --> B[Stage 1: Product Analysis]
    B -->|Generate Search Keywords| C[Stage 2: Company Discovery via Serper.dev]
    C -->|Aggregate Websites & Map Listings| D[Stage 3: Lead Extraction via Claude]
    D -->|Identify Missing Fields| E[Stage 4: Lead Enrichment via Google Search]
    E -->|Clean & Sanitize| F[Stage 5: Lead Validation]
    F -->|Deduplicate & Partially Update| G[(PostgreSQL Database)]
    G --> H[Export to Excel]
    H --> I[Stage 6: Email Outreach Sandbox]
    I -->|Gmail Mailto / Apps Script| J[Bulk Outreach Campaign]
```

---

## ✨ Core Features

1. **Interactive Dashboard UI**:
   - **Target Parameters Configuration**: Choose predefined product categories, types, and names, or manually input division, product name, brand, and description.
   - **Bulk Upload**: Batch-process lists of products or SKUs by uploading an Excel worksheet (`.xlsx` or `.xls`).
   - **Interactive Leads Table**: Real-time progress updates, advanced client-side searching, table/split-pane/card views, and categorization filters (segment, priority, channel, location).
   - **Excel Export**: Quick download of generated leads in a sales-ready Excel file.

2. **Autonomous Multi-Stage Pipeline**:
   - **AI-Powered Product Analysis**: Translates raw descriptions into domain keywords, competitor brands, and specific buyer profiles.
   - **Live Web Scraping & Serper API Search**: Scans the live web (organic search and Google Maps Places listings) to source current domains, addresses, and phone numbers.
   - **Context-Bound Lead Extraction**: Evaluates raw web results to parse out name, title, email, phone, location, segment, and priority.
   - **Deep Lead Enrichment**: Selectively re-crawls search engines for company-specific contact, procurement, and LinkedIn details where data is missing.
   - **Robust Validation**: Enforces strict domain rules and rejects placeholders, generic email domains, dummy names, and incomplete listings.

3. **Email Outreach Sandbox**:
   - **Gmail Client Integration**: Generates customized Gmail compose URLs pre-populated with lead names, titles, companies, and partnership templates.
   - **Google Apps Script Integration**: Connects with a custom Google Apps Script web app template (`bulk_mail_script.gs`) for one-click bulk email campaigns.

4. **PostgreSQL Database Storage**:
   - Saves leads with smart deduplication. If a contact matches an existing company, email, or website in the database, it performs partial updates (fills in missing columns) instead of creating duplicate records.

---

## 📂 Project Directory Structure

```text
Lead_Generation_Agent/
├── components/                 # Shared UI Components (shadcn/ui layout elements)
│   └── ui/
│       ├── button.tsx, card.tsx, input.tsx, label.tsx, sonner.tsx, table.tsx, tabs.tsx
├── src/
│   ├── components/
│   │   ├── EmailOutreach.tsx   # Email Outreach dashboard, bulk email controls, sandbox layout
│   │   └── GenerateLeads.tsx   # Target parameters, file uploading, leads grid, streaming progress bar
│   ├── lib/
│   │   ├── claude.ts           # Predefined dropdown prompt, legacy Claude lead generator
│   │   ├── db.ts               # PostgreSQL connection pool and upsert/deduplication logic
│   │   ├── gemini.ts           # Gemini SDK lead generator (Gemini 2.0 / 1.5)
│   │   ├── groq.ts             # Groq SDK lead generator (Llama-3.3-70b-versatile)
│   │   ├── leadEnricher.ts     # Secondary Google search queries & target contact extraction
│   │   ├── leadExtractor.ts    # Initial search-result parsing using Claude Haiku 4.5
│   │   ├── leadValidator.ts    # Clean and filter logic for phone, email, websites, and placeholders
│   │   ├── openai.ts           # OpenAI SDK lead generator (GPT-4o)
│   │   ├── productAnalyzer.ts  # Claude-powered product context, competitors, and keywords analysis
│   │   ├── searchService.ts    # Serper.dev Google Search & Google Maps Places API integrations
│   │   └── x.ts                # xAI Grok SDK lead generator integration
│   ├── App.tsx                 # Main application dashboard layout, tab navigation, export scripts
│   ├── index.css               # Global Tailwind CSS custom design tokens, fonts, and scroll styles
│   └── main.tsx                # React app bootstrapping
├── bulk_mail_script.gs         # Google Apps Script for automated bulk email campaigns
├── check_db.cjs                # PostgreSQL connection verification script
├── index.html                  # Main React template wrapper
├── main.py                     # FastAPI Python equivalent backend (alternative implementation)
├── package.json                # Dependencies, Tailwind, and concurrently startup scripts
├── refactor.mjs                # App.tsx JSX splitting utility script
├── requirements.txt            # Python dependencies (FastAPI, pandas, asyncpg)
├── server.ts                   # TypeScript Express server (API endpoints, SSE generator stream, static build serving)
├── test-xai.ts                 # Test script for xAI Grok API compatibility
├── test_query.cjs              # Quick database SQL verification script
├── tsconfig.json               # TypeScript project configurations
└── vite.config.ts              # Vite configurations with Tailwind CSS plugins
```

---

## 🛠️ Key Modules & Components

### 🖥️ Express Backend (`server.ts`)
- Configures middleware, static directory hosts, and uploads folder.
- Exposes `POST /api/generate-leads`:
  - Establishes a chunked **Server-Sent Events (SSE)** stream (`text/event-stream`).
  - Sequentially fires the pipeline stages and writes progress reports to the client.
- Exposes other utility routes:
  - `GET /api/product-service-types`: Returns types filtered by category (`PACKAGE`/`SERVICE`).
  - `GET /api/product-service-names`: Returns service name records.
  - `POST /api/upload-file`: Accepts a `.xlsx` file, extracts product listings via `xlsx`, and cleans up files.
  - `POST /api/filter-existing-leads` & `POST /api/save-leads`.

### ⚡ Pipeline Modules (`src/lib/`)
- [productAnalyzer.ts](file:///d:/Disposal%20Agent/Lead_Generation_Agent/src/lib/productAnalyzer.ts): Calls `claude-haiku-4-5` with product characteristics.
- [searchService.ts](file:///d:/Disposal%20Agent/Lead_Generation_Agent/src/lib/searchService.ts): Connects to `google.serper.dev/search` to retrieve the top 15 results (both organic listings and local maps places). Normalizes domains for deduplication.
- [leadExtractor.ts](file:///d:/Disposal%20Agent/Lead_Generation_Agent/src/lib/leadExtractor.ts): Formats search result snippets and instructs Claude to output structured JSON data based on strictly verified text.
- [leadEnricher.ts](file:///d:/Disposal%20Agent/Lead_Generation_Agent/src/lib/leadEnricher.ts): Processes leads concurrently in small batches, triggering targeted queries (e.g. site domains plus contact terms) to find missing items.
- [leadValidator.ts](file:///d:/Disposal%20Agent/Lead_Generation_Agent/src/lib/leadValidator.ts): Ensures each lead contains a valid domain structure and scrubs common test keywords (e.g., `dummy.com`, `example.com`, `xxx`, `12345`).
- [db.ts](file:///d:/Disposal%20Agent/Lead_Generation_Agent/src/lib/db.ts): Instantiates a `pg` database connection pool. Builds dynamic SQL update statements for partial record syncing based on company name, email, or domain overlaps.

---

## 🗄️ Database Schema

The PostgreSQL database (configured via `DATABASE_URL`) holds a `public.leads` table and a `public.product_services` table:

```sql
-- public.leads table (Structured Lead Storage)
CREATE TABLE IF NOT EXISTS public.leads (
    id SERIAL PRIMARY KEY,
    name text,
    title text,
    company text,
    email text,
    phone text,
    website text,
    location text,
    linkedin text,
    segment text,
    priority text,
    channel text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    verified boolean DEFAULT true
);

-- public.product_services table (Target Dropdown Feeds)
CREATE TABLE IF NOT EXISTS public.product_services (
    id SERIAL PRIMARY KEY,
    category_type text,        -- 'PACKAGE' or 'SERVICE'
    product_service_type text, -- Software, Consulting, Maintenance, etc.
    product_service_name text  -- Specific names like 'Basic Package', 'IT Strategy', etc.
);
```

---

## ⚙️ Configuration & Environment Variables

Create a `.env` or `.env.local` file in the root directory to store credentials:

```ini
# Server Port
PORT=8000

# Database URL
DATABASE_URL=postgres://postgres:root@localhost:5432/Lead_DB

# Search Engine API
SERPER_API_KEY=your_serper_api_key_here

# LLM Providers (API Keys)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
XAI_API_KEY=your_xai_api_key_here
```

---

## 🚀 Running the App

### 1. Install Dependencies
```bash
npm install
```

### 2. Run Locally (Concurrently starts Vite Dev Server & Express Backend)
```bash
npm run dev
```
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

### 3. Alternate Python Backend (FastAPI)
If desired, install Python dependencies and run `main.py` directly:
```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
