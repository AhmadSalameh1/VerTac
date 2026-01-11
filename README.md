# VerTac - Cycle-Based Monitoring Platform

A lightweight, web-based monitoring and analysis platform for small factories and technical environments where machines, test benches, or processes operate through repeated runs.

## Overview

VerTac is designed to analyze historical multi-sensor datasets organized into distinct cycles. The platform provides:

- **Cycle-centric analysis**: Each dataset is organized into distinct cycles treated as first-class entities
- **Automated comparisons**: Compares each cycle against a reference cycle and the preceding cycle
- **Deviation detection**: Identifies abnormal behavior in signal shape, timing, amplitude, or overall behavior
- **Root cause analysis**: For abnormal terminations, traces and ranks sensor deviations leading up to the stop
- **Synchronized visualization**: Time-series graphs for multi-sensor data
- **Operator-friendly**: Designed for maintenance technicians with explainability and ease of use

## Technology Stack

- **Backend**: Python FastAPI
- **Frontend**: React with TypeScript
- **Data Processing**: Pandas, NumPy, SciPy
- **Visualization**: Plotly.js
- **Database**: SQLite (development) / PostgreSQL (production)

## Project Structure

```
VerTac/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── data/            # Sample datasets
├── docs/            # Documentation
└── tests/           # Test suites
```

## Getting Started

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

## Features

- Import and parse multi-sensor datasets
- Organize data into cycles
- Define reference cycles
- Automated cycle comparison
- Deviation detection and alerting
- Root cause analysis for abnormal stops
- Synchronized time-series visualization
- Lightweight and accessible web interface

## License

MIT
