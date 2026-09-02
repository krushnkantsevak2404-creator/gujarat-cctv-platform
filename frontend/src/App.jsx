import React, { useState, useEffect } from 'react';
import {
  Shield,
  Activity,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Server,
  Database,
  Layers,
  Terminal,
  ExternalLink,
  Lock,
  Cpu
} from 'lucide-react';

export default function App() {
  const [healthData, setHealthData] = useState(null);
  const [status, setStatus] = useState('checking'); // 'connected' | 'error' | 'checking'
  const [errorMsg, setErrorMsg] = useState(null);
  const [latency, setLatency] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const checkHealth = async () => {
    setIsRefreshing(true);
    const startTime = performance.now();
    try {
      const response = await fetch('/api/health');
      const endTime = performance.now();
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setLatency(Math.round(endTime - startTime));
      setHealthData(data);
      setStatus('connected');
      setErrorMsg(null);
      setLastChecked(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Failed to fetch health status:', err);
      setStatus('error');
      setErrorMsg(err.message || 'Backend is unreachable');
      setLastChecked(new Date().toLocaleTimeString());
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    checkHealth();
    // Poll every 5 seconds for status updates
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex flex-col justify-between">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800 bg-[#081120]/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-600/20 border border-blue-500/40 rounded-lg text-blue-400">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight text-white">
                  Gujarat CCTV Intelligence Platform
                </span>
                <span className="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider bg-blue-900/60 text-blue-300 border border-blue-700/50 rounded-full">
                  PoC v1.0
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Gujarat Police Innovation Hackathon 2026 • Command Center
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex items-center px-3 py-1 bg-slate-900/80 border border-slate-800 rounded-lg text-xs font-mono text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 mr-2 animate-pulse"></span>
              Milestone 1: Active
            </div>
            <a
              href="/api/health"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-1 px-3 py-1.5 bg-blue-600/10 hover:bg-blue-600/20 border border-blue-500/30 rounded-lg text-xs font-medium text-blue-400 transition"
            >
              <span>API Health</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex-1 w-full space-y-8">
        
        {/* Hero & Primary Status Banner */}
        <div className="bg-gradient-to-r from-[#0d1c38] via-[#0b172d] to-[#0a1224] border border-blue-900/40 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl pointer-events-none"></div>
          
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
            <div>
              <div className="inline-flex items-center space-x-2 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full text-xs font-medium text-blue-400 mb-3">
                <Cpu className="w-3.5 h-3.5" />
                <span>Selected Solution: Model 2 – Unified Viewing & Selective Analytics</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                Gujarat CCTV Intelligence Platform
              </h1>
              <p className="mt-2 text-slate-300 max-w-2xl text-sm sm:text-base leading-relaxed">
                Foundational architecture for real-time video surveillance aggregation, GIS camera mapping, 
                and selective AI analytics built for Gujarat Police command and control centers.
              </p>
            </div>

            {/* Primary Live Status Badge */}
            <div className="flex flex-col sm:items-end justify-center">
              <div
                className={`flex items-center space-x-3 px-5 py-3 rounded-xl border shadow-lg ${
                  status === 'connected'
                    ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                    : status === 'checking'
                    ? 'bg-amber-950/40 border-amber-500/40 text-amber-300'
                    : 'bg-rose-950/40 border-rose-500/40 text-rose-300'
                }`}
              >
                {status === 'connected' ? (
                  <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                ) : status === 'checking' ? (
                  <RefreshCw className="w-6 h-6 text-amber-400 animate-spin" />
                ) : (
                  <XCircle className="w-6 h-6 text-rose-400" />
                )}
                <div>
                  <div className="text-xs uppercase font-mono tracking-wider opacity-80">
                    Live System Status
                  </div>
                  <div className="text-lg font-bold">
                    {status === 'connected'
                      ? 'System Status: Connected'
                      : status === 'checking'
                      ? 'System Status: Connecting...'
                      : 'System Status: Disconnected'}
                  </div>
                </div>
              </div>

              {lastChecked && (
                <div className="mt-2 text-xs font-mono text-slate-400 flex items-center space-x-2">
                  <span>Last sync: {lastChecked}</span>
                  {latency !== null && (
                    <span className="text-emerald-400">({latency}ms)</span>
                  )}
                  <button
                    onClick={checkHealth}
                    disabled={isRefreshing}
                    className="hover:text-white transition"
                    title="Refresh Now"
                  >
                    <RefreshCw
                      className={`w-3.5 h-3.5 inline ml-1 ${
                        isRefreshing ? 'animate-spin' : ''
                      }`}
                    />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Foundation Architecture Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Backend Service */}
          <div className="bg-[#0b1424] border border-slate-800 hover:border-slate-700 transition rounded-xl p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-400">
                <Server className="w-5 h-5" />
              </div>
              <span
                className={`px-2 py-1 text-xs font-mono rounded ${
                  status === 'connected'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                }`}
              >
                {status === 'connected' ? 'FastAPI 200 OK' : 'Offline'}
              </span>
            </div>
            <h2 className="text-base font-semibold text-white">Backend API Server</h2>
            <p className="text-xs text-slate-400 mt-1">
              FastAPI asynchronous application delivering REST endpoints and health diagnostics.
            </p>
            <div className="mt-4 pt-4 border-t border-slate-800/80 font-mono text-xs text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>Port:</span>
                <span className="text-slate-200">8000</span>
              </div>
              <div className="flex justify-between">
                <span>Endpoint:</span>
                <span className="text-blue-400">/api/health</span>
              </div>
            </div>
          </div>

          {/* Card 2: Database Foundation */}
          <div className="bg-[#0b1424] border border-slate-800 hover:border-slate-700 transition rounded-xl p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
                <Database className="w-5 h-5" />
              </div>
              <span className="px-2 py-1 text-xs font-mono bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded">
                PostgreSQL + PostGIS
              </span>
            </div>
            <h2 className="text-base font-semibold text-white">GIS Database Engine</h2>
            <p className="text-xs text-slate-400 mt-1">
              Geospatial database configuration for CCTV camera coordinates, coverage polygons, and jurisdictions.
            </p>
            <div className="mt-4 pt-4 border-t border-slate-800/80 font-mono text-xs text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>Engine:</span>
                <span className="text-slate-200">SQLAlchemy ORM</span>
              </div>
              <div className="flex justify-between">
                <span>Spatial Extension:</span>
                <span className="text-indigo-400">GeoAlchemy2</span>
              </div>
            </div>
          </div>

          {/* Card 3: Milestone Foundation Status */}
          <div className="bg-[#0b1424] border border-slate-800 hover:border-slate-700 transition rounded-xl p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
                <Layers className="w-5 h-5" />
              </div>
              <span className="px-2 py-1 text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded">
                Milestone 1 Complete
              </span>
            </div>
            <h2 className="text-base font-semibold text-white">Project Foundation</h2>
            <p className="text-xs text-slate-400 mt-1">
              Incremental architecture initialized. Model 1 (Registry/GIS) and Model 2 (Analytics) structure prepared.
            </p>
            <div className="mt-4 pt-4 border-t border-slate-800/80 font-mono text-xs text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>Frontend:</span>
                <span className="text-slate-200">React + Vite (5173)</span>
              </div>
              <div className="flex justify-between">
                <span>Next Phase:</span>
                <span className="text-emerald-400">Milestone 2 (Registry)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Live Diagnostics & Health Check Inspector */}
        <div className="bg-[#081120] border border-slate-800 rounded-xl p-6">
          <div className="flex items-center space-x-2 text-slate-200 font-semibold mb-4">
            <Terminal className="w-5 h-5 text-blue-400" />
            <span>Health Endpoint Response Inspector (`/api/health`)</span>
          </div>

          {status === 'connected' && healthData ? (
            <pre className="bg-[#040810] border border-slate-800/80 rounded-lg p-4 font-mono text-xs text-emerald-400 overflow-x-auto">
              {JSON.stringify(healthData, null, 2)}
            </pre>
          ) : status === 'checking' ? (
            <div className="bg-[#040810] border border-slate-800/80 rounded-lg p-6 text-center text-slate-400 text-xs font-mono">
              Connecting to backend at http://127.0.0.1:8000/api/health...
            </div>
          ) : (
            <div className="bg-rose-950/20 border border-rose-900/40 rounded-lg p-4 font-mono text-xs text-rose-300">
              <p className="font-bold">Connection Failed:</p>
              <p className="mt-1 text-slate-400">{errorMsg}</p>
              <p className="mt-2 text-slate-400 text-[11px]">
                Please ensure the FastAPI backend is running via `python run.py` on port 8000.
              </p>
            </div>
          )}
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#060b14] py-6 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Lock className="w-3.5 h-3.5 text-blue-400" />
            <span>Gujarat Police Innovation Hackathon 2026 — Proof of Concept</span>
          </div>
          <div>
            Built with React, Vite, FastAPI & PostgreSQL/PostGIS
          </div>
        </div>
      </footer>
    </div>
  );
}
