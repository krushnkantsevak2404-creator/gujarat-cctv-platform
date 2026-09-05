import React, { useState, useEffect } from 'react';
import {
  Bell,
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  Clock,
  Play,
  MapPin,
  Search,
  Filter,
  RefreshCw,
  Shield,
  ShieldAlert,
  Car,
  Check,
  Eye,
  ExternalLink,
  ChevronRight,
  Radio,
} from 'lucide-react';

const SEVERITY_CONFIG = {
  CRITICAL: {
    bg: 'bg-rose-950/60 border-rose-600/80 text-rose-300',
    badge: 'bg-rose-600 text-white animate-pulse',
    border: 'border-rose-500/60',
    glow: 'shadow-rose-900/40',
  },
  HIGH: {
    bg: 'bg-orange-950/40 border-orange-600/60 text-orange-300',
    badge: 'bg-orange-600 text-white',
    border: 'border-orange-500/50',
    glow: 'shadow-orange-900/30',
  },
  MEDIUM: {
    bg: 'bg-yellow-950/30 border-yellow-600/50 text-yellow-300',
    badge: 'bg-yellow-600 text-slate-900 font-bold',
    border: 'border-yellow-500/40',
    glow: 'shadow-yellow-900/20',
  },
  LOW: {
    bg: 'bg-slate-900/60 border-slate-700 text-slate-300',
    badge: 'bg-slate-700 text-slate-200',
    border: 'border-slate-700',
    glow: 'shadow-slate-900/20',
  },
};

const STATUS_CONFIG = {
  NEW: {
    label: 'NEW ALERT',
    badge: 'bg-rose-500/20 text-rose-300 border-rose-500/50 ring-2 ring-rose-500/30 animate-pulse',
    icon: Bell,
  },
  ACKNOWLEDGED: {
    label: 'ACKNOWLEDGED',
    badge: 'bg-amber-500/20 text-amber-300 border-amber-500/50',
    icon: Clock,
  },
  RESOLVED: {
    label: 'RESOLVED',
    badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50',
    icon: CheckCircle2,
  },
};

export default function AlertsPage({
  initialPlateFilter = '',
  onPlayFootageEvidence,
  onLocateCameraOnGis,
}) {
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [plateFilter, setPlateFilter] = useState(initialPlateFilter);
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedCrop, setSelectedCrop] = useState(null);

  useEffect(() => {
    if (initialPlateFilter) {
      setPlateFilter(initialPlateFilter);
    }
  }, [initialPlateFilter]);

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/alerts/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch alert stats:', err);
    }
  };

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (plateFilter.trim()) params.append('plate', plateFilter.trim());
      if (statusFilter) params.append('status', statusFilter);
      if (severityFilter) params.append('severity', severityFilter);
      params.append('limit', '100');

      const res = await fetch(`/api/alerts?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setAlerts(data);
      }
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  const refreshAll = () => {
    fetchStats();
    fetchAlerts();
  };

  useEffect(() => {
    refreshAll();
  }, [plateFilter, statusFilter, severityFilter]);

  // Periodic Auto-refresh for live alerts
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchStats();
      fetchAlerts();
    }, 6000);
    return () => clearInterval(interval);
  }, [autoRefresh, plateFilter, statusFilter, severityFilter]);

  // Acknowledge Action
  const handleAcknowledge = async (alertId) => {
    try {
      const res = await fetch(`/api/alerts/${alertId}/acknowledge`, {
        method: 'PATCH',
      });
      if (res.ok) {
        refreshAll();
      }
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  // Resolve Action
  const handleResolve = async (alertId) => {
    try {
      const res = await fetch(`/api/alerts/${alertId}/resolve`, {
        method: 'PATCH',
      });
      if (res.ok) {
        refreshAll();
      }
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Alert Metrics Dashboard */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Alerts */}
        <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-4 shadow-lg flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Total Surveillance Alerts
            </p>
            <h3 className="text-2xl font-black text-white mt-1">
              {stats ? stats.total_alerts : alerts.length}
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">Matched CCTV sightings</p>
          </div>
          <div className="p-3 bg-blue-600/15 border border-blue-500/30 rounded-xl text-blue-400">
            <Bell className="w-6 h-6" />
          </div>
        </div>

        {/* New / Action Required */}
        <div className="bg-[#0b1424] border border-rose-900/40 rounded-xl p-4 shadow-lg flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
              <p className="text-[11px] font-bold text-rose-400 uppercase tracking-wider">
                New Action Required
              </p>
            </div>
            <h3 className="text-2xl font-black text-rose-400 mt-1">
              {stats ? stats.new_alerts : alerts.filter((a) => a.status === 'NEW').length}
            </h3>
            <p className="text-[11px] text-rose-500/80 mt-0.5">Unacknowledged events</p>
          </div>
          <div className="p-3 bg-rose-600/20 border border-rose-500/40 rounded-xl text-rose-400 animate-pulse">
            <AlertOctagon className="w-6 h-6" />
          </div>
        </div>

        {/* Acknowledged */}
        <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-4 shadow-lg flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Under Investigation
            </p>
            <h3 className="text-2xl font-black text-amber-400 mt-1">
              {stats ? stats.acknowledged_alerts : alerts.filter((a) => a.status === 'ACKNOWLEDGED').length}
            </h3>
            <p className="text-[11px] text-amber-500/80 mt-0.5">Acknowledged by officer</p>
          </div>
          <div className="p-3 bg-amber-600/15 border border-amber-500/30 rounded-xl text-amber-400">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        {/* Resolved */}
        <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-4 shadow-lg flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Resolved Cases
            </p>
            <h3 className="text-2xl font-black text-emerald-400 mt-1">
              {stats ? stats.resolved_alerts : alerts.filter((a) => a.status === 'RESOLVED').length}
            </h3>
            <p className="text-[11px] text-emerald-500/80 mt-0.5">Closed observations</p>
          </div>
          <div className="p-3 bg-emerald-600/15 border border-emerald-500/30 rounded-xl text-emerald-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Toolbar & Live Status Filter */}
      <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-4 shadow-lg space-y-3">
        <div className="flex flex-col md:flex-row items-center justify-between gap-3">
          {/* Plate Search */}
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Filter by plate number (e.g. GJ01)..."
              value={plateFilter}
              onChange={(e) => setPlateFilter(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-[#060c18] border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500 uppercase font-mono"
            />
          </div>

          {/* Controls */}
          <div className="flex items-center space-x-3 w-full md:w-auto justify-end">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition ${
                autoRefresh
                  ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300'
                  : 'bg-slate-800 border-slate-700 text-slate-400'
              }`}
            >
              <Radio className={`w-3.5 h-3.5 ${autoRefresh ? 'animate-pulse text-emerald-400' : ''}`} />
              <span>{autoRefresh ? 'Live Polling: ON' : 'Live Polling: OFF'}</span>
            </button>

            <button
              onClick={refreshAll}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition"
              title="Refresh Alerts Feed"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filter Rows */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2 border-t border-slate-800/60">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 bg-[#060c18] border border-slate-700/60 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-rose-500"
          >
            <option value="">All Statuses (NEW, Acknowledged, Resolved)</option>
            <option value="NEW">🚨 NEW (Unacknowledged)</option>
            <option value="ACKNOWLEDGED">⏳ Acknowledged</option>
            <option value="RESOLVED">✅ Resolved</option>
          </select>

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 bg-[#060c18] border border-slate-700/60 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-rose-500"
          >
            <option value="">All Severities (Critical, High, Medium, Low)</option>
            <option value="CRITICAL">Critical Severity</option>
            <option value="HIGH">High Severity</option>
            <option value="MEDIUM">Medium Severity</option>
            <option value="LOW">Low Severity</option>
          </select>
        </div>
      </div>

      {/* Alerts Feed List */}
      <div className="space-y-3">
        {loading && alerts.length === 0 ? (
          <div className="bg-[#0b1424] border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
            <RefreshCw className="w-8 h-8 animate-spin text-rose-500 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-300">Scanning for automated vehicle alerts...</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="bg-[#0b1424] border border-slate-800 rounded-2xl p-12 text-center text-slate-400 space-y-2">
            <Shield className="w-10 h-10 text-emerald-500/60 mx-auto" />
            <h4 className="text-base font-bold text-white">No Vehicle Alerts Found</h4>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              No watchlist plates matched during ANPR video processing for the current filter criteria.
            </p>
          </div>
        ) : (
          alerts.map((alert) => {
            const sev = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.HIGH;
            const stat = STATUS_CONFIG[alert.status] || STATUS_CONFIG.NEW;
            const StatusIcon = stat.icon;

            return (
              <div
                key={alert.id}
                className={`bg-[#0b1424] border ${sev.border} rounded-2xl p-5 shadow-xl transition hover:border-slate-600 space-y-4`}
              >
                {/* Top Row: Severity, Status & Plate Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-3 border-b border-slate-800/80">
                  <div className="flex items-center space-x-2.5 flex-wrap gap-y-1.5">
                    {/* Severity Badge */}
                    <span className={`px-2.5 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${sev.badge}`}>
                      {alert.severity} SEVERITY
                    </span>

                    {/* Status Badge */}
                    <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${stat.badge}`}>
                      <StatusIcon className="w-3 h-3" />
                      <span>{stat.label}</span>
                    </span>

                    {/* Category */}
                    {alert.watchlist_category && (
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-950/60 text-purple-300 border border-purple-700/50 uppercase">
                        {alert.watchlist_category.replace('_', ' ')}
                      </span>
                    )}

                    {/* Vehicle Class */}
                    <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700 capitalize">
                      {alert.vehicle_class}
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-400 font-mono">
                    Alert #{alert.id} • {new Date(alert.created_at).toLocaleTimeString()}
                  </div>
                </div>

                {/* Center Content Row: Plate, Message & Camera Details */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                  {/* Plate Display + Crop Preview (3 cols) */}
                  <div className="md:col-span-4 flex items-center space-x-3">
                    {alert.has_crop && alert.plate_crop_url ? (
                      <div
                        onClick={() => setSelectedCrop(alert.plate_crop_url)}
                        className="cursor-pointer group relative flex-shrink-0 w-24 h-14 bg-black rounded-lg border border-slate-700 overflow-hidden"
                        title="Click to zoom plate crop"
                      >
                        <img
                          src={alert.plate_crop_url}
                          alt="Plate Crop"
                          className="w-full h-full object-contain group-hover:scale-105 transition"
                        />
                        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                          <Eye className="w-4 h-4 text-white" />
                        </div>
                      </div>
                    ) : (
                      <div className="flex-shrink-0 w-20 h-14 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-center text-slate-600">
                        <Car className="w-6 h-6" />
                      </div>
                    )}

                    <div>
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">
                        Monitored License Plate
                      </div>
                      <div className="text-base font-black font-mono text-white tracking-wider px-2 py-0.5 bg-[#060c18] border border-slate-700 rounded-md inline-block mt-0.5 shadow-inner">
                        {alert.plate_text}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-1">
                        Confidence:{' '}
                        <span className="text-emerald-400 font-mono font-bold">
                          {alert.confidence_percent}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Machine Message & Location Info (5 cols) */}
                  <div className="md:col-span-5 space-y-1.5">
                    <p className="text-xs text-slate-200 font-medium leading-relaxed">
                      {alert.message}
                    </p>
                    {alert.watchlist_description && (
                      <p className="text-[11px] text-rose-300/90 italic bg-rose-950/20 px-2 py-1 rounded border border-rose-900/30">
                        Case Note: {alert.watchlist_description}
                      </p>
                    )}
                    <div className="flex items-center space-x-3 text-[11px] text-slate-400 pt-1">
                      <span className="flex items-center space-x-1">
                        <MapPin className="w-3.5 h-3.5 text-blue-400" />
                        <span className="text-slate-300 font-semibold">{alert.camera_name}</span>
                        <span className="text-slate-500 font-mono">({alert.camera_code})</span>
                      </span>
                      <span className="text-slate-500">•</span>
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3.5 h-3.5 text-amber-400" />
                        <span className="font-mono text-amber-300">{alert.formatted_timestamp}</span>
                      </span>
                    </div>
                  </div>

                  {/* Action Buttons (3 cols) */}
                  <div className="md:col-span-3 flex flex-col sm:flex-row md:flex-col gap-2 justify-end">
                    {/* View Video Evidence (Click to seek) */}
                    <button
                      onClick={() =>
                        onPlayFootageEvidence &&
                        onPlayFootageEvidence(
                          { id: alert.footage_id, filename: `Footage #${alert.footage_id}` },
                          {
                            id: alert.camera_id,
                            camera_name: alert.camera_name,
                            camera_code: alert.camera_code,
                            location_name: alert.location_name,
                            latitude: alert.latitude,
                            longitude: alert.longitude,
                          },
                          alert.timestamp_seconds
                        )
                      }
                      className="flex items-center justify-center space-x-1.5 px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/40 rounded-xl text-xs font-bold transition shadow"
                      title="Play CCTV footage seeked to exact detection second"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                      <span>Video Evidence ({alert.formatted_timestamp})</span>
                    </button>

                    {/* Locate on GIS Map */}
                    {alert.latitude && alert.longitude && (
                      <button
                        onClick={() =>
                          onLocateCameraOnGis &&
                          onLocateCameraOnGis({
                            id: alert.camera_id,
                            camera_name: alert.camera_name,
                            camera_code: alert.camera_code,
                            location_name: alert.location_name,
                            latitude: alert.latitude,
                            longitude: alert.longitude,
                          })
                        }
                        className="flex items-center justify-center space-x-1.5 px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 rounded-xl text-xs font-bold transition shadow"
                        title="Locate camera on GIS Map"
                      >
                        <MapPin className="w-3.5 h-3.5" />
                        <span>Locate on GIS Map</span>
                      </button>
                    )}

                    {/* Status Transition Buttons */}
                    <div className="flex items-center space-x-2 pt-1">
                      {alert.status === 'NEW' && (
                        <button
                          onClick={() => handleAcknowledge(alert.id)}
                          className="flex-1 flex items-center justify-center space-x-1 px-2.5 py-1 bg-amber-600 hover:bg-amber-500 text-slate-950 rounded-lg text-[11px] font-bold transition shadow"
                        >
                          <Check className="w-3 h-3" />
                          <span>Acknowledge</span>
                        </button>
                      )}

                      {alert.status !== 'RESOLVED' && (
                        <button
                          onClick={() => handleResolve(alert.id)}
                          className="flex-1 flex items-center justify-center space-x-1 px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-[11px] font-bold transition shadow"
                        >
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Resolve Case</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Plate Crop Zoom Modal */}
      {selectedCrop && (
        <div
          onClick={() => setSelectedCrop(null)}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md cursor-pointer"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="bg-[#0b1424] border border-slate-700 rounded-2xl p-4 max-w-lg w-full text-center space-y-3"
          >
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-xs font-bold text-slate-300">ANPR High-Resolution Plate Crop Evidence</span>
              <button
                onClick={() => setSelectedCrop(null)}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 bg-slate-800 rounded"
              >
                Close
              </button>
            </div>
            <div className="bg-black rounded-xl p-2 border border-slate-800">
              <img src={selectedCrop} alt="License Plate Zoom" className="w-full h-auto object-contain rounded-lg" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
