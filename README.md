# DataPilot AI

**Upload. Ask. Analyze. Understand.**

DataPilot AI is an AI-powered data analysis platform that transforms CSV files into actionable insights through natural-language queries. Users can upload datasets, ask questions in plain English, and receive AI-generated analysis, statistics, tables, and visualizations.

## Live Application

**Demo:** http://65.20.95.233

## How Vultr Was Used

Vultr powers both the application infrastructure and AI capabilities of DataPilot AI.

- **Vultr Cloud Compute:** Created and configured an Ubuntu virtual machine to host the application.
- **Application Deployment:** Deployed the frontend and backend on the Vultr server.
- **Vultr AI Inference:** Used Vultr's AI inference service to access the DeepSeek model for generating data-analysis code.
- **Docker Sandbox:** Executed AI-generated Python code inside an isolated Docker environment to reduce execution risks.
- **Nginx:** Configured as the web server and reverse proxy to serve the frontend and route API requests to the backend.

## AI Model

DataPilot AI uses **DeepSeek V4.1 Flash (`deepseek-v4.1-flash-1017`)** through Vultr AI Inference.

The model interprets users' natural-language questions and generates Python code to analyze uploaded datasets.

## Data Pipeline

1. **CSV Upload:** The user uploads a CSV dataset through the web interface.
2. **Data Validation:** The backend validates the uploaded file and prepares the dataset.
3. **Natural-Language Query:** The user asks a question about the data.
4. **AI Processing:** The backend sends the question and relevant dataset information to DeepSeek through Vultr AI Inference.
5. **Code Generation:** DeepSeek generates Python code for the requested analysis.
6. **Code Validation:** The backend validates the generated code before execution.
7. **Sandbox Execution:** The code runs inside an isolated Docker container using Python and Pandas.
8. **Results:** The application returns analysis results, statistics, tables, and visualizations to the user.

## Key Features

- Upload and analyze CSV datasets.
- Ask questions using natural language.
- AI-powered Python code generation.
- Secure, isolated Docker-based code execution.
- Automated data analysis and statistical summaries.
- Interactive charts and visualizations.
- Structured analysis results.
- User-friendly interface for non-technical users.
- Responsive web application.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| AI Model | DeepSeek V4.1 Flash |
| AI Infrastructure | Vultr AI Inference |
| Data Analysis | Pandas |
| Code Execution | Docker |
| Web Server | Nginx |
| Hosting | Vultr Cloud Compute |
| Communication | REST API |

## Project Vision

DataPilot AI aims to make data analysis accessible to everyone. Instead of writing complex Python scripts or SQL queries, users can simply upload their datasets and ask questions in natural language.

By combining Vultr Cloud Compute, Vultr AI Inference, DeepSeek, and isolated Docker execution, DataPilot AI provides an accessible and practical approach to AI-powered data analysis.
