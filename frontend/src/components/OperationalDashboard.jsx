import React, { useState, useEffect, useMemo } from 'react';
import {
  Shield,
  Activity,
  Server,
  Database,
  Globe,
  Cpu,
  Radio,
  Film,
  Camera as CamIcon,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  Search,
  Filter,
  SlidersHorizontal,
  ExternalLink,
  MapPin,
  Tv,
  Car,
  Bell,
  Eye,
  ChevronRight,
  Layers,
  ShieldAlert,
  ArrowUpRight,
  Sparkles,
  Info,
  Plus,
} from 'lucide-react';

export default function OperationalDashboard({
  onNavigateToGis,
  onNavigateToViewer,
  onNavigateToVehicleSearch,
  onNavigateToAlerts,
  onNavigateToRegistry,
  onOpenAddCamera,
  onOpenDetailsModal,
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Auto-refresh config (default 30 seconds)
  const [autoRefreshInterval, setAutoRefreshInterval] = useState(30); // in seconds, 0 = OFF
  const [lastUpdatedTime, setLastUpdatedTime] = useState(Date.now());
  const [secondsAgo, setSecondsAgo] = useState(0);

  // Search & Filter state for Camera Health Table
  const [search, setSearch] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceTypeFilter, setSourceTypeFilter] = useState('');
  const [connectivityFilter, setConnectivityFilter] = useState('');
  const [streamStatusFilter, setStreamStatusFilter] = useState('');

  // Fetch complete operational health data from backend API
  const fetchDashboardData = async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.append('search', search.trim());
      if (departmentFilter) params.append('department', departmentFilter);
      if (statusFilter) params.append('status', statusFilter);
      if (sourceTypeFilter) params.append('source_type', sourceTypeFilter);
      if (connectivityFilter) params.append('connectivity_type', connectivityFilter);
      if (streamStatusFilter) params.append('stream_status', streamStatusFilter);

      const res = await fetch(`/api/health/cameras?${params.toString()}`);
      if (!res.ok) {
        throw new Error(`Health check request failed with status ${res.status}`);
      }
      const json = await res.json();
      setData(json);
      setError(null);
      setLastUpdatedTime(Date.now());
      setSecondsAgo(0);
    } catch (err) {
      console.error('Error fetching dashboard health data:', err);
      setError(err.message || 'Failed to connect to health monitoring service');
    } finally {
      setLoading(false);
      if (isManual) setRefreshing(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchDashboardData();
  }, [departmentFilter, statusFilter, sourceTypeFilter, connectivityFilter, streamStatusFilter]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchDashboardData();
    }, 250);
    return () => clearTimeout(timer);
  }, [search]);

  // Periodic Auto-refresh Timer
  useEffect(() => {
    if (autoRefreshInterval <= 0) return;

    const interval = setInterval(() => {
      fetchDashboardData();
    }, autoRefreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefreshInterval, search, departmentFilter, statusFilter, sourceTypeFilter, connectivityFilter, streamStatusFilter]);

  // Seconds ago live counter
  useEffect(() => {
    const counter = setInterval(() => {
      setSecondsAgo(Math.floor((Date.now() - lastUpdatedTime) / 1000));
    }, 1000);
    return () => clearInterval(counter);
  }, [lastUpdatedTime]);

  // Quick Filter click handlers
  const handleFilterByStatus = (status) => {
    setStatusFilter(status === statusFilter ? '' : status);
  };

  const handleFilterBySource = (source) => {
    setSourceTypeFilter(source === sourceTypeFilter ? '' : source);
  };

  const handleResetFilters = () => {
    setSearch('');
    setDepartmentFilter('');
    setStatusFilter('');
    setSourceTypeFilter('');
    setConnectivityFilter('');
    setStreamStatusFilter('');
  };

  const summary = data?.summary || {
    total: 0,
    online: 0,
    offline: 0,
    maintenance: 0,
    unknown: 0,
    live_sources: 0,
    recorded_sources: 0,
    connected_streams: 0,
    disconnected_streams: 0,
    not_configured_streams: 0,
    error_streams: 0,
    active_alerts: 0,
    total_observations: 0,
  };

  const system = data?.system_health || null;
  const analytics = data?.vehicle_analytics || {
    total_anpr_observations: 0,
    total_vehicles_detected: 0,
    total_tracked_vehicles: 0,
    total_watchlist_matches: 0,
    unique_plates_count: 0,
  };

  // Percentage calculations for health bar
  const totalCams = summary.total || 1;
  const onlinePct = Math.round((summary.online / totalCams) * 100);
  const offlinePct = Math.round((summary.offline / totalCams) * 100);
  const maintenancePct = Math.round((summary.maintenance / totalCams) * 100);
  const unknownPct = Math.max(0, 100 - (onlinePct + offlinePct + maintenancePct));

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* 1. TOP COMMAND HEADER & SYSTEM STATUS */}
      <div className="bg-[#0b1424] border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          
          {/* Header Title */}
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-blue-600/20 border border-blue-500/40 rounded-xl text-blue-400">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold text-white tracking-tight">
                  Operational Command & CCTV Health Dashboard
                </h1>
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-emerald-950/60 text-emerald-300 border border-emerald-700/50 rounded-full flex items-center space-x-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>LIVE TELEMETRY</span>
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Real-time health monitoring, stream inspection, and surveillance analytics across Gujarat Police jurisdictions.
              </p>
            </div>
          </div>

          {/* Auto Refresh & Action Controls */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Last Updated indicator */}
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-[#070d18] border border-slate-800 text-xs font-mono text-slate-300">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              <span>Updated {secondsAgo === 0 ? 'just now' : `${secondsAgo}s ago`}</span>
            </div>

            {/* Auto-refresh selector */}
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-[#070d18] border border-slate-800 text-xs">
              <span className="text-slate-400 font-mono text-[11px]">Auto:</span>
              <select
                value={autoRefreshInterval}
                onChange={(e) => setAutoRefreshInterval(Number(e.target.value))}
                className="bg-transparent text-slate-200 font-bold focus:outline-none cursor-pointer"
              >
                <option value={15} className="bg-[#0b1424]">15s</option>
                <option value={30} className="bg-[#0b1424]">30s</option>
                <option value={60} className="bg-[#0b1424]">60s</option>
                <option value={0} className="bg-[#0b1424]">OFF</option>
              </select>
            </div>

            {/* Manual Refresh Button */}
            <button
              onClick={() => fetchDashboardData(true)}
              disabled={refreshing}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition shadow-lg shadow-blue-600/30"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
            </button>
          </div>
        </div>

        {/* System Sub-service Health Status Pills */}
        {system && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5 pt-2 border-t border-slate-800/80">
            {/* 1. Backend API */}
            <div className="p-2 rounded-xl bg-[#070d18] border border-slate-800/90 flex items-center justify-between">
              <div className="flex items-center space-x-2 truncate">
                <Server className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                <span className="text-[11px] font-medium text-slate-300 truncate">Backend API</span>
              </div>
              <span className="px-1.5 py-0.5 text-[9px] font-bold font-mono rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shrink-0">
                {system.backend_api?.status || 'HEALTHY'}
              </span>
            </div>

            {/* 2. Database */}
            <div className="p-2 rounded-xl bg-[#070d18] border border-slate-800/90 flex items-center justify-between">
              <div className="flex items-center space-x-2 truncate">
                <Database className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                <span className="text-[11px] font-medium text-slate-300 truncate">Database (PostGIS)</span>
              </div>
              <span
                className={`px-1.5 py-0.5 text-[9px] font-bold font-mono rounded shrink-0 ${
                  system.database?.status === 'HEALTHY'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                }`}
              >
                {system.database?.status || 'HEALTHY'}
              </span>
            </div>

            {/* 3. GIS Map */}
            <div className="p-2 rounded-xl bg-[#070d18] border border-slate-800/90 flex items-center justify-between">
              <div className="flex items-center space-x-2 truncate">
                <Globe className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span className="text-[11px] font-medium text-slate-300 truncate">GIS Map (OSM)</span>
              </div>
              <span className="px-1.5 py-0.5 text-[9px] font-bold font-mono rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shrink-0">
                {system.gis?.status || 'HEALTHY'}
              </span>
            </div>

            {/* 4. AI Processing */}
            <div className="p-2 rounded-xl bg-[#070d18] border border-slate-800/90 flex items-center justify-between">
              <div className="flex items-center space-x-2 truncate">
                <Cpu className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                <span className="text-[11px] font-medium text-slate-300 truncate">AI Processing</span>
              </div>
              <span className="px-1.5 py-0.5 text-[9px] font-bold font-mono rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 shrink-0">
                {system.ai_processing?.status || 'READY'}
              </span>
            </div>

            {/* 5. Stream Service */}
            <div className="p-2 rounded-xl bg-[#070d18] border border-slate-800/90 flex items-center justify-between col-span-2 sm:col-span-1">
              <div className="flex items-center space-x-2 truncate">
                <Radio className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                <span className="text-[11px] font-medium text-slate-300 truncate">Stream Relay</span>
              </div>
              <span
                className={`px-1.5 py-0.5 text-[9px] font-bold font-mono rounded shrink-0 ${
                  system.stream_service?.status === 'HEALTHY'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                }`}
              >
                {system.stream_service?.status || 'HEALTHY'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* 2. QUICK ACCESS SHORTCUT TOOLBAR */}
      <div className="bg-[#0b1424] border border-slate-800/90 rounded-2xl p-4 shadow-lg flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono">
          <Sparkles className="w-4 h-4 text-blue-400" />
          <span>Quick Module Access:</span>
        </div>
        
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={onNavigateToGis}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-600/15 hover:bg-emerald-600/25 border border-emerald-500/30 text-emerald-300 text-xs font-semibold transition"
          >
            <MapPin className="w-3.5 h-3.5 text-emerald-400" />
            <span>GIS Camera Map</span>
          </button>

          <button
            onClick={onNavigateToViewer}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-blue-600/15 hover:bg-blue-600/25 border border-blue-500/30 text-blue-300 text-xs font-semibold transition"
          >
            <Tv className="w-3.5 h-3.5 text-blue-400" />
            <span>Unified Multi-Camera Viewer</span>
          </button>

          <button
            onClick={onNavigateToVehicleSearch}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-cyan-600/15 hover:bg-cyan-600/25 border border-cyan-500/30 text-cyan-300 text-xs font-semibold transition"
          >
            <Car className="w-3.5 h-3.5 text-cyan-400" />
            <span>Vehicle Search & Movement</span>
          </button>

          <button
            onClick={onNavigateToAlerts}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-rose-600/15 hover:bg-rose-600/25 border border-rose-500/30 text-rose-300 text-xs font-semibold transition"
          >
            <Bell className="w-3.5 h-3.5 text-rose-400" />
            <span>Watchlist Surveillance Alerts</span>
            {summary.active_alerts > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-rose-600 text-white text-[10px] font-bold">
                {summary.active_alerts}
              </span>
            )}
          </button>

          <button
            onClick={onNavigateToRegistry}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition"
          >
            <CamIcon className="w-3.5 h-3.5 text-slate-400" />
            <span>CCTV Registry</span>
          </button>
        </div>
      </div>

      {/* 3. DYNAMIC KPI SUMMARY CARDS (Clickable Filters) */}
      <div className="space-y-3">
        {/* Row 1: Infrastructure Fleet Status */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* Card 1: Total Cameras */}
          <div
            onClick={handleResetFilters}
            className="p-4 rounded-2xl bg-[#0b1424] border border-blue-900/40 hover:border-blue-500/60 shadow-lg cursor-pointer transition group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Registered</span>
              <div className="p-2 rounded-xl bg-blue-600/20 text-blue-400 group-hover:scale-110 transition">
                <CamIcon className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-black text-white font-mono">{summary.total}</div>
            <p className="text-[11px] text-slate-400 mt-1">Gujarat state CCTV assets</p>
          </div>

          {/* Card 2: Online Cameras */}
          <div
            onClick={() => handleFilterByStatus('ONLINE')}
            className={`p-4 rounded-2xl border shadow-lg cursor-pointer transition group ${
              statusFilter === 'ONLINE'
                ? 'bg-emerald-950/40 border-emerald-500 ring-2 ring-emerald-500/30'
                : 'bg-[#0b1424] border-emerald-900/40 hover:border-emerald-500/60'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Online Cameras</span>
              <div className="p-2 rounded-xl bg-emerald-600/20 text-emerald-400 group-hover:scale-110 transition">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-black text-emerald-300 font-mono">{summary.online}</div>
            <p className="text-[11px] text-emerald-400/80 mt-1">{onlinePct}% of registered fleet</p>
          </div>

          {/* Card 3: Offline Cameras */}
          <div
            onClick={() => handleFilterByStatus('OFFLINE')}
            className={`p-4 rounded-2xl border shadow-lg cursor-pointer transition group ${
              statusFilter === 'OFFLINE'
                ? 'bg-rose-950/40 border-rose-500 ring-2 ring-rose-500/30'
                : 'bg-[#0b1424] border-rose-900/40 hover:border-rose-500/60'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-rose-400 uppercase tracking-wider">Offline Cameras</span>
              <div className="p-2 rounded-xl bg-rose-600/20 text-rose-400 group-hover:scale-110 transition">
                <XCircle className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-black text-rose-300 font-mono">{summary.offline}</div>
            <p className="text-[11px] text-rose-400/80 mt-1">Requires connectivity attention</p>
          </div>

          {/* Card 4: Maintenance & Unknown */}
          <div
            onClick={() => handleFilterByStatus('MAINTENANCE')}
            className={`p-4 rounded-2xl border shadow-lg cursor-pointer transition group ${
              statusFilter === 'MAINTENANCE' || statusFilter === 'UNKNOWN'
                ? 'bg-amber-950/40 border-amber-500 ring-2 ring-amber-500/30'
                : 'bg-[#0b1424] border-amber-900/40 hover:border-amber-500/60'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">Maint / Unknown</span>
              <div className="p-2 rounded-xl bg-amber-600/20 text-amber-400 group-hover:scale-110 transition">
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-black text-amber-300 font-mono">
              {summary.maintenance + summary.unknown}
            </div>
            <p className="text-[11px] text-amber-400/80 mt-1">
              {summary.maintenance} in maintenance, {summary.unknown} unverified
            </p>
          </div>
        </div>

        {/* Row 2: Operational Intelligence Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* Card 5: Live Sources */}
          <div
            onClick={() => handleFilterBySource('LIVE_CAMERA')}
            className={`p-4 rounded-2xl border shadow-lg cursor-pointer transition group ${
              sourceTypeFilter === 'LIVE_CAMERA'
                ? 'bg-blue-950/40 border-blue-500 ring-2 ring-blue-500/30'
                : 'bg-[#0b1424] border-slate-800 hover:border-blue-500/50'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Live CCTV Sources</span>
              <div className="p-2 rounded-xl bg-blue-600/20 text-blue-400 group-hover:scale-110 transition">
                <Radio className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-black text-blue-300 font-mono">{summary.live_sources}</div>
            <p className="text-[11px] text-slate-400 mt-1">RTSP / VMS live integrations</p>
          </div>

          {/* Card 6: Recorded Footage Sources */}
          <div
            onClick={() => handleFilterBySource('RECORDED_FOOTAGE')}
            className={`p-4 rounded-2xl border shadow-lg cursor-pointer transition group ${
              sourceTypeFilter === 'RECORDED_FOOTAGE'
                ? 'bg-amber-950/40 border-amber-500 ring-2 ring-amber-500/30'
                : 'bg-[#0b1424] border-slate-800 hover:border-amber-500/50'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Recorded Sources</span>
              <div className="p-2 rounded-xl bg-amber-600/20 text-amber-400 group-hover:scale-110 transition">
                <Film className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-black text-amber-300 font-mono">{summary.recorded_sources}</div>
            <p className="text-[11px] text-slate-400 mt-1">Local media files for analytics</p>
          </div>

          {/* Card 7: Active Watchlist Alerts */}
          <div
            onClick={onNavigateToAlerts}
            className="p-4 rounded-2xl bg-[#0b1424] border border-rose-900/40 hover:border-rose-500/60 shadow-lg cursor-pointer transition group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-rose-400 uppercase tracking-wider">Active Watchlist Alerts</span>
              <div className="p-2 rounded-xl bg-rose-600/20 text-rose-400 group-hover:scale-110 transition">
                <ShieldAlert className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-black text-rose-300 font-mono flex items-center space-x-2">
              <span>{summary.active_alerts}</span>
              {summary.active_alerts > 0 && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-rose-600 text-white font-bold animate-pulse">
                  ACTIVE
                </span>
              )}
            </div>
            <p className="text-[11px] text-rose-400/80 mt-1">Hotlist matches requiring action</p>
          </div>

          {/* Card 8: Total ANPR Observations */}
          <div
            onClick={onNavigateToVehicleSearch}
            className="p-4 rounded-2xl bg-[#0b1424] border border-cyan-900/40 hover:border-cyan-500/60 shadow-lg cursor-pointer transition group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">ANPR Observations</span>
              <div className="p-2 rounded-xl bg-cyan-600/20 text-cyan-400 group-hover:scale-110 transition">
                <Car className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-black text-cyan-300 font-mono">{summary.total_observations.toLocaleString()}</div>
            <p className="text-[11px] text-cyan-400/80 mt-1">Extracted license plate sightings</p>
          </div>
        </div>
      </div>

      {/* 4. MIDDLE SECTION: FLEET DISTRIBUTION + DEPARTMENT BREAKDOWN & RECENT ALERTS */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column (7 cols): Camera Fleet Distribution & Department Breakdown */}
        <div className="lg:col-span-7 space-y-6">
          
          {/* Camera Fleet Status Distribution Bar */}
          <div className="bg-[#0b1424] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span>Camera Fleet Health Distribution</span>
              </h3>
              <span className="text-xs text-slate-400 font-mono">{summary.total} Registered Total</span>
            </div>

            {/* Segmented Progress Bar */}
            <div className="h-4 w-full bg-[#070d18] rounded-full overflow-hidden flex border border-slate-800">
              <div
                style={{ width: `${onlinePct}%` }}
                className="bg-emerald-500 transition-all duration-500 relative group"
                title={`Online: ${summary.online} (${onlinePct}%)`}
              />
              <div
                style={{ width: `${offlinePct}%` }}
                className="bg-rose-500 transition-all duration-500 relative group"
                title={`Offline: ${summary.offline} (${offlinePct}%)`}
              />
              <div
                style={{ width: `${maintenancePct}%` }}
                className="bg-amber-500 transition-all duration-500 relative group"
                title={`Maintenance: ${summary.maintenance} (${maintenancePct}%)`}
              />
              <div
                style={{ width: `${unknownPct}%` }}
                className="bg-slate-600 transition-all duration-500 relative group"
                title={`Unknown: ${summary.unknown} (${unknownPct}%)`}
              />
            </div>

            {/* Legend with interactive click filters */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-xs">
              <div
                onClick={() => handleFilterByStatus('ONLINE')}
                className="p-2 rounded-xl bg-[#070d18] border border-slate-800 cursor-pointer hover:border-emerald-500/50 transition"
              >
                <div className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                  <span className="font-semibold text-slate-300">Online</span>
                </div>
                <div className="font-mono font-bold text-emerald-300 mt-1">
                  {summary.online} <span className="text-[10px] text-slate-500">({onlinePct}%)</span>
                </div>
              </div>

              <div
                onClick={() => handleFilterByStatus('OFFLINE')}
                className="p-2 rounded-xl bg-[#070d18] border border-slate-800 cursor-pointer hover:border-rose-500/50 transition"
              >
                <div className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                  <span className="font-semibold text-slate-300">Offline</span>
                </div>
                <div className="font-mono font-bold text-rose-300 mt-1">
                  {summary.offline} <span className="text-[10px] text-slate-500">({offlinePct}%)</span>
                </div>
              </div>

              <div
                onClick={() => handleFilterByStatus('MAINTENANCE')}
                className="p-2 rounded-xl bg-[#070d18] border border-slate-800 cursor-pointer hover:border-amber-500/50 transition"
              >
                <div className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                  <span className="font-semibold text-slate-300">Maintenance</span>
                </div>
                <div className="font-mono font-bold text-amber-300 mt-1">
                  {summary.maintenance} <span className="text-[10px] text-slate-500">({maintenancePct}%)</span>
                </div>
              </div>

              <div
                onClick={() => handleFilterByStatus('UNKNOWN')}
                className="p-2 rounded-xl bg-[#070d18] border border-slate-800 cursor-pointer hover:border-slate-500/50 transition"
              >
                <div className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
                  <span className="font-semibold text-slate-300">Unknown</span>
                </div>
                <div className="font-mono font-bold text-slate-300 mt-1">
                  {summary.unknown} <span className="text-[10px] text-slate-500">({unknownPct}%)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Department Jurisdiction Breakdown */}
          <div className="bg-[#0b1424] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Shield className="w-4 h-4 text-blue-400" />
                <span>Department Jurisdiction Overview</span>
              </h3>
              <span className="text-xs text-slate-400 font-mono">
                {data?.departments?.length || 0} Departments Active
              </span>
            </div>

            <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
              {data?.departments?.map((dept) => {
                const isSelected = departmentFilter === dept.department;
                return (
                  <div
                    key={dept.department}
                    onClick={() => setDepartmentFilter(isSelected ? '' : dept.department)}
                    className={`p-3 rounded-xl border cursor-pointer transition flex items-center justify-between ${
                      isSelected
                        ? 'bg-blue-950/40 border-blue-500 text-white'
                        : 'bg-[#070d18] border-slate-800/80 hover:border-slate-700 text-slate-300'
                    }`}
                  >
                    <div>
                      <div className="font-bold text-xs text-white">{dept.department}</div>
                      <div className="text-[11px] text-slate-400 flex items-center space-x-2 mt-0.5 font-mono">
                        <span className="text-emerald-400">{dept.online_cameras} Online</span>
                        <span>•</span>
                        <span className="text-blue-400">{dept.live_cameras} Live</span>
                        <span>•</span>
                        <span className="text-amber-400">{dept.recorded_cameras} Recorded</span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      {dept.active_alerts_count > 0 && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-600/20 border border-rose-500/40 text-rose-300">
                          {dept.active_alerts_count} Alerts
                        </span>
                      )}
                      <span className="px-2.5 py-1 rounded-lg bg-[#0b1424] border border-slate-700 font-mono text-xs font-bold text-white">
                        {dept.total_cameras} {dept.total_cameras === 1 ? 'Cam' : 'Cams'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column (5 cols): Recent Surveillance Alerts & Vehicle Analytics Metrics */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* Recent Watchlist Alerts Card */}
          <div className="bg-[#0b1424] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Bell className="w-4 h-4 text-rose-400" />
                <span>Recent Watchlist Alerts</span>
              </h3>
              <button
                onClick={onNavigateToAlerts}
                className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center space-x-1"
              >
                <span>View All</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {data?.recent_alerts?.length === 0 ? (
              <div className="p-6 text-center text-slate-500 text-xs bg-[#070d18] rounded-xl border border-slate-800">
                <CheckCircle2 className="w-8 h-8 text-emerald-500/40 mx-auto mb-2" />
                <p>No active surveillance alerts recorded</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
                {data?.recent_alerts?.map((alert) => (
                  <div
                    key={alert.alert_id}
                    onClick={onNavigateToAlerts}
                    className="p-3 rounded-xl bg-[#070d18] border border-slate-800/90 hover:border-rose-500/50 transition cursor-pointer space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-black text-xs text-rose-400 tracking-wider">
                        {alert.plate_text}
                      </span>
                      <span
                        className={`px-1.5 py-0.2 rounded text-[9px] font-bold font-mono uppercase ${
                          alert.severity === 'CRITICAL'
                            ? 'bg-red-600 text-white'
                            : alert.severity === 'HIGH'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        }`}
                      >
                        {alert.severity}
                      </span>
                    </div>

                    <div className="text-[11px] text-slate-300 truncate">
                      {alert.camera_code} • {alert.camera_name}
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-0.5">
                      <span>{alert.location_name}</span>
                      <span>{alert.timestamp_formatted}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Vehicle Intelligence Metrics Mini Grid */}
          <div className="bg-[#0b1424] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-purple-400" />
              <span>Vehicle Analytics Summary (Database)</span>
            </h3>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-xl bg-[#070d18] border border-slate-800">
                <div className="text-[10px] uppercase font-bold text-slate-400">Total ANPR</div>
                <div className="text-xl font-bold font-mono text-cyan-300 mt-0.5">
                  {analytics.total_anpr_observations.toLocaleString()}
                </div>
                <div className="text-[10px] text-slate-500">{analytics.unique_plates_count} unique plates</div>
              </div>

              <div className="p-3 rounded-xl bg-[#070d18] border border-slate-800">
                <div className="text-[10px] uppercase font-bold text-slate-400">Detections</div>
                <div className="text-xl font-bold font-mono text-blue-300 mt-0.5">
                  {analytics.total_vehicles_detected.toLocaleString()}
                </div>
                <div className="text-[10px] text-slate-500">YOLOv8 vehicle frames</div>
              </div>

              <div className="p-3 rounded-xl bg-[#070d18] border border-slate-800">
                <div className="text-[10px] uppercase font-bold text-slate-400">Tracked Vehicles</div>
                <div className="text-xl font-bold font-mono text-purple-300 mt-0.5">
                  {analytics.total_tracked_vehicles.toLocaleString()}
                </div>
                <div className="text-[10px] text-slate-500">ByteTrack trajectories</div>
              </div>

              <div className="p-3 rounded-xl bg-[#070d18] border border-slate-800">
                <div className="text-[10px] uppercase font-bold text-slate-400">Watchlist Matches</div>
                <div className="text-xl font-bold font-mono text-rose-300 mt-0.5">
                  {analytics.total_watchlist_matches.toLocaleString()}
                </div>
                <div className="text-[10px] text-slate-500">Milestone 7 alerts</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 5. CAMERA FLEET HEALTH MONITORING TABLE */}
      <div className="bg-[#0b1424] border border-slate-800 rounded-2xl shadow-xl overflow-hidden space-y-4 p-5">
        
        {/* Table Title & Filter Bar */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center space-x-2">
              <CamIcon className="w-5 h-5 text-blue-400" />
              <span>Camera Fleet Operational Health Table</span>
            </h2>
            <p className="text-xs text-slate-400">
              Detailed inspection of registration status, live stream sessions, and storage footage availability.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            {(search || departmentFilter || statusFilter || sourceTypeFilter || connectivityFilter || streamStatusFilter) && (
              <button
                onClick={handleResetFilters}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
              >
                Clear Filters
              </button>
            )}
            <button
              onClick={onOpenAddCamera}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition shadow-lg shadow-blue-600/30"
            >
              <Plus className="w-4 h-4" />
              <span>Register Camera</span>
            </button>
          </div>
        </div>

        {/* Filter Inputs Toolbar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 text-xs bg-[#070d18] p-3.5 rounded-xl border border-slate-800">
          
          {/* Keyword Search */}
          <div className="sm:col-span-2 relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search camera name, code, location..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-lg bg-[#0b1424] border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Department Filter */}
          <div>
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-[#0b1424] border border-slate-700 text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="">All Departments</option>
              {data?.departments?.map((d) => (
                <option key={d.department} value={d.department}>
                  {d.department}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-[#0b1424] border border-slate-700 text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="ONLINE">ONLINE</option>
              <option value="OFFLINE">OFFLINE</option>
              <option value="MAINTENANCE">MAINTENANCE</option>
              <option value="UNKNOWN">UNKNOWN</option>
            </select>
          </div>

          {/* Source Filter */}
          <div>
            <select
              value={sourceTypeFilter}
              onChange={(e) => setSourceTypeFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-[#0b1424] border border-slate-700 text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="">All Sources</option>
              <option value="LIVE_CAMERA">Live Camera (RTSP)</option>
              <option value="RECORDED_FOOTAGE">Recorded Footage</option>
            </select>
          </div>

          {/* Stream Status Filter */}
          <div>
            <select
              value={streamStatusFilter}
              onChange={(e) => setStreamStatusFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-[#0b1424] border border-slate-700 text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="">All Stream States</option>
              <option value="CONNECTED">CONNECTED</option>
              <option value="DISCONNECTED">DISCONNECTED</option>
              <option value="NOT_CONFIGURED">NOT CONFIGURED</option>
              <option value="ERROR">ERROR</option>
            </select>
          </div>
        </div>

        {/* Camera Table */}
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#080f1c] text-slate-400 border-b border-slate-800 font-mono uppercase text-[11px]">
              <tr>
                <th className="px-4 py-3">Camera / Code</th>
                <th className="px-4 py-3">Department</th>
                <th className="px-4 py-3">Location & GPS</th>
                <th className="px-4 py-3">Source & Mode</th>
                <th className="px-4 py-3">Registration</th>
                <th className="px-4 py-3">Stream Session</th>
                <th className="px-4 py-3">Health Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 bg-[#070d18]">
              {data?.cameras?.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-slate-500">
                    No camera assets matched the current search and filter criteria.
                  </td>
                </tr>
              ) : (
                data?.cameras?.map((cam) => {
                  const isOnline = cam.status === 'ONLINE';
                  const isOffline = cam.status === 'OFFLINE';
                  const isMaint = cam.status === 'MAINTENANCE';

                  return (
                    <tr key={cam.camera_id} className="hover:bg-slate-800/40 transition">
                      
                      {/* Camera Name & Code */}
                      <td className="px-4 py-3">
                        <div className="font-bold text-white text-xs">{cam.camera_name}</div>
                        <div className="font-mono text-[11px] text-blue-400 font-bold">{cam.camera_code}</div>
                      </td>

                      {/* Department */}
                      <td className="px-4 py-3 text-slate-300 font-medium">
                        {cam.department}
                      </td>

                      {/* Location & GPS */}
                      <td className="px-4 py-3">
                        <div className="text-slate-300 truncate max-w-[180px]" title={cam.location_name}>
                          {cam.location_name}
                        </div>
                        {cam.has_valid_coordinates ? (
                          <span className="font-mono text-[10px] text-emerald-400 flex items-center space-x-1 mt-0.5">
                            <MapPin className="w-3 h-3 inline" />
                            <span>{cam.latitude?.toFixed(4)}°N, {cam.longitude?.toFixed(4)}°E</span>
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-500 font-mono">No GPS mapped</span>
                        )}
                      </td>

                      {/* Source & Connectivity */}
                      <td className="px-4 py-3">
                        <div className="flex items-center space-x-1.5">
                          {cam.source_type === 'RECORDED_FOOTAGE' ? (
                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20">
                              <Film className="w-3 h-3" />
                              <span>RECORDED</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-300 border border-blue-500/20">
                              <Radio className="w-3 h-3" />
                              <span>LIVE RTSP</span>
                            </span>
                          )}
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-slate-800 text-slate-300">
                            {cam.connectivity_type}
                          </span>
                        </div>
                      </td>

                      {/* Registration Status */}
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                            isOnline
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : isOffline
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                              : isMaint
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                              : 'bg-slate-800 text-slate-300 border border-slate-700'
                          }`}
                        >
                          {cam.status}
                        </span>
                      </td>

                      {/* Stream Session Status */}
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase flex items-center space-x-1 w-fit ${
                            cam.stream_status === 'CONNECTED'
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : cam.stream_status === 'ERROR'
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                              : cam.stream_status === 'NOT_CONFIGURED'
                              ? 'bg-blue-950/40 text-blue-300 border border-blue-800/40'
                              : 'bg-slate-800 text-slate-400 border border-slate-700'
                          }`}
                        >
                          {cam.stream_status === 'CONNECTED' && (
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                          )}
                          <span>{cam.stream_status}</span>
                        </span>
                      </td>

                      {/* Health Summary */}
                      <td className="px-4 py-3 text-slate-300 max-w-[200px]">
                        <p className="text-[11px] truncate" title={cam.health_summary}>
                          {cam.health_summary}
                        </p>
                        {cam.error_message && (
                          <p className="text-[10px] text-rose-400 truncate mt-0.5" title={cam.error_message}>
                            Reason: {cam.error_message}
                          </p>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end space-x-1.5">
                          <button
                            onClick={() => onNavigateToViewer && onNavigateToViewer(cam)}
                            title="Open in Unified Viewer"
                            className="p-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/40 text-blue-300 transition"
                          >
                            <Tv className="w-3.5 h-3.5" />
                          </button>

                          <button
                            onClick={() => onNavigateToGis && onNavigateToGis(cam)}
                            title="Locate on GIS Map"
                            className="p-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/40 text-emerald-300 transition"
                          >
                            <MapPin className="w-3.5 h-3.5" />
                          </button>

                          <button
                            onClick={() => onOpenDetailsModal && onOpenDetailsModal(cam)}
                            title="View Camera Details"
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
