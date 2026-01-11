# VerTac Development Guide

## Project Overview

VerTac is a cycle-based monitoring and analysis platform designed for small factories and technical environments. The system analyzes historical multi-sensor datasets organized into distinct cycles.

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLAlchemy with SQLite/PostgreSQL
- **Data Processing**: Pandas, NumPy, SciPy
- **API Documentation**: Auto-generated Swagger/OpenAPI

### Frontend
- **Framework**: React with TypeScript
- **Routing**: React Router
- **Charts**: Plotly.js
- **Styling**: CSS Modules
- **HTTP Client**: Axios

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database:
```bash
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

6. Run the server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
echo "REACT_APP_API_URL=http://localhost:8000/api/v1" > .env
```

4. Start development server:
```bash
npm start
```

The application will open at `http://localhost:3000`

## Project Structure

```
VerTac/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core configuration
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic
│   ├── main.py          # Application entry
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API services
│   │   └── types/       # TypeScript types
│   └── package.json
└── README.md
```

## Core Features

### 1. Dataset Management
- Upload multi-sensor datasets (CSV, Excel, Parquet)
- Automatic cycle extraction
- Dataset metadata tracking

### 2. Cycle Analysis
- View individual cycles with sensor data
- Set reference cycles
- Compare cycles against reference
- Identify deviations

### 3. Deviation Detection
- Shape deviation detection
- Amplitude deviation detection
- Timing deviation detection
- Severity scoring

### 4. Anomaly Detection
- Automated anomaly identification
- Health score calculation
- Actionable recommendations

### 5. Root Cause Analysis
- Trace deviations before abnormal stops
- Rank contributing sensors
- Generate root cause reports

## API Endpoints

### Datasets
- `POST /api/v1/datasets/upload` - Upload dataset
- `GET /api/v1/datasets/` - List datasets
- `GET /api/v1/datasets/{id}` - Get dataset
- `DELETE /api/v1/datasets/{id}` - Delete dataset

### Cycles
- `GET /api/v1/cycles/dataset/{dataset_id}` - List cycles
- `GET /api/v1/cycles/{id}` - Get cycle detail
- `POST /api/v1/cycles/{id}/set-reference` - Set reference
- `GET /api/v1/cycles/{id}/sensors` - Get sensors

### Analysis
- `GET /api/v1/analysis/cycle/{id}/deviations` - Analyze deviations
- `GET /api/v1/analysis/dataset/{id}/anomalies` - Detect anomalies
- `GET /api/v1/analysis/cycle/{id}/root-cause` - Root cause analysis

## Data Format

### Expected Dataset Structure

Datasets should contain:
- **Time column**: `time` or `timestamp`
- **Cycle identifier**: `cycle`, `cycle_id`, or `cycle_number`
- **Sensor columns**: Numeric columns representing sensor measurements

Example CSV:
```csv
time,cycle,sensor1,sensor2,sensor3
0.0,1,10.5,20.3,5.1
0.1,1,10.6,20.4,5.2
...
```

## Development

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Code Style
- Backend: Follow PEP 8
- Frontend: ESLint + Prettier configuration

## Deployment

### Backend Deployment
1. Set production environment variables
2. Use PostgreSQL for production database
3. Use gunicorn or uvicorn with multiple workers
4. Set up reverse proxy (nginx)

### Frontend Deployment
1. Build production bundle:
```bash
cd frontend
npm run build
```
2. Serve static files with nginx or CDN

## Contributing

1. Create feature branch
2. Make changes with tests
3. Submit pull request

## License

MIT License
