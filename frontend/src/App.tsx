import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import Dashboard from './pages/Dashboard';
import DatasetList from './pages/DatasetList';
import CycleViewer from './pages/CycleViewer';
import Analysis from './pages/Analysis';

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <div className="container">
            <nav className="nav">
              <h1 className="app-title">VerTac</h1>
              <div className="nav-links">
                <Link to="/">Dashboard</Link>
                <Link to="/datasets">Datasets</Link>
                <Link to="/analysis">Analysis</Link>
              </div>
            </nav>
          </div>
        </header>

        <main className="app-main">
          <div className="container">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/datasets" element={<DatasetList />} />
              <Route path="/cycles/:datasetId" element={<CycleViewer />} />
              <Route path="/analysis" element={<Analysis />} />
            </Routes>
          </div>
        </main>

        <footer className="app-footer">
          <div className="container">
            <p>VerTac - Cycle-Based Monitoring Platform</p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
