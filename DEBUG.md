# VerTac Debug & Troubleshooting Guide

## Quick System Check

### Backend
```bash
cd backend
python validate_system.py  # Run comprehensive validation
python test_setup.py       # Test dependencies and imports
python init_db.py          # Initialize database
```

### Frontend
```bash
cd frontend
python check_setup.py      # Check frontend setup
```

## Common Issues & Fixes

### Backend Issues

#### 1. Import Errors
**Problem**: `ModuleNotFoundError` or `ImportError`

**Solution**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Database Errors
**Problem**: `sqlite3.OperationalError: no such table`

**Solution**:
```bash
cd backend
python init_db.py
```

#### 3. CORS Errors
**Problem**: Frontend can't connect to backend

**Solution**: Check `.env` file has correct CORS origins:
```env
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

#### 4. File Upload Errors
**Problem**: `FileNotFoundError` when uploading

**Solution**: Upload directory will be created automatically, but ensure write permissions

### Frontend Issues

#### 1. Module Not Found
**Problem**: `Cannot find module 'react'`

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### 2. API Connection Errors
**Problem**: `ERR_CONNECTION_REFUSED` or `Network Error`

**Solution**: 
- Ensure backend is running: `uvicorn main:app --reload`
- Check `.env` file:
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

#### 3. Build Errors
**Problem**: TypeScript compilation errors

**Solution**:
```bash
npm install --save-dev @types/react @types/react-dom @types/node
```

## System Architecture Validation

### Backend Component Check
✓ **Core Layer**
- `app/core/config.py` - Configuration management
- `app/core/database.py` - Database connection & session

✓ **Models Layer**
- `app/models/models.py` - SQLAlchemy models (Dataset, Cycle, Deviation)

✓ **Schemas Layer**
- `app/schemas/dataset.py` - Dataset request/response schemas
- `app/schemas/cycle.py` - Cycle schemas
- `app/schemas/analysis.py` - Analysis schemas

✓ **Services Layer**
- `app/services/dataset_service.py` - Dataset upload & parsing
- `app/services/cycle_service.py` - Cycle management
- `app/services/analysis_service.py` - Deviation detection & analysis

✓ **API Layer**
- `app/api/v1/endpoints/datasets.py` - Dataset endpoints
- `app/api/v1/endpoints/cycles.py` - Cycle endpoints
- `app/api/v1/endpoints/analysis.py` - Analysis endpoints

### Frontend Component Check
✓ **Services**
- `services/api.ts` - API client with type definitions

✓ **Pages**
- `pages/Dashboard.tsx` - Main dashboard
- `pages/DatasetList.tsx` - Dataset management
- `pages/CycleViewer.tsx` - Cycle visualization
- `pages/Analysis.tsx` - Deviation analysis

✓ **Components**
- `components/CycleChart.tsx` - Plotly time-series charts

## Manual Testing Procedure

### 1. Backend API Test
```bash
# Start backend
cd backend
source venv/bin/activate
uvicorn main:app --reload

# In another terminal, test endpoints
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/datasets/
```

### 2. Database Test
```python
# Run in Python shell
cd backend
python
>>> from app.core.database import SessionLocal, engine
>>> from app.models.models import Dataset, Cycle
>>> session = SessionLocal()
>>> datasets = session.query(Dataset).all()
>>> print(f"Found {len(datasets)} datasets")
```

### 3. Frontend Test
```bash
cd frontend
npm start

# Should open http://localhost:3000
# Check browser console for errors
```

### 4. Full Integration Test
1. Start backend: `uvicorn main:app --reload`
2. Start frontend: `npm start`
3. Open browser to `http://localhost:3000`
4. Upload sample dataset: `data/sample_cycles.csv`
5. View cycles
6. Set reference cycle
7. Analyze deviations

## Debug Mode

### Enable Verbose Logging

**Backend** - Edit `app/core/config.py`:
```python
DEBUG = True  # Already enabled by default
```

**Frontend** - Check browser console (F12)

### API Documentation
When backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Performance Checks

### Backend Performance
```python
# Test data processing speed
import time
import pandas as pd

df = pd.read_csv('data/sample_cycles.csv')
start = time.time()
# Process operations here
end = time.time()
print(f"Processing took {end-start:.2f} seconds")
```

### Frontend Performance
- Open DevTools → Performance tab
- Record a session
- Check for slow operations

## Known Limitations

1. **SQLite Limitations**: For production, use PostgreSQL
2. **File Size**: Default max upload is 100MB (configurable)
3. **Concurrent Users**: SQLite doesn't handle high concurrency well
4. **Memory Usage**: Large datasets loaded entirely into memory

## Validation Checklist

- [ ] Backend starts without errors
- [ ] Database tables created
- [ ] All API endpoints accessible
- [ ] Frontend compiles successfully
- [ ] Frontend connects to backend
- [ ] File upload works
- [ ] Cycle visualization displays
- [ ] Analysis runs without errors
- [ ] No console errors in browser

## Getting Help

1. **Check Logs**: Backend terminal and browser console
2. **Run Validation**: `python validate_system.py`
3. **Check Dependencies**: `pip list` and `npm list`
4. **Review Error Stack Traces**: Full error messages help identify issues

## System Requirements

### Minimum
- Python 3.9+
- Node.js 16+
- 4GB RAM
- 1GB disk space

### Recommended
- Python 3.11+
- Node.js 18+
- 8GB RAM
- 5GB disk space (for datasets)

## Environment Variables

### Backend (.env)
```env
PROJECT_NAME=VerTac
VERSION=0.1.0
DEBUG=True
DATABASE_URL=sqlite:///./vertac.db
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
SECRET_KEY=your-secret-key
MAX_UPLOAD_SIZE_MB=100
SUPPORTED_FILE_FORMATS=csv,xlsx,parquet
```

### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## Useful Commands

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Run tests
python validate_system.py

# Start server
uvicorn main:app --reload

# Start with different port
uvicorn main:app --reload --port 8001
```

### Frontend
```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run type checking
npx tsc --noEmit
```

## Debugging Tips

1. **Enable All Logs**: Set `DEBUG=True` in backend `.env`
2. **Check Network Tab**: Browser DevTools → Network
3. **Validate JSON**: Use JSON validator for API responses
4. **Test Endpoints**: Use Postman or curl
5. **Check File Permissions**: Ensure upload directory is writable
6. **Database Inspection**: Use DB Browser for SQLite

## Contact & Support

For issues:
1. Check this debug guide
2. Run `validate_system.py`
3. Review error messages carefully
4. Check GitHub Issues

---

**Last Updated**: 2026-01-11
**System Version**: 0.1.0
