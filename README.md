# DataPilot AI

**Upload. Ask. Analyze. Understand.**

DataPilot AI is an AI-powered data analysis platform that transforms raw CSV datasets into meaningful, actionable insights through natural-language queries.

It enables users to analyze data simply by uploading a CSV file and asking questions in plain English, without requiring Python, SQL, or advanced spreadsheet skills.

## Live Application

- **Project URL:** http://65.20.95.233
- **Platform:** Vultr Cloud Compute

## How We Used Vultr

DataPilot AI is built and deployed using Vultr infrastructure and AI services.

- **Vultr Cloud Compute:** A Vultr virtual machine hosts the backend and frontend in a production environment.
- **Vultr AI Inference:** Powers natural-language understanding and Python code generation.
- **DeepSeek Model:** `deepseek-v4.1-flash-1017` interprets user questions and generates data analysis code through Vultr AI Inference.
- **Docker Sandbox:** AI-generated Python code runs inside an isolated Docker container, separate from the main application environment.
- **Nginx:** Delivers the frontend and routes API requests to the backend.

Vultr provides the cloud infrastructure and AI inference capabilities that power DataPilot AI.

## Data Pipeline

1. **CSV Upload:** The user uploads a dataset to the platform.
2. **Data Processing:** The backend validates the CSV and prepares the dataset for analysis.
3. **Natural Language Query:** The user asks a question about the uploaded data.
4. **AI Understanding:** DeepSeek, accessed through Vultr AI Inference, interprets the user's request.
5. **Python Code Generation:** The AI generates Python code based on the user's analytical requirements.
6. **Code Validation:** The backend validates the generated code before execution.
7. **Sandbox Execution:** The code runs inside an isolated Docker environment using Python and Pandas.
8. **Result Processing:** Structured analysis results, statistics, and chart data are returned to the application.
9. **Visualization:** The frontend displays understandable insights, tables, statistics, and relevant charts.

## Key Features

- CSV dataset upload and analysis
- Natural-language analytics in simple English
- AI-powered Python code generation using DeepSeek via Vultr AI Inference
- Isolated code execution inside a Docker sandbox
- Dynamic calculations based on dataset columns and user questions
- Statistical insights including totals, averages, rankings, comparisons, and aggregations
- Interactive visualizations with relevant charts and graphs
- Readable analytical results
- Responsive web interface

## Technology Stack

| Category | Technologies |
| --- | --- |
| Frontend | React.js, TypeScript, Vite |
| Backend | Python, FastAPI |
| AI Inference | Vultr AI Inference |
| AI Model | DeepSeek V4.1 Flash (`deepseek-v4.1-flash-1017`) |
| Data Analysis | Python, Pandas, NumPy |
| Code Execution | Docker |
| Web Server | Nginx |
| Cloud Infrastructure | Vultr Cloud Compute |
| API Communication | REST API |

## Application Architecture

```text
React Frontend
    -> FastAPI Backend
    -> Vultr AI Inference (DeepSeek)
    -> Code Validation
    -> Docker Sandbox
    -> Pandas Analysis
    -> Structured Results
    -> Interactive Visualizations
```

## Project Structure

```text
.
├── backend/       # FastAPI API, AI integration, validation, and sandbox execution
├── frontend/      # React + TypeScript web application
├── planning/      # Project planning documents
└── README.md
```

## Local Development

### Prerequisites

- Python 3.12 or newer
- Node.js 18 or newer
- Docker
- A Vultr AI Inference API key
- Firebase credentials for authentication

### Backend

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Update `backend/.env` with the required deployment values before starting the backend.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend development server runs on the Vite default port, usually `http://localhost:5173`.

### Production Build

```bash
cd frontend
npm run build
```

For production deployments, Nginx serves the frontend build and proxies API requests to FastAPI.

## Security

Environment files and Firebase service-account JSON credentials are intentionally excluded from version control. Never commit API keys, private credentials, or other secrets. Use `backend/.env.example` as the configuration template.

## Project Vision

Our vision is to make data analytics accessible to everyone by removing the technical barriers associated with traditional data analysis.

DataPilot AI transforms the way people interact with data: instead of writing code or complex queries, users can simply ask questions and explore their datasets through AI-powered analysis.

**DataPilot AI — Upload. Ask. Analyze. Understand.**
