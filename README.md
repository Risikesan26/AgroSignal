# 🌾 AgroSignal AI: Next-Gen Agricultural Intelligence
[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-Visit_Site-blue?style=for-the-badge)](https://agrosignal-583139806956.us-central1.run.app/)
[![🎥 Video Demo](https://img.shields.io/badge/🎥_Video_Demo-Watch_Now-red?style=for-the-badge)](https://youtu.be/7oj0pwFyWrk)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=flat&logo=google-cloud&logoColor=white)](https://cloud.google.com/)
[![Gemini](https://img.shields.io/badge/Gemini-AI-orange)](https://deepmind.google/technologies/gemini/)

**AgroSignal** is a state-of-the-art agricultural market analysis and planning platform. It leverages a multi-agent AI architecture to provide Malaysian farmers with real-time, grounded insights into market trends, pricing, and strategic logistics.

---

## 🧠 Intelligence Architecture

Our platform is built on a "Brain & Orchestration" model using the latest Google Cloud AI innovations:

### 1. The Intelligence (The Brain)
Powered by **Gemini (Flash for speed/low-latency or Pro for complex reasoning)**. 
- **Gemini Flash**: Optimized for rapid user interactions and real-time market updates.
- **Gemini Pro**: Leveraged for deep strategic analysis, multi-step market forecasting, and complex reasoning tasks.

### 2. The Orchestrator
We utilize **Vertex AI Agent Builder** for building sophisticated Agentic AI workflows. The system coordinates multiple sub-agents to handle specific domains:
- **Market Analyzers**: Tracking price volatility and trade flows across Malaysian states.
- **Strategic Planners**: Providing actionable, step-by-step selling plans for farmers.

### 3. The Context (Grounded RAG)
AgroSignal implements grounded Retrieval-Augmented Generation (RAG) using **Vertex AI Search**. Our models are grounded in:
- National agricultural datasets (e.g., FAMA price records).
- Industrial market reports and regional seasonal data.
- Real-time global trade information.

### 4. The Development Lifecycle
- **Development**: Built and optimized using **Google Antigravity**, the advanced AI-powered coding environment for agentic systems.
- **Deployment**: Hosted on **Google Cloud Run**, providing a serverless, highly available environment that scales automatically to meet market demands.

---

## 🚀 Key Features

- **📍 Intelligent Market Matching**: Automatically calculates the best state/region to sell crops based on net profit (Price - Transport Cost).
- **🤖 Agentic Advisor**: A Gemini-powered conversational assistant that can explain complex market dynamics and generate tailored PDF selling plans.
- **📊 Real-time Data Visualization**: Interactive maps and demand charts powered by live FAMA datasets.
- **🌦️ Weather & Seasonal Risk**: Integrated assessments of monsoon risks and seasonal crop cycles for Malaysia.
- **🚛 Logistics Optimization**: Calculates transport costs across all 16 Malaysian states/territories to ensure profitable trade.

---

## 🛠️ Getting Started

### Prerequisites
- **Python 3.11+**
- **Google Cloud Project** with Vertex AI and Cloud Run enabled.
- **Gemini API Key** (or Vertex AI credentials).
- **FAMA Dataset** (provided in `./data/fama_prices.csv`).

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/AgroSignal.git
   cd AgroSignal
   ```

2. **Set up Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   GOOGLE_MAPS_API_KEY=your_maps_key
   FAMA_CSV_PATH=./data/fama_prices.csv
   PROJECT_ID=your-gcp-project-id
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python main.py
   # or
   uvicorn main.py:app --reload
   ```

---

## 🚢 Deployment

Deploy to **Google Cloud Run** using the provided `Dockerfile`:

```bash
gcloud builds submit --tag gcr.io/[PROJECT_ID]/agrosignal
gcloud run deploy agrosignal --image gcr.io/[PROJECT_ID]/agrosignal --platform managed
```

---

## 🌐 Vision

AgroSignal aims to democratize access to elite market intelligence, empowering small-scale farmers with the same data-driven insights used by global agricultural conglomerates.

---

*Developed with ❤️ using Google Cloud Vertex AI and Antigravity.*
