# DataPilot AI — Project Context & Implementation Record

> **IMPORTANT FOR FUTURE SESSIONS:**
> Read this file completely before touching any code.
> This is the ground truth for what has been built, what is in progress, and what comes next.
> The specification is `planning/docs/doc.txt`. This file is the implementation record.
> Last Updated: Phase 1 — Project Understanding & Planning

---


## A. PROJECT UNDERSTANDING

### Purpose
DataPilot AI is an AI-powered autonomous data analysis platform. Users upload CSV datasets and interact with them through natural language. The platform generates Python analysis code via AI, executes it in a secure Docker sandbox, and returns insights, statistics, and dynamic visualizations — without the user ever writing code.

### Vision
Make advanced data analysis accessible to non-technical users. A business analyst, product manager, or researcher should be able to upload a CSV and immediately get meaningful insights, trend analysis, outlier detection, and professional charts — just by describing what they want in plain English.

### Target Users
- Business analysts working with sales/marketing data
- Product managers analyzing user metrics
- Researchers processing survey or experimental data
- Data-curious non-programmers who understand their domain but not Python
- Students learning data analysis concepts

### Problems Solved
| Problem | Solution |
|---|---|
| Data analysis requires Python knowledge | AI generates the code automatically |
| Code execution is risky on shared servers | Docker sandbox isolates every execution |
| Generic charts don't match the actual question | AI picks chart types based on data and request |
| Analysis tools are complex to set up | Web-based platform, zero local installation |
| Sharing analysis results is hard | Analysis history stored and accessible |

### Complete End-to-End Workflow
```
1. User authenticates (Firebase Auth — email/password or Google)
2. User uploads CSV file
   └── Backend validates: format, size, encoding, structure
   └── Metadata extracted: columns, dtypes, shape, null counts, basic stats
   └── Preview generated: first 10 rows
3. User types natural language analysis request
   └── e.g. "Show me sales trends by month and identify the top performing categories"
4. Backend builds AI prompt
   └── Includes: dataset metadata + column names + dtypes + sample rows + user request
5. Vultr Serverless Inference generates Python code
   └── Code uses pandas/numpy to analyze the CSV
   └── Code outputs JSON to stdout (structured result schema)
6. Backend validates the generated code
   └── Syntax check (ast.parse)
   └── Safety scan (blocked imports/functions)
7. Backend sends code + CSV to Docker sandbox
   └── Fresh container created per run
   └── CSV mounted as read-only at /data/input.csv
   └── Resource limits applied (CPU, RAM, PIDs, network disabled)
   └── 30-second execution timeout
8. Sandbox executes analysis
   └── runner.py wraps the AI code
   └── Captures stdout (JSON result) and stderr (errors)
9. Results returned to backend
   └── Backend parses JSON output
   └── Validates result schema
   └── Extracts: insights text, statistics, chart data arrays
10. If execution failed:
    └── Error message sent back to AI (controlled context)
    └── AI generates corrected code
    └── Retry attempted (max 3 retries)
    └── After 3 failures: return graceful error to user
11. Frontend displays results
    └── Insight text (AI-generated explanation)
    └── Statistics table
    └── Dynamic charts (1 to N charts based on analysis)
    └── Execution metadata (time, retry count)
12. Analysis saved to Firestore
    └── Linked to user ID + dataset ID
    └── Accessible in Analysis History
```

---

## B. TECHNOLOGY STACK

### Frontend
| Technology | Version | Responsibility |
|---|---|---|
| React | 18+ | UI framework |
| TypeScript | 5+ | Type safety |
| Vite | 5+ | Build tool, dev server |
| Tailwind CSS | 3+ | Styling (utility-first, design system enforcement) |
| Recharts | 2+ | All 12 chart types — bar, line, area, pie, scatter, etc. |
| Axios | 1+ | HTTP client, interceptors for auth tokens |
| Zustand | 4+ | Global state management (auth state, dataset state, analysis state) |
| React Router | 6+ | Client-side routing |
| Firebase JS SDK | 10+ | Authentication (client-side token management) |

### Backend
| Technology | Version | Responsibility |
|---|---|---|
| Python | 3.11+ | Language |
| FastAPI | 0.110+ | REST API framework |
| Uvicorn | 0.29+ | ASGI server |
| Pydantic | v2 | Request/response validation, settings management |
| firebase-admin | 6+ | Server-side Firebase JWT verification |
| openai SDK | 1+ | HTTP client for Vultr Serverless Inference (base_url override) |
| docker SDK | 7+ | Programmatic Docker container management |
| pandas | 2+ | CSV parsing, metadata extraction |
| chardet | 5+ | CSV encoding detection |
| python-multipart | — | File upload handling |
| aiofiles | — | Async file I/O |
| python-dotenv | — | .env file loading |

### AI / Inference
| Item | Detail |
|---|---|
| Provider | Vultr Serverless Inference |
| Access | OpenAI-compatible REST API |
| SDK | openai Python SDK with `base_url` set to Vultr endpoint |
| Credentials | Backend only — never in frontend, never in sandbox |
| Model | To be confirmed after Vultr account inspection (likely a Llama 3.x variant) |
| Usage | Code generation + error correction |

### Sandbox
| Item | Detail |
|---|---|
| Technology | Docker |
| Base image | python:3.11-slim |
| Installed libs | pandas, numpy, scipy, json (stdlib) |
| Execution user | uid 1000 (non-root) |
| CPU limit | 0.5 cores |
| Memory limit | 256 MB |
| PID limit | 50 processes |
| Network | Disabled (`--network none`) |
| Timeout | 30 seconds hard limit |
| Input | CSV file mounted read-only at `/data/input.csv` |
| Output | JSON written to stdout by the analysis code |
| Cleanup | Container auto-removed after execution (`--rm`) |

### Authentication
| Item | Detail |
|---|---|
| Provider | Firebase Authentication |
| Methods | Email/Password, Google OAuth |
| Token type | Firebase ID Token (JWT) |
| Verification | Backend verifies every protected request via firebase-admin |
| Frontend | Firebase JS SDK handles login/logout/token refresh |

### Storage
| Item | Phase | Technology |
|---|---|---|
| Temporary CSV files | All phases | Local filesystem (`/tmp/datapilot/<uuid>/`) |
| Analysis history | Phase 2+ | Firebase Firestore |
| Dataset metadata | Phase 2+ | Firebase Firestore |
| Persistent CSV storage | Phase 11 | Vultr Object Storage (S3-compatible) |

### Deployment (Target — Phase 11)
| Component | Platform |
|---|---|
| Backend | Vultr Cloud Compute VM (Ubuntu 22.04) |
| Frontend | Vultr Object Storage (static hosting) or same VM via nginx |
| AI Inference | Vultr Serverless Inference (managed) |
| Docker | Installed on the same Vultr VM as backend |

---

## C. ARCHITECTURE

### System Communication Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                          USER BROWSER                           │
│                     React + TypeScript + Vite                   │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTPS REST API
                               │ (Bearer: Firebase ID Token)
┌──────────────────────────────▼──────────────────────────────────┐
│                        FASTAPI BACKEND                          │
│                    Python 3.11 + Uvicorn                        │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │   Routers   │  │   Services   │  │       Models           │ │
│  │  auth.py    │  │ ai_service   │  │  dataset.py            │ │
│  │  datasets   │  │ sandbox_svc  │  │  analysis.py           │ │
│  │  analysis   │  │ dataset_svc  │  │  user.py               │ │
│  └─────────────┘  │ firebase_svc │  └────────────────────────┘ │
│                   └──────────────┘                              │
└──────┬───────────────────┬────────────────────┬────────────────┘
       │                   │                    │
       ▼                   ▼                    ▼
┌─────────────┐  ┌──────────────────┐  ┌───────────────────────┐
│  FIREBASE   │  │  VULTR           │  │  DOCKER SANDBOX       │
│             │  │  SERVERLESS      │  │                       │
│  Auth       │  │  INFERENCE       │  │  python:3.11-slim     │
│  Firestore  │  │                  │  │  + pandas + numpy     │
│             │  │  (OpenAI-compat) │  │                       │
│  JWT verify │  │  Code generation │  │  --network none       │
│  User data  │  │  Error recovery  │  │  --cpus 0.5           │
│  Analysis   │  │                  │  │  --memory 256m        │
│  history    │  │  base_url =      │  │  --pids-limit 50      │
│             │  │  Vultr endpoint  │  │  --user 1000          │
└─────────────┘  └──────────────────┘  │  --read-only          │
                                       │  timeout: 30s         │
                                       └───────────────────────┘
```

### Data Flow — Analysis Request
```
Frontend                    Backend                      Sandbox
   │                           │                            │
   │── POST /analysis/run ──►  │                            │
   │   {dataset_id, prompt}    │                            │
   │                           │── validate token ──► Firebase
   │                           │                            │
   │                           │── load CSV metadata        │
   │                           │── build AI prompt          │
   │                           │── POST to Vultr AI ──────► Vultr Inference
   │                           │◄── Python code ────────────│
   │                           │                            │
   │                           │── validate code (ast + safety scan)
   │                           │── create temp dir /tmp/datapilot/<uuid>/
   │                           │── docker run (with CSV mount)──► Sandbox
   │                           │                            │── execute code
   │                           │                            │── stdout: JSON
   │                           │◄── stdout JSON ────────────│
   │                           │── parse & validate result  │
   │                           │── save to Firestore        │
   │                           │── cleanup temp dir         │
   │◄── 200 {result JSON} ─────│                            │
   │                           │                            │
   │── render charts & insights│                            │
```

### Sandbox Output JSON Schema
```json
{
  "success": true,
  "insights": "Text explanation of findings...",
  "statistics": {
    "key_metric_name": "value",
    "another_metric": 123.45
  },
  "charts": [
    {
      "type": "bar",
      "title": "Sales by Category",
      "x_label": "Category",
      "y_label": "Total Sales ($)",
      "data": [
        {"name": "Electronics", "value": 45000},
        {"name": "Clothing", "value": 32000}
      ]
    },
    {
      "type": "line",
      "title": "Monthly Revenue Trend",
      "x_label": "Month",
      "y_label": "Revenue ($)",
      "data": [
        {"name": "Jan", "value": 12000},
        {"name": "Feb", "value": 15000}
      ]
    }
  ],
  "error": null
}
```

---

## D. FOLDER STRUCTURE

### Current State (Phase 1 — Planning Only)
```
datapilot-ai/  (D:\Vultr Rush Hackathon lablab.ai DataPilot AI\)
└── planning/
    └── docs/
        ├── doc.txt        ✅ Created — complete project specification
        └── context.md     ✅ This file — implementation record
```

### Target Structure (Full — Phases 2–9)
```
datapilot-ai/
├── planning/
│   └── docs/
│       ├── doc.txt
│       └── context.md
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, middleware, startup
│   │   ├── config.py                # Pydantic Settings — env vars
│   │   ├── dependencies.py          # get_current_user, get_db, etc.
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # POST /auth/verify
│   │   │   ├── datasets.py          # POST /datasets/upload, GET /datasets, DELETE /datasets/{id}
│   │   │   └── analysis.py          # POST /analysis/run, GET /analysis/history
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py        # Vultr inference client, prompt builder, code extractor
│   │   │   ├── sandbox_service.py   # Docker run, timeout, cleanup, output parse
│   │   │   ├── dataset_service.py   # CSV validation, metadata extraction, encoding detection
│   │   │   └── firebase_service.py  # firebase-admin init, token verification
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── dataset.py           # DatasetUploadResponse, DatasetMetadata, DatasetInfo
│   │   │   ├── analysis.py          # AnalysisRequest, AnalysisResult, ChartData, ExecutionResult
│   │   │   └── user.py              # UserInfo, AuthenticatedUser
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── code_validator.py    # AST parse + blocked pattern scanner
│   │       └── file_utils.py        # UUID temp dir create/cleanup, safe path helpers
│   ├── sandbox/
│   │   ├── Dockerfile               # python:3.11-slim, install libs, create uid 1000 user
│   │   └── runner.py                # Wraps AI code, enforces JSON stdout, catches exceptions
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_upload.py
│   │   ├── test_analysis.py
│   │   └── test_sandbox.py
│   ├── .env.example                 # Template — never commit actual .env
│   ├── requirements.txt
│   └── Dockerfile                   # Backend container for production deployment
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx                  # Routes + Auth guard
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx      # Nav links, responsive collapse
│   │   │   │   ├── Header.tsx       # User info, mobile menu toggle
│   │   │   │   └── Layout.tsx       # Sidebar + Header + outlet
│   │   │   ├── upload/
│   │   │   │   └── CSVUpload.tsx    # Drag-drop + click upload, progress, validation feedback
│   │   │   ├── analysis/
│   │   │   │   ├── AnalysisInput.tsx     # Natural language textarea + submit
│   │   │   │   ├── AnalysisResult.tsx    # Insights + stats + charts display
│   │   │   │   └── ExecutionHistory.tsx  # Past runs for current dataset
│   │   │   ├── charts/
│   │   │   │   ├── ChartRenderer.tsx     # Reads chart.type, routes to correct component
│   │   │   │   └── chartTypes/
│   │   │   │       ├── BarChartView.tsx
│   │   │   │       ├── LineChartView.tsx
│   │   │   │       ├── AreaChartView.tsx
│   │   │   │       ├── PieChartView.tsx
│   │   │   │       ├── ScatterChartView.tsx
│   │   │   │       ├── HistogramView.tsx
│   │   │   │       ├── HeatmapView.tsx
│   │   │   │       └── BoxPlotView.tsx
│   │   │   └── common/
│   │   │       ├── Button.tsx
│   │   │       ├── Card.tsx
│   │   │       ├── LoadingSpinner.tsx
│   │   │       ├── EmptyState.tsx
│   │   │       └── ErrorBoundary.tsx
│   │   ├── pages/
│   │   │   ├── auth/
│   │   │   │   ├── Login.tsx
│   │   │   │   └── Register.tsx
│   │   │   ├── Overview.tsx         # Stats cards, recent analyses, quick actions
│   │   │   ├── NewAnalysis.tsx      # Upload + analysis workspace combined
│   │   │   ├── MyDatasets.tsx       # Dataset list, metadata, delete
│   │   │   ├── AnalysisHistory.tsx  # All past analyses, filterable
│   │   │   └── Settings.tsx         # User profile, API key display (future)
│   │   ├── services/
│   │   │   ├── api.ts               # Axios instance, request/response interceptors
│   │   │   └── firebase.ts          # Firebase app init, auth instance export
│   │   ├── hooks/
│   │   │   ├── useAuth.ts           # Login, logout, register, current user
│   │   │   ├── useDataset.ts        # Upload, list, delete datasets
│   │   │   └── useAnalysis.ts       # Run analysis, fetch history
│   │   ├── store/
│   │   │   ├── authStore.ts         # Zustand: user, token, loading
│   │   │   ├── datasetStore.ts      # Zustand: datasets list, active dataset
│   │   │   └── analysisStore.ts     # Zustand: current result, history, loading state
│   │   └── types/
│   │       ├── dataset.ts
│   │       ├── analysis.ts
│   │       └── auth.ts
│   ├── public/
│   │   └── favicon.ico
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
│
├── .gitignore
└── README.md
```

---

## E. DEVELOPMENT PROGRESS

### Phase Status Overview
| Phase | Name | Status |
|---|---|---|
| 1 | Project Understanding & Planning | ✅ COMPLETED |
| 2 | Project Foundation | ✅ COMPLETED |
| 3 | Dataset Management | ✅ COMPLETED |
| 4 | Vultr AI Integration | ✅ COMPLETED |
| 5 | Docker Sandbox | ✅ COMPLETED |
| 6 | Data Analysis Engine | ✅ COMPLETED (runs in sandbox) |
| 7 | Dynamic Visualization | ✅ COMPLETED (AI picks charts) |
| 8 | AI Error Recovery | ✅ COMPLETED (retry loop) |
| 3 | Dataset Management | ⏳ PENDING |
| 4 | Vultr AI Integration | ⏳ PENDING |
| 5 | Docker Sandbox | ⏳ PENDING |
| 6 | Data Analysis Engine | ⏳ PENDING |
| 7 | Dynamic Visualization | ⏳ PENDING |
| 8 | AI Error Recovery | ⏳ PENDING |
| 9 | Dashboard & UX | ⏳ PENDING |
| 10 | Security & Testing | ⏳ PENDING |
| 11 | Vultr Deployment | ⏳ PENDING |
| 12 | Hackathon Submission | ⏳ PENDING |

### Completed Tasks
- [x] Created `planning/docs/` directory
- [x] Created `planning/docs/doc.txt` (complete specification)
- [x] Analyzed all requirements, architecture, and technical challenges
- [x] Created `planning/docs/context.md` (this file)

### In Progress
- Nothing currently in implementation

### Pending (Next up — Phase 2)
- Backend project scaffold (FastAPI, folder structure, requirements.txt)
- Frontend project scaffold (React + Vite + TypeScript + Tailwind)
- Environment configuration (.env.example)
- Firebase project setup instructions
- Basic health check API

### Blocked
- Vultr Serverless Inference model slug — need to verify available models in Vultr console
- Firebase project credentials — need to create Firebase project and download service account key

---

## F. IMPLEMENTATION DETAILS

### Feature: Project Documentation & Planning
- **Status:** Complete
- **Files Created:**
  - `planning/docs/doc.txt` — full specification
  - `planning/docs/context.md` — this file
- **Files Modified:** None
- **Dependencies:** None
- **Testing Status:** N/A (planning phase)

---

## G. SECURITY IMPLEMENTATION

> Nothing implemented yet. Security features will be recorded here as they are built and verified.

### Planned Security Controls (to be checked off when implemented + tested)
- [ ] Firebase JWT verification on all protected endpoints
- [ ] User ownership check before serving dataset files
- [ ] CSV upload validation (MIME type, extension, size limit, content check)
- [ ] AI-generated code syntax validation (ast.parse)
- [ ] AI-generated code safety scan (blocked imports: os, sys, subprocess, socket, shutil)
- [ ] Docker sandbox: non-root user (uid 1000)
- [ ] Docker sandbox: `--network none`
- [ ] Docker sandbox: `--cpus 0.5`
- [ ] Docker sandbox: `--memory 256m`
- [ ] Docker sandbox: `--pids-limit 50`
- [ ] Docker sandbox: `--read-only` root filesystem
- [ ] Docker sandbox: 30-second execution timeout with forced kill
- [ ] Docker sandbox: automatic container removal after use (`--rm`)
- [ ] Temporary file cleanup on success, failure, and timeout
- [ ] No credentials in sandbox environment
- [ ] No Docker socket mounted in sandbox
- [ ] CORS restricted to frontend domain in production
- [ ] Rate limiting on analysis endpoint
- [ ] .env files in .gitignore

---

## H. CURRENT DEVELOPMENT STATE

### Working Features
- Project documentation exists and is complete
- Project structure is defined and understood

### Incomplete Features
- Everything application-related (Phase 2–12 not started)

### Known Issues / Bugs
- None yet (no code written)

### Configuration Requirements Before Phase 2 Starts
1. **Firebase Project:**
   - Create a Firebase project at https://console.firebase.google.com
   - Enable Authentication (Email/Password + Google)
   - Enable Firestore Database
   - Download service account JSON key → save as `backend/firebase-service-account.json` (gitignored)
   - Copy web app config → used in `frontend/src/services/firebase.ts`

2. **Vultr Account:**
   - Confirm Vultr Serverless Inference is enabled
   - Get the inference API key and base URL
   - Identify available model slugs (check Vultr console → AI → Serverless Inference)
   - Save API key in `backend/.env` as `VULTR_INFERENCE_API_KEY`

3. **Docker:**
   - Docker Desktop (Windows dev) or Docker Engine (Linux VM)
   - Must be running before starting backend

4. **Node.js:**
   - v20+ required for Vite + React

5. **Python:**
   - 3.11+ required

### Pending Integrations
- Firebase (not set up)
- Vultr Serverless Inference (not configured)
- Docker sandbox image (not built)

### Current Development Phase
**Phase 1 — Complete**
**Next Phase: Phase 2 — Project Foundation**

### Exact Next Task
> **START HERE IN NEXT SESSION:**
> Begin Phase 2 — Project Foundation.
> Task 2.1: Scaffold the backend — create `backend/` folder structure, `requirements.txt`, `app/main.py` with FastAPI app skeleton, `app/config.py` with Pydantic Settings, `.env.example`, and `.gitignore`.
> Task 2.2: Scaffold the frontend — create React + Vite + TypeScript project in `frontend/`, configure Tailwind CSS, set up folder structure.
> Task 2.3: Basic API health check endpoint (`GET /health`).
> Task 2.4: CORS configuration.
> Do NOT start Phase 3 until Phase 2 scaffold is complete and running locally.

---

## I. ARCHITECTURAL DECISIONS

### Decision 1: Recharts over Chart.js for Frontend
**Decision:** Use Recharts as the charting library.
**Reasoning:**
- Recharts is React-native (components, not imperative API)
- Better TypeScript support than Chart.js
- Supports all 12 required chart types
- Composable API makes dynamic chart rendering easier
- Active maintenance, good documentation
- Lighter integration with React state

### Decision 2: Zustand over Redux for State Management
**Decision:** Use Zustand for global state.
**Reasoning:**
- DataPilot has moderate state complexity (auth, datasets, analysis results)
- Zustand requires ~80% less boilerplate than Redux
- Simpler DevEx for a hackathon timeline
- Easy to migrate to Redux later if complexity grows
- Works well with TypeScript

### Decision 3: Sandbox Output via stdout JSON, not Files
**Decision:** AI-generated code writes results as JSON to stdout. Backend reads stdout from docker container logs.
**Reasoning:**
- Eliminates a file-system escape vector (no output files to read from container)
- Simpler container lifecycle (no volume mounts for output)
- JSON on stdout is a clean, auditable protocol
- Docker SDK `container.logs()` is reliable and synchronous after container stops

### Decision 4: Backend Directly on VM (not containerized in production)
**Decision:** In production, run the FastAPI backend directly on the Vultr VM (not inside a Docker container).
**Reasoning:**
- If the backend is inside a container, it needs Docker-in-Docker (DinD) or Docker socket mounting to spawn sandbox containers
- Mounting the Docker socket into a backend container is a major security risk (container escape → host access)
- Running backend on the VM directly and having it call the host Docker daemon is safer and simpler
- For development: run backend directly on dev machine, not containerized

### Decision 5: Firebase Firestore for Analysis History
**Decision:** Use Firestore instead of a self-managed relational database.
**Reasoning:**
- No database server to provision or manage on Vultr VM
- Firestore is already in use for Firebase Auth
- Analysis history is naturally document-structured (not relational)
- Scales automatically
- Free tier is generous for hackathon scale
- Reduces infrastructure complexity significantly

### Decision 6: Temporary File Storage in Phase 2–10, Vultr Object Storage in Phase 11
**Decision:** Use local `/tmp/datapilot/<uuid>/` directories for CSV storage during development and testing. Migrate to Vultr Object Storage only in the production deployment phase.
**Reasoning:**
- Keeps early phases simple and fast to develop
- Object Storage integration is straightforward to add later (boto3/S3-compat)
- `/tmp` files are cleaned up automatically on VM restart
- Each analysis UUID directory isolates files between concurrent requests

### Decision 7: OpenAI SDK as Vultr Inference Client
**Decision:** Use the `openai` Python SDK with `base_url` overridden to Vultr's inference endpoint.
**Reasoning:**
- Vultr Serverless Inference is OpenAI-API compatible
- This approach requires zero custom HTTP code
- If Vultr's endpoint changes, only the `base_url` config needs updating
- The SDK handles retries, timeouts, streaming, and response parsing
- **Critical:** No OpenAI API key is used. Only `VULTR_INFERENCE_API_KEY` and `VULTR_INFERENCE_BASE_URL` are set

### Decision 8: Code Validation = AST Parse + Blocklist Scan
**Decision:** Validate AI-generated code before sandbox execution using two layers:
1. `ast.parse()` — catches syntax errors immediately without executing anything
2. AST node visitor that blocks: `import os`, `import sys`, `import subprocess`, `import socket`, `import shutil`, `exec()`, `eval()`, `__import__()`, `open()` (except the pre-approved path)
**Reasoning:**
- Defense in depth: sandbox restrictions are the hard wall, code validation is the soft wall
- Catches obvious malicious patterns before they even reach Docker
- AST-based analysis is more reliable than regex for code scanning
- Allows fast-fail with a clear error message before consuming Docker resources

---

## J. TECHNICAL CHALLENGES & MITIGATIONS

### Challenge 1: Vultr Model Slug Unknown
**Risk:** Don't know the exact model name until Vultr console is inspected.
**Mitigation:** Make `VULTR_MODEL_NAME` a configurable env var. Default to a likely value like `"meta/llama-3.1-70b-instruct"`. Test and update after Vultr console inspection.

### Challenge 2: AI Code Contains Markdown Fences
**Risk:** LLM may return ` ```python ... ``` ` instead of raw code.
**Mitigation:** `ai_service.py` extracts code with a regex: strip everything before the first ` ```python ` or ` ``` ` and after the closing ` ``` `. If no fences found, treat the entire response as code.

### Challenge 3: NumPy Types Not JSON-Serializable
**Risk:** `json.dumps({"value": np.int64(5)})` raises `TypeError`.
**Mitigation:** `runner.py` uses a custom JSON encoder that converts all `numpy` scalar types to native Python types before output. Also handles `pandas.Timestamp` → ISO string.

### Challenge 4: CSV Encoding Errors
**Risk:** `pd.read_csv()` fails on non-UTF-8 files.
**Mitigation:** `dataset_service.py` tries UTF-8 first, then uses `chardet.detect()` to identify encoding, then retries with detected encoding. Falls back to `latin-1` as last resort.

### Challenge 5: Container Timeout Enforcement
**Risk:** Infinite loop in AI-generated code hangs the request forever.
**Mitigation:**
- Docker `--stop-timeout 5` (5s for graceful stop)
- Backend sets `timeout=30` on `container.wait()`
- If timeout exceeded: `container.kill()` then `container.remove(force=True)`
- Return `{"success": false, "error": "Execution timeout exceeded"}` to user

### Challenge 6: Concurrent Analysis Requests
**Risk:** Multiple users running analyses simultaneously could exhaust Docker resources.
**Mitigation:**
- Each run gets a unique UUID directory and container name
- Add a semaphore in `sandbox_service.py` to limit concurrent sandbox runs (e.g., max 5)
- Return `429 Too Many Requests` if semaphore is full
- This is acceptable for hackathon scale; proper job queue (Celery/Redis) would be Phase 2+ optimization

### Challenge 7: Large CSV Files
**Risk:** User uploads a 500MB CSV — OOM in backend, slow processing.
**Mitigation:**
- Hard upload size limit: 10MB (configurable via `MAX_CSV_SIZE_MB` env var)
- `dataset_service.py` reads only the first 100 rows for metadata/preview
- AI prompt includes only column names, dtypes, and 5 sample rows (not entire dataset)

---

## K. VULTR BUDGET PLAN

### Available: $200 USD Hackathon Credits

| Service | Estimated Cost | Notes |
|---|---|---|
| Compute VM (2 vCPU / 4GB) | ~$24/mo | Only needed for demo/testing |
| Serverless Inference | ~$0.20/1M tokens | Very cheap; hackathon usage ~$2-5 |
| Object Storage (250GB) | $5/mo | Only Phase 11 onward |
| **Estimated Total** | **~$30-40** | Leaves >$160 buffer |

### Cost Control Rules
- Shut down Vultr VM when not actively testing
- Use object storage only in Phase 11
- Monitor inference token usage — don't send full CSV contents to AI

---

*End of context.md — Update this file after every implementation session.*
