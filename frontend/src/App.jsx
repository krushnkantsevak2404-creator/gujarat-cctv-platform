import React, { useState, useEffect } from 'react';
import {
  Shield,
  Plus,
  Search,
  Filter,
  RefreshCw,
  Server,
  Database,
  Layers,
  Terminal,
  ExternalLink,
  Lock,
  Cpu,
  CheckCircle2,
  XCircle,
  Film,
  Radio,
  Camera as CamIcon,
  SlidersHorizontal,
  MapPin,
  Globe,
  Bell,
  ShieldAlert,
  AlertOctagon,
} from 'lucide-react';

import CameraStats from './components/CameraStats';
import CameraTable from './components/CameraTable';
import CameraModal from './components/CameraModal';
import CameraDetailsModal from './components/CameraDetailsModal';
import VideoPlayerModal from './components/VideoPlayerModal';
import DetectionResultsModal from './components/DetectionResultsModal';
import GisView from './components/GisView';
import AnprResultsModal from './components/AnprResultsModal';
import AnprSearchGlobal from './components/AnprSearchGlobal';
import WatchlistPage from './components/WatchlistPage';
import AlertsPage from './components/AlertsPage';
import VehicleSearchPage from './components/VehicleSearchPage';

export default function App() {
  // Navigation tabs: 'registry' | 'gis' | 'watchlist' | 'alerts' | 'vehicle-search' | 'anpr' | 'diagnostics'
  const [activeTab, setActiveTab] = useState('registry');

  // Health check state
  const [healthData, setHealthData] = useState(null);
  const [healthStatus, setHealthStatus] = useState('checking');
  const [latency, setLatency] = useState(null);

  // Cameras & Stats data
  const [cameras, setCameras] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  // Search & Filters state for Registry view
  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceTypeFilter, setSourceTypeFilter] = useState('');
  const [cameraTypeFilter, setCameraTypeFilter] = useState('');

  // Modals state
  const [isCameraModalOpen, setIsCameraModalOpen] = useState(false);
  const [cameraToEdit, setCameraToEdit] = useState(null);
  const [viewingCamera, setViewingCamera] = useState(null);
  const [playingFootageInfo, setPlayingFootageInfo] = useState(null);
  const [analyzingFootageInfo, setAnalyzingFootageInfo] = useState(null);
  const [anprModalInfo, setAnprModalInfo] = useState(null);

  // Focused camera on GIS map
  const [focusedCameraOnMap, setFocusedCameraOnMap] = useState(null);

  // Milestone 7 & 8: Watchlist, Alerts, and Vehicle Search state
  const [alertStats, setAlertStats] = useState(null);
  const [alertsPlateFilter, setAlertsPlateFilter] = useState('');
  const [vehicleSearchPlate, setVehicleSearchPlate] = useState('');

  // Fetch Health Check
  const checkHealth = async () => {
    const start = performance.now();
    try {
      const res = await fetch('/api/health');
      const end = performance.now();
      if (res.ok) {
        const data = await res.json();
        setHealthData(data);
        setHealthStatus('connected');
        setLatency(Math.round(end - start));
      } else {
        setHealthStatus('error');
      }
    } catch {
      setHealthStatus('error');
    }
  };

  // Fetch Stats
  const fetchStats = async () => {
    try {
      const res = await fetch('/api/cameras/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  // Fetch Alert Stats for live navigation badges
  const fetchAlertStats = async () => {
    try {
      const res = await fetch('/api/alerts/stats');
      if (res.ok) {
        const data = await res.json();
        setAlertStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch alert stats:', err);
    }
  };

  // Fetch Cameras with filters
  const fetchCameras = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.append('search', search.trim());
      if (department) params.append('department', department);
      if (statusFilter) params.append('status', statusFilter);
      if (sourceTypeFilter) params.append('source_type', sourceTypeFilter);
      if (cameraTypeFilter) params.append('camera_type', cameraTypeFilter);

      const res = await fetch(`/api/cameras?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setCameras(data);
      }
    } catch (err) {
      console.error('Failed to fetch cameras:', err);
    } finally {
      setLoading(false);
    }
  };

  const refreshAll = () => {
    checkHealth();
    fetchStats();
    fetchAlertStats();
    fetchCameras();
  };

  useEffect(() => {
    refreshAll();
    const interval = setInterval(() => {
      checkHealth();
      fetchAlertStats();
    }, 6000);
    return () => clearInterval(interval);
  }, []);

  // Debounced search / filter trigger for registry tab
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchCameras();
    }, 250);
    return () => clearTimeout(timer);
  }, [search, department, statusFilter, sourceTypeFilter, cameraTypeFilter]);

  // Handle Save Camera (Create / Update)
  const handleSaveCamera = async (payload, camera_id) => {
    const url = camera_id ? `/api/cameras/${camera_id}` : '/api/cameras';
    const method = camera_id ? 'PUT' : 'POST';

    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to save camera asset');
    }

    refreshAll();
  };

  // Handle Delete Camera
  const handleDeleteCamera = async (cam) => {
    if (
      !window.confirm(
        `Are you sure you want to delete camera "${cam.camera_code} - ${cam.camera_name}"? All associated footage files will be permanently deleted.`
      )
    ) {
      return;
    }

    try {
      const res = await fetch(`/api/cameras/${cam.id}`, { method: 'DELETE' });
      if (res.ok) {
        refreshAll();
      } else {
        alert('Failed to delete camera.');
      }
    } catch (err) {
      alert(`Error deleting camera: ${err.message}`);
    }
  };

  const handleOpenAddModal = () => {
    setCameraToEdit(null);
    setIsCameraModalOpen(true);
  };

  const handleOpenEditModal = (cam) => {
    setCameraToEdit(cam);
    setIsCameraModalOpen(true);
  };

  const handleOpenDetailsModal = (cam) => {
    setViewingCamera(cam);
  };

  const handlePlayFootage = (footage, camera) => {
    setPlayingFootageInfo({ footage, camera });
  };

  // Cross-Navigation: Navigate from Table / Modal to GIS Map
  const handleViewOnGisMap = (cam) => {
    setFocusedCameraOnMap(cam);
    setActiveTab('gis');
  };

  // Handle GIS popup view footage
  const handleGisViewFootage = async (cam) => {
    try {
      const res = await fetch(`/api/cameras/${cam.id}/footage`);
      if (res.ok) {
        const clips = await res.json();
        if (clips && clips.length > 0) {
          handlePlayFootage(clips[0], cam);
        } else {
          setViewingCamera(cam);
        }
      }
    } catch {
      setViewingCamera(cam);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-between bg-[#060b14] text-slate-100">
      
      {/* Top Police Command Navigation */}
      <header className="border-b border-slate-800 bg-[#081120]/95 backdrop-blur-md sticky top-0 z-40">
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
                <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-blue-900/60 text-blue-300 border border-blue-700/50 rounded-full">
                  PoC v3.0 (GIS)
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Gujarat Police Innovation Hackathon 2026 • Command & Control Center
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* System Status Pill */}
            <div className="hidden sm:flex items-center px-3 py-1.5 bg-[#0a1424] border border-slate-800 rounded-lg text-xs font-mono">
              <span
                className={`w-2 h-2 rounded-full mr-2 ${
                  healthStatus === 'connected'
                    ? 'bg-emerald-400 animate-pulse'
                    : 'bg-rose-400'
                }`}
              ></span>
              <span className={healthStatus === 'connected' ? 'text-emerald-300' : 'text-rose-300'}>
                {healthStatus === 'connected'
                  ? `System Status: Connected (${latency}ms)`
                  : 'System Status: Disconnected'}
              </span>
            </div>

            <button
              onClick={handleOpenAddModal}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition shadow-lg shadow-blue-600/25"
            >
              <Plus className="w-4 h-4" />
              <span>Register Camera</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Dashboard */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-6">
        
        {/* Navigation Tabs */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2 sm:space-x-3 overflow-x-auto">
            {/* Tab 1: CCTV Camera Registry */}
            <button
              onClick={() => setActiveTab('registry')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition whitespace-nowrap ${
                activeTab === 'registry'
                  ? 'bg-blue-600/20 text-blue-300 border border-blue-500/40 shadow-inner'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <CamIcon className="w-4 h-4 text-blue-400" />
              <span>CCTV Camera Registry</span>
            </button>

            {/* Tab 2: GIS Camera Map (Leaflet + PostGIS) */}
            <button
              onClick={() => setActiveTab('gis')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition whitespace-nowrap ${
                activeTab === 'gis'
                  ? 'bg-emerald-600/20 text-emerald-300 border border-emerald-500/40 shadow-inner'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <MapPin className="w-4 h-4 text-emerald-400" />
              <span>GIS Camera Map (Leaflet)</span>
              <span className="px-1.5 py-0.2 rounded bg-emerald-500/20 text-[10px] text-emerald-300 font-mono">
                {cameras.length}
              </span>
            </button>

            {/* Tab 3: Watchlist Management (Milestone 7) */}
            <button
              onClick={() => setActiveTab('watchlist')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition whitespace-nowrap ${
                activeTab === 'watchlist'
                  ? 'bg-rose-600/20 text-rose-300 border border-rose-500/40 shadow-inner'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <span>Watchlist Management</span>
              <span className="px-1.5 py-0.2 rounded bg-rose-500/20 text-[10px] text-rose-300 font-mono font-bold">
                M7
              </span>
            </button>

            {/* Tab 4: Surveillance Alerts (Milestone 7) */}
            <button
              onClick={() => setActiveTab('alerts')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition whitespace-nowrap relative ${
                activeTab === 'alerts'
                  ? 'bg-red-600/25 text-red-300 border border-red-500/50 shadow-inner'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <Bell className="w-4 h-4 text-rose-400" />
              <span>Surveillance Alerts</span>
              {alertStats && alertStats.new_alerts > 0 ? (
                <span className="px-2 py-0.5 rounded-full bg-rose-600 text-white text-[10px] font-black animate-pulse flex items-center space-x-1 shadow-lg shadow-rose-600/50">
                  <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>
                  <span>{alertStats.new_alerts} NEW</span>
                </span>
              ) : alertStats && alertStats.total_alerts > 0 ? (
                <span className="px-1.5 py-0.2 rounded bg-slate-800 text-[10px] text-slate-300 font-mono">
                  {alertStats.total_alerts}
                </span>
              ) : null}
            </button>

            {/* Tab 5: Vehicle Search & Movement History (Milestone 8) */}
            <button
              onClick={() => setActiveTab('vehicle-search')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition whitespace-nowrap ${
                activeTab === 'vehicle-search'
                  ? 'bg-cyan-600/20 text-cyan-300 border border-cyan-500/40 shadow-inner'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <Car className="w-4 h-4 text-cyan-400" />
              <span>Vehicle Search & History</span>
              <span className="px-1.5 py-0.2 rounded bg-cyan-500/20 text-[10px] text-cyan-300 font-mono font-bold">
                M8
              </span>
            </button>

            {/* Tab 6: Central ANPR & License Plate Intelligence */}
            <button
              onClick={() => setActiveTab('anpr')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition whitespace-nowrap ${
                activeTab === 'anpr'
                  ? 'bg-amber-600/20 text-amber-300 border border-amber-500/40 shadow-inner'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <Shield className="w-4 h-4 text-amber-400" />
              <span>ANPR Intelligence & Search</span>
              <span className="px-1.5 py-0.2 rounded bg-amber-500/20 text-[10px] text-amber-300 font-mono font-bold">
                M6
              </span>
            </button>

            {/* Tab 7: Diagnostics */}
            <button
              onClick={() => setActiveTab('diagnostics')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition whitespace-nowrap ${
                activeTab === 'diagnostics'
                  ? 'bg-blue-600/20 text-blue-300 border border-blue-500/40'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <Terminal className="w-4 h-4 text-cyan-400" />
              <span>Diagnostics & GeoJSON</span>
            </button>
          </div>

          <button
            onClick={refreshAll}
            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
            title="Refresh All Data"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>

        {/* Tab Content 1: CCTV Camera Registry */}
        {activeTab === 'registry' && (
          <div className="space-y-6">
            {/* Top Statistics Cards */}
            <CameraStats stats={stats} loading={!stats} />

            {/* Search & Filter Toolbar */}
            <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-4 shadow-lg space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
                
                {/* Keyword Search */}
                <div className="relative sm:col-span-2">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Search by camera name, code, department, location..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 rounded-lg bg-[#070d18] border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                  {search && (
                    <button
                      onClick={() => setSearch('')}
                      className="absolute right-2.5 top-2.5 text-slate-500 hover:text-slate-300"
                    >
                      ×
                    </button>
                  )}
                </div>

                {/* Source Type Filter */}
                <div>
                  <select
                    value={sourceTypeFilter}
                    onChange={(e) => setSourceTypeFilter(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[#070d18] border border-slate-700 text-slate-200 focus:outline-none focus:border-blue-500"
                  >
                    <option value="">All CCTV Sources</option>
                    <option value="RECORDED_FOOTAGE">Recorded Footage (File)</option>
                    <option value="LIVE_CAMERA">Live Camera (RTSP)</option>
                  </select>
                </div>

                {/* Status Filter */}
                <div>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[#070d18] border border-slate-700 text-slate-200 focus:outline-none focus:border-blue-500"
                  >
                    <option value="">All Statuses</option>
                    <option value="ONLINE">ONLINE</option>
                    <option value="OFFLINE">OFFLINE</option>
                    <option value="MAINTENANCE">MAINTENANCE</option>
                    <option value="UNKNOWN">UNKNOWN</option>
                  </select>
                </div>

                {/* Camera Hardware Type */}
                <div>
                  <select
                    value={cameraTypeFilter}
                    onChange={(e) => setCameraTypeFilter(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[#070d18] border border-slate-700 text-slate-200 focus:outline-none focus:border-blue-500"
                  >
                    <option value="">All Camera Types</option>
                    <option value="FIXED">FIXED</option>
                    <option value="PTZ">PTZ</option>
                    <option value="DOME">DOME</option>
                    <option value="BULLET">BULLET</option>
                    <option value="OTHER">OTHER</option>
                  </select>
                </div>

              </div>

              {/* Active Filter Badges */}
              {(search || sourceTypeFilter || statusFilter || cameraTypeFilter) && (
                <div className="flex items-center space-x-2 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
                  <SlidersHorizontal className="w-3.5 h-3.5" />
                  <span>Filtered Results ({cameras.length})</span>
                  <button
                    onClick={() => {
                      setSearch('');
                      setSourceTypeFilter('');
                      setStatusFilter('');
                      setCameraTypeFilter('');
                    }}
                    className="text-blue-400 hover:underline font-mono"
                  >
                    Reset Filters
                  </button>
                </div>
              )}
            </div>

            {/* Cameras Table */}
            <CameraTable
              cameras={cameras}
              loading={loading}
              onView={handleOpenDetailsModal}
              onEdit={handleOpenEditModal}
              onDelete={handleDeleteCamera}
              onViewOnMap={handleViewOnGisMap}
            />
          </div>
        )}

        {/* Tab Content 2: GIS Camera Map (Leaflet + PostGIS) */}
        {activeTab === 'gis' && (
          <GisView
            cameras={cameras}
            stats={stats}
            focusedCamera={focusedCameraOnMap}
            onSelectCamera={(cam) => setFocusedCameraOnMap(cam)}
            onViewDetails={handleOpenDetailsModal}
            onViewFootage={handleGisViewFootage}
          />
        )}

        {/* Tab Content 3: Watchlist Management (Milestone 7) */}
        {activeTab === 'watchlist' && (
          <WatchlistPage
            onNavigateToAlerts={(plate) => {
              setAlertsPlateFilter(plate);
              setActiveTab('alerts');
            }}
            onSearchVehicle={(plate) => {
              setVehicleSearchPlate(plate);
              setActiveTab('vehicle-search');
            }}
          />
        )}

        {/* Tab Content 4: Surveillance Alerts (Milestone 7) */}
        {activeTab === 'alerts' && (
          <AlertsPage
            initialPlateFilter={alertsPlateFilter}
            onPlayFootageEvidence={(clip, cam, seekSec) => {
              setPlayingFootageInfo({ footage: clip, camera: cam, seekTime: seekSec });
            }}
            onLocateCameraOnGis={(cam) => {
              handleViewOnGisMap(cam);
            }}
          />
        )}

        {/* Tab Content 5: Vehicle Search & Movement History (Milestone 8) */}
        {activeTab === 'vehicle-search' && (
          <VehicleSearchPage
            initialPlate={vehicleSearchPlate}
            onPlayFootageEvidence={(clip, cam, seekSec) => {
              setPlayingFootageInfo({ footage: clip, camera: cam, seekTime: seekSec });
            }}
            onNavigateToAlerts={(plate) => {
              setAlertsPlateFilter(plate);
              setActiveTab('alerts');
            }}
          />
        )}

        {/* Tab Content 6: ANPR Intelligence & Global Search */}
        {activeTab === 'anpr' && (
          <AnprSearchGlobal
            onSelectResult={async (item) => {
              try {
                const footRes = await fetch(`/api/footage/${item.footage_id}`);
                const camRes = await fetch(`/api/cameras/${item.camera_id}`);
                if (footRes.ok && camRes.ok) {
                  const foot = await footRes.json();
                  const cam = await camRes.json();
                  setAnprModalInfo({ footage: foot, camera: cam, autoStart: false });
                }
              } catch (err) {
                console.error('Error opening ANPR record:', err);
              }
            }}
            onNavigateToGis={(cameraId) => {
              const cam = cameras.find((c) => c.id === cameraId);
              if (cam) {
                handleViewOnGisMap(cam);
              } else {
                setActiveTab('gis');
              }
            }}
          />
        )}

        {/* Tab Content 6: System Diagnostics & GeoJSON */}
        {activeTab === 'diagnostics' && (
          <div className="space-y-6">
            <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-white font-bold">
                  <Terminal className="w-5 h-5 text-emerald-400" />
                  <span>Backend & Database Connectivity Diagnostics</span>
                </div>
                <a
                  href="/api/cameras/geojson"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-1.5 px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/40 rounded-lg text-xs font-bold text-blue-300 transition"
                >
                  <span>Open Raw GeoJSON</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
              <pre className="p-4 rounded-lg bg-[#040810] border border-slate-800 font-mono text-xs text-emerald-400 overflow-x-auto">
                {JSON.stringify(healthData, null, 2)}
              </pre>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
              <div className="p-5 rounded-xl bg-[#0b1424] border border-slate-800 space-y-3">
                <h3 className="font-bold text-white text-sm flex items-center space-x-2">
                  <Globe className="w-4 h-4 text-blue-400" />
                  <span>GeoJSON FeatureCollection API</span>
                </h3>
                <p className="text-slate-400">
                  Export camera assets as an RFC 7946 compliant GeoJSON FeatureCollection with Point coordinates <code>[longitude, latitude]</code> and camera metadata.
                </p>
                <div className="p-3 rounded-lg bg-[#070d18] border border-slate-800 font-mono text-slate-300">
                  Endpoint: GET /api/cameras/geojson
                </div>
              </div>

              <div className="p-5 rounded-xl bg-[#0b1424] border border-slate-800 space-y-3">
                <h3 className="font-bold text-white text-sm flex items-center space-x-2">
                  <MapPin className="w-4 h-4 text-emerald-400" />
                  <span>PostGIS Spatial SRID 4326</span>
                </h3>
                <p className="text-slate-400">
                  Geographic location points are stored natively in PostGIS as WGS84 coordinates (Latitude North/South, Longitude East/West).
                </p>
                <div className="p-3 rounded-lg bg-[#070d18] border border-slate-800 font-mono text-slate-300">
                  Table: cameras (location GEOGRAPHY(POINT, 4326))
                </div>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* Modals */}
      <CameraModal
        isOpen={isCameraModalOpen}
        onClose={() => setIsCameraModalOpen(false)}
        onSave={handleSaveCamera}
        camera={cameraToEdit}
      />

      <CameraDetailsModal
        isOpen={!!viewingCamera}
        onClose={() => setViewingCamera(null)}
        camera={viewingCamera}
        onPlayFootage={(clip, cam) => {
          setPlayingFootageInfo({ footage: clip, camera: cam });
        }}
        onViewOnMap={handleViewOnGisMap}
        onAnalyzeFootage={(clip, cam) => {
          setAnalyzingFootageInfo({ footage: clip, camera: cam, autoStart: true });
        }}
        onViewDetections={(clip, cam) => {
          setAnalyzingFootageInfo({ footage: clip, camera: cam, autoStart: false });
        }}
        onViewAnpr={(clip, cam) => {
          setAnprModalInfo({ footage: clip, camera: cam });
        }}
        onRunAnpr={async (clip, cam) => {
          try {
            await fetch(`/api/footage/${clip.id}/anpr`, { method: 'POST' });
            setAnprModalInfo({ footage: clip, camera: cam });
          } catch (err) {
            console.error('Failed to start ANPR:', err);
          }
        }}
      />

      <VideoPlayerModal
        isOpen={!!playingFootageInfo}
        onClose={() => setPlayingFootageInfo(null)}
        footage={playingFootageInfo?.footage}
        camera={playingFootageInfo?.camera}
        initialSeekTime={playingFootageInfo?.seekTime}
      />

      <DetectionResultsModal
        isOpen={!!analyzingFootageInfo}
        onClose={() => setAnalyzingFootageInfo(null)}
        footage={analyzingFootageInfo?.footage}
        camera={analyzingFootageInfo?.camera}
        autoStart={analyzingFootageInfo?.autoStart}
      />

      <AnprResultsModal
        isOpen={!!anprModalInfo}
        onClose={() => setAnprModalInfo(null)}
        footage={anprModalInfo?.footage}
        camera={anprModalInfo?.camera}
        onRerunAnpr={async (clip, cam) => {
          try {
            await fetch(`/api/footage/${clip.id}/anpr`, { method: 'POST' });
            setAnprModalInfo({ footage: clip, camera: cam });
          } catch (e) {
            console.error('Failed to rerun ANPR:', e);
          }
        }}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#060b14] py-6 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Lock className="w-3.5 h-3.5 text-blue-400" />
            <span>Gujarat Police Innovation Hackathon 2026 — Milestone 8 Vehicle Search & Movement History Active</span>
          </div>
          <div>
            FastAPI + PostGIS + YOLO + ByteTrack + EasyOCR + Vehicle Sequence Engine + React 18
          </div>
        </div>
      </footer>

    </div>
  );
}
