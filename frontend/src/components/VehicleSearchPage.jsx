import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  Shield,
  Car,
  MapPin,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ZoomIn,
  Play,
  FileCheck,
  Sparkles,
  ExternalLink,
  Layers,
  X,
  Calendar,
  Filter,
  RefreshCw,
  Eye,
  Bell,
  ArrowDown,
  Navigation,
  ChevronRight,
  Info,
  Radio,
  SlidersHorizontal,
} from 'lucide-react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';

// Map controller to center on focused step or fit bounds
function MovementMapController({ focusedCoords, allCoords }) {
  const map = useMap();

  useEffect(() => {
    if (focusedCoords && focusedCoords[0] && focusedCoords[1]) {
      map.flyTo(focusedCoords, 14, { duration: 1.0 });
    } else if (allCoords && allCoords.length > 0) {
      const bounds = L.latLngBounds(allCoords);
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
    }
  }, [focusedCoords, allCoords, map]);

  return null;
}

// Generate numbered sequence pin
function createSequencePinIcon(stepNumber, isSelected) {
  const bg = isSelected ? '#f43f5e' : '#2563eb';
  const border = isSelected ? '#ffffff' : '#93c5fd';
  const shadow = isSelected ? 'rgba(244, 63, 94, 0.8)' : 'rgba(37, 99, 235, 0.7)';

  return L.divIcon({
    className: 'custom-sequence-pin',
    html: `
      <div style="
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: ${bg};
        border: 2.5px solid ${border};
        color: #ffffff;
        font-weight: 900;
        font-family: monospace;
        font-size: 13px;
        box-shadow: 0 0 12px ${shadow};
        cursor: pointer;
        transition: transform 0.2s;
      ">
        ${stepNumber}
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18],
  });
}

export default function VehicleSearchPage({
  initialPlate = '',
  onPlayFootageEvidence,
  onNavigateToAlerts,
}) {
  const [plateInput, setPlateInput] = useState(initialPlate);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState(null);

  // Filters State
  const [showFilters, setShowFilters] = useState(false);
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [department, setDepartment] = useState('');
  const [cameraFilterId, setCameraFilterId] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [allCameras, setAllCameras] = useState([]);

  // UI View Mode: 'map' | 'timeline' | 'table'
  const [activeSubTab, setActiveSubTab] = useState('map');
  const [showSequenceLine, setShowSequenceLine] = useState(true);
  const [focusedStep, setFocusedStep] = useState(null);
  const [zoomedCrop, setZoomedCrop] = useState(null);

  // Normalized key preview
  const normalizedPreview = plateInput.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();

  // Load cameras for filter dropdown
  useEffect(() => {
    fetch('/api/cameras?limit=500')
      .then((res) => res.json())
      .then((cams) => setAllCameras(cams || []))
      .catch((err) => console.error('Failed to load cameras list:', err));
  }, []);

  // Trigger search on mount if initialPlate is provided
  useEffect(() => {
    if (initialPlate) {
      setPlateInput(initialPlate);
      executeSearch(initialPlate);
    }
  }, [initialPlate]);

  const executeSearch = async (plateToSearch) => {
    const queryTerm = (plateToSearch !== undefined ? plateToSearch : plateInput).trim();
    if (!queryTerm) {
      setError('Please enter a vehicle registration number to search.');
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(true);
    setFocusedStep(null);

    try {
      const params = new URLSearchParams();
      params.append('plate_text', queryTerm);
      if (startTime) params.append('start_time', startTime);
      if (endTime) params.append('end_time', endTime);
      if (department) params.append('department', department);
      if (cameraFilterId) params.append('camera_id', cameraFilterId);
      if (locationFilter.trim()) params.append('location', locationFilter.trim());
      params.append('limit', '200');

      const res = await fetch(`/api/vehicle-search?${params.toString()}`);
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Search request failed.');
      }

      const resultData = await res.json();
      setData(resultData);
    } catch (err) {
      console.error('Vehicle search error:', err);
      setError(err.message || 'Error executing vehicle search.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setPlateInput('');
    setData(null);
    setSearched(false);
    setError(null);
    setFocusedStep(null);
    setStartTime('');
    setEndTime('');
    setDepartment('');
    setCameraFilterId('');
    setLocationFilter('');
  };

  // Collect map coordinates from sequence steps
  const validSequencePoints = data?.observed_sequence
    ? data.observed_sequence
        .filter((step) => step.has_valid_coordinates && step.latitude && step.longitude)
        .map((step) => [step.latitude, step.longitude])
    : [];

  const centerPosition =
    validSequencePoints.length > 0 ? validSequencePoints[0] : [23.0225, 72.5714]; // Ahmedabad default

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Search & Filter Card */}
      <div className="bg-[#0b1424] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2.5">
              <div className="p-2 bg-blue-600/20 border border-blue-500/40 rounded-xl text-blue-400">
                <Search className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white tracking-tight">
                  Vehicle Movement History & Observed Detection Sequence
                </h1>
                <p className="text-xs text-slate-400">
                  Search vehicle license plate sightings across all registered Gujarat CCTV cameras.
                </p>
              </div>
            </div>
          </div>

          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition ${
              showFilters
                ? 'bg-blue-600/20 border-blue-500/50 text-blue-300'
                : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>{showFilters ? 'Hide Filters' : 'Advanced Filters'}</span>
          </button>
        </div>

        {/* Search Bar Input */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            executeSearch();
          }}
          className="flex flex-col sm:flex-row items-center gap-3 pt-2"
        >
          <div className="relative flex-1 w-full">
            <Search className="w-5 h-5 text-slate-500 absolute left-3.5 top-3" />
            <input
              type="text"
              value={plateInput}
              onChange={(e) => setPlateInput(e.target.value)}
              placeholder="Enter Vehicle Plate Number (e.g. GJ 01 AB 1234 or CGCE)..."
              className="w-full pl-11 pr-4 py-2.5 bg-[#060c18] border border-slate-700 rounded-xl text-white font-mono text-sm uppercase placeholder-slate-500 focus:outline-none focus:border-blue-500 tracking-wider shadow-inner"
            />
          </div>

          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <button
              type="submit"
              disabled={loading || !plateInput.trim()}
              className="flex-1 sm:flex-initial flex items-center justify-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-lg shadow-blue-600/30 transition"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Search Vehicle</span>
                </>
              )}
            </button>

            {searched && (
              <button
                type="button"
                onClick={handleClear}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl transition"
              >
                Clear
              </button>
            )}
          </div>
        </form>

        {/* Live Normalized Key Preview */}
        {normalizedPreview && (
          <div className="flex items-center space-x-2 text-[11px] text-slate-400 pl-1">
            <span>Normalized Search Key:</span>
            <span className="font-mono px-2 py-0.5 bg-blue-950/50 text-blue-300 border border-blue-800/40 rounded font-bold">
              {normalizedPreview}
            </span>
          </div>
        )}

        {/* Collapsible Advanced Filters */}
        {showFilters && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 p-4 bg-[#070d1a] border border-slate-800 rounded-xl animate-fadeIn">
            {/* Start Time */}
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                From Date / Time
              </label>
              <input
                type="datetime-local"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-[#050912] border border-slate-700 rounded-lg text-slate-200 text-xs focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* End Time */}
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                To Date / Time
              </label>
              <input
                type="datetime-local"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-[#050912] border border-slate-700 rounded-lg text-slate-200 text-xs focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Department */}
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Department / Branch
              </label>
              <select
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-[#050912] border border-slate-700 rounded-lg text-slate-200 text-xs focus:outline-none focus:border-blue-500"
              >
                <option value="">All Departments</option>
                <option value="Traffic Branch">Traffic Branch</option>
                <option value="Crime Branch">Crime Branch</option>
                <option value="Special Operations Group (SOG)">Special Operations Group (SOG)</option>
                <option value="Surveillance Squad">Surveillance Squad</option>
                <option value="Gandhinagar HQ">Gandhinagar HQ</option>
              </select>
            </div>

            {/* Specific Camera */}
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Filter by Camera
              </label>
              <select
                value={cameraFilterId}
                onChange={(e) => setCameraFilterId(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-[#050912] border border-slate-700 rounded-lg text-slate-200 text-xs focus:outline-none focus:border-blue-500"
              >
                <option value="">All Registered Cameras</option>
                {allCameras.map((cam) => (
                  <option key={cam.id} value={cam.id}>
                    {cam.camera_code} - {cam.camera_name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center space-x-2 p-4 bg-rose-500/15 border border-rose-500/40 rounded-xl text-rose-300 text-xs font-medium">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {data && searched && (
        <div className="space-y-6">
          {/* Summary KPI Banner */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-3.5 shadow">
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                Total Sightings
              </p>
              <h3 className="text-xl font-black text-white mt-0.5">
                {data.summary.total_observations}
              </h3>
              <p className="text-[10px] text-slate-500">ANPR observations</p>
            </div>

            <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-3.5 shadow">
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                Unique Cameras
              </p>
              <h3 className="text-xl font-black text-blue-400 mt-0.5">
                {data.summary.unique_cameras_count}
              </h3>
              <p className="text-[10px] text-blue-500/80">CCTV vantage points</p>
            </div>

            <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-3.5 shadow">
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                Departments
              </p>
              <h3 className="text-xl font-black text-emerald-400 mt-0.5">
                {data.summary.departments_count}
              </h3>
              <p className="text-[10px] text-emerald-500/80">Jurisdictions</p>
            </div>

            <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-3.5 shadow">
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                First Observed
              </p>
              <h3 className="text-xs font-bold text-amber-300 mt-1 font-mono">
                {data.summary.first_observed_at || 'N/A'}
              </h3>
              <p className="text-[10px] text-slate-500">Initial recorded sighting</p>
            </div>

            <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-3.5 shadow">
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                Last Observed
              </p>
              <h3 className="text-xs font-bold text-amber-300 mt-1 font-mono">
                {data.summary.last_observed_at || 'N/A'}
              </h3>
              <p className="text-[10px] text-slate-500">
                {data.summary.duration_span ? `Span: ${data.summary.duration_span}` : 'Latest sighting'}
              </p>
            </div>
          </div>

          {/* Watchlist / Alert History Notification (Milestone 7 Integration) */}
          {data.alerts_history && data.alerts_history.length > 0 && (
            <div className="p-4 bg-rose-950/40 border border-rose-600/70 rounded-2xl shadow-xl space-y-3 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="p-2 bg-rose-600 text-white rounded-lg">
                    <Bell className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white flex items-center space-x-2">
                      <span>WATCHLIST SURVEILLANCE ALERTS DETECTED</span>
                      <span className="px-2 py-0.5 rounded text-[10px] bg-rose-600 text-white font-mono">
                        {data.alerts_history.length} ALERTS
                      </span>
                    </h4>
                    <p className="text-xs text-rose-300">
                      This searched vehicle matched active police surveillance watchlist rules.
                    </p>
                  </div>
                </div>

                {onNavigateToAlerts && (
                  <button
                    onClick={() => onNavigateToAlerts(data.query_plate_normalized)}
                    className="flex items-center space-x-1.5 px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-lg transition shadow"
                  >
                    <span>Open in Alert Center</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                {data.alerts_history.slice(0, 2).map((a) => (
                  <div
                    key={a.id}
                    className="p-2.5 bg-[#090e1a] border border-rose-800/40 rounded-lg text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-900/60 text-rose-200 border border-rose-700/50">
                        {a.severity} SEVERITY • {a.status}
                      </span>
                      <span className="font-mono text-[10px] text-slate-400">
                        {a.formatted_timestamp}
                      </span>
                    </div>
                    <p className="text-slate-200 text-[11px] font-medium">{a.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* View Mode Tabs & Disclaimer */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setActiveSubTab('map')}
                className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition ${
                  activeSubTab === 'map'
                    ? 'bg-blue-600/20 text-blue-300 border border-blue-500/40 shadow-inner'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
                }`}
              >
                <MapPin className="w-3.5 h-3.5" />
                <span>GIS Movement Map</span>
              </button>

              <button
                onClick={() => setActiveSubTab('timeline')}
                className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition ${
                  activeSubTab === 'timeline'
                    ? 'bg-blue-600/20 text-blue-300 border border-blue-500/40 shadow-inner'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
                }`}
              >
                <Clock className="w-3.5 h-3.5" />
                <span>Chronological Timeline ({data.observed_sequence.length} Steps)</span>
              </button>

              <button
                onClick={() => setActiveSubTab('table')}
                className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition ${
                  activeSubTab === 'table'
                    ? 'bg-blue-600/20 text-blue-300 border border-blue-500/40 shadow-inner'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Sighting Logs ({data.observations.length})</span>
              </button>
            </div>

            {/* Ethical Disclaimer */}
            <div className="flex items-center space-x-1.5 text-[11px] text-slate-400 bg-slate-900/60 px-3 py-1 rounded-lg border border-slate-800">
              <Info className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
              <span>
                Observed camera detections based on available CCTV records. Does not represent continuous GPS tracking.
              </span>
            </div>
          </div>

          {/* Tab 1: GIS Detection Map */}
          {activeSubTab === 'map' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-3">
                  <label className="flex items-center space-x-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={showSequenceLine}
                      onChange={(e) => setShowSequenceLine(e.target.checked)}
                      className="rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-0"
                    />
                    <span className="text-slate-300 font-semibold">
                      Draw Observed Detection Sequence Line
                    </span>
                  </label>
                  <span className="text-[11px] text-slate-500">
                    ({validSequencePoints.length} cameras mapped)
                  </span>
                </div>

                {focusedStep && (
                  <button
                    onClick={() => setFocusedStep(null)}
                    className="text-[11px] text-blue-400 hover:underline"
                  >
                    Reset Map View
                  </button>
                )}
              </div>

              {/* Map Container */}
              <div className="bg-[#080f1c] border border-slate-800 rounded-2xl overflow-hidden shadow-2xl h-[520px] relative">
                {validSequencePoints.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center p-8 text-center text-slate-400">
                    <MapPin className="w-10 h-10 text-slate-600 mb-2" />
                    <p className="text-sm font-semibold text-slate-300">
                      Geographic coordinates unavailable for these observations
                    </p>
                    <p className="text-xs text-slate-500 mt-1 max-w-sm">
                      Please view the Chronological Timeline or Sighting Logs tab for full observation details and video playback.
                    </p>
                  </div>
                ) : (
                  <MapContainer
                    center={centerPosition}
                    zoom={12}
                    className="h-full w-full"
                    zoomControl={true}
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    <MovementMapController
                      focusedCoords={
                        focusedStep && focusedStep.latitude && focusedStep.longitude
                          ? [focusedStep.latitude, focusedStep.longitude]
                          : null
                      }
                      allCoords={validSequencePoints}
                    />

                    {/* Sequential Dashed Polyline */}
                    {showSequenceLine && validSequencePoints.length >= 2 && (
                      <Polyline
                        positions={validSequencePoints}
                        pathOptions={{
                          color: '#3b82f6',
                          weight: 3.5,
                          dashArray: '8, 8',
                          opacity: 0.85,
                        }}
                      />
                    )}

                    {/* Numbered Sequence Markers */}
                    {data.observed_sequence.map((step) => {
                      if (!step.has_valid_coordinates || !step.latitude || !step.longitude) {
                        return null;
                      }

                      const isSelected = focusedStep?.step_number === step.step_number;

                      return (
                        <Marker
                          key={step.step_number}
                          position={[step.latitude, step.longitude]}
                          icon={createSequencePinIcon(step.step_number, isSelected)}
                          eventHandlers={{
                            click: () => setFocusedStep(step),
                          }}
                        >
                          <Popup className="custom-police-popup">
                            <div className="p-3 bg-[#0b1424] text-slate-100 rounded-xl space-y-2 min-w-[220px]">
                              <div className="flex items-center justify-between border-b border-slate-700 pb-1.5">
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-600 text-white font-mono">
                                  STEP {step.step_number}
                                </span>
                                <span className="text-[10px] text-slate-400 font-mono">
                                  {step.camera_code}
                                </span>
                              </div>

                              <div>
                                <h4 className="font-bold text-xs text-white">
                                  {step.camera_name}
                                </h4>
                                <p className="text-[11px] text-slate-400">{step.location_name}</p>
                              </div>

                              <div className="grid grid-cols-2 gap-1.5 pt-1 text-[10px] font-mono">
                                <div className="p-1 bg-[#060c18] rounded border border-slate-800">
                                  <span className="text-slate-500">TIME:</span>{' '}
                                  <span className="text-amber-300 font-bold">{step.time_window_display}</span>
                                </div>
                                <div className="p-1 bg-[#060c18] rounded border border-slate-800">
                                  <span className="text-slate-500">CONF:</span>{' '}
                                  <span className="text-emerald-300 font-bold">{step.best_confidence_percent}</span>
                                </div>
                              </div>

                              {onPlayFootageEvidence && (
                                <button
                                  onClick={() =>
                                    onPlayFootageEvidence(
                                      { id: step.primary_footage_id, filename: `Footage #${step.primary_footage_id}` },
                                      {
                                        id: step.camera_id,
                                        camera_name: step.camera_name,
                                        camera_code: step.camera_code,
                                        location_name: step.location_name,
                                      },
                                      step.first_timestamp_seconds
                                    )
                                  }
                                  className="w-full flex items-center justify-center space-x-1.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition shadow mt-1"
                                >
                                  <Play className="w-3.5 h-3.5 fill-current" />
                                  <span>View Detection Video</span>
                                </button>
                              )}
                            </div>
                          </Popup>
                        </Marker>
                      );
                    })}
                  </MapContainer>
                )}
              </div>
            </div>
          )}

          {/* Tab 2: Chronological Observed Camera Detection Sequence Timeline */}
          {activeSubTab === 'timeline' && (
            <div className="space-y-4">
              <div className="space-y-3">
                {data.observed_sequence.map((step, idx) => {
                  const isLast = idx === data.observed_sequence.length - 1;

                  return (
                    <div key={step.step_number} className="flex items-start space-x-4">
                      {/* Left Step Badge & Connecting Line */}
                      <div className="flex flex-col items-center flex-shrink-0">
                        <div
                          onClick={() => setFocusedStep(step)}
                          className={`w-10 h-10 rounded-full flex items-center justify-center font-black font-mono text-sm border-2 cursor-pointer transition shadow-lg ${
                            focusedStep?.step_number === step.step_number
                              ? 'bg-rose-600 border-white text-white ring-4 ring-rose-600/30'
                              : 'bg-blue-600 border-blue-400 text-white hover:scale-105'
                          }`}
                        >
                          {step.step_number}
                        </div>
                        {!isLast && (
                          <div className="w-0.5 h-16 bg-gradient-to-b from-blue-500/60 to-slate-700 my-1"></div>
                        )}
                      </div>

                      {/* Right Sighting Content Card */}
                      <div className="flex-1 bg-[#0b1424] border border-slate-800 hover:border-slate-700 rounded-2xl p-5 shadow-lg space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800">
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="text-sm font-bold text-white tracking-wide">
                                {step.camera_name}
                              </span>
                              <span className="px-2 py-0.5 bg-blue-950/60 text-blue-300 border border-blue-800/40 rounded text-[10px] font-mono">
                                {step.camera_code}
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 flex items-center space-x-1 mt-0.5">
                              <MapPin className="w-3.5 h-3.5 text-blue-400" />
                              <span>{step.location_name}</span>
                              <span className="text-slate-600">•</span>
                              <span className="text-slate-400">{step.department}</span>
                            </p>
                          </div>

                          <div className="flex items-center space-x-2">
                            <span className="px-2.5 py-1 bg-amber-500/15 text-amber-300 border border-amber-500/40 rounded-lg text-xs font-mono font-bold flex items-center space-x-1">
                              <Clock className="w-3.5 h-3.5" />
                              <span>{step.time_window_display}</span>
                            </span>
                          </div>
                        </div>

                        {/* Details Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                          {/* Sighting stats & Crop preview */}
                          <div className="md:col-span-8 flex items-center space-x-4">
                            {step.primary_crop_url ? (
                              <div
                                onClick={() => setZoomedCrop(step.primary_crop_url)}
                                className="cursor-pointer group relative flex-shrink-0 w-24 h-14 bg-black rounded-lg border border-slate-700 overflow-hidden"
                                title="Click to zoom plate crop"
                              >
                                <img
                                  src={step.primary_crop_url}
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

                            <div className="space-y-1 text-xs">
                              <div className="flex items-center space-x-2">
                                <span className="text-slate-400">Class:</span>
                                <span className="font-semibold text-slate-200 capitalize">
                                  {step.primary_vehicle_class}
                                </span>
                                <span className="text-slate-600">•</span>
                                <span className="text-slate-400">Sightings:</span>
                                <span className="font-mono text-blue-400 font-bold">
                                  {step.sighting_count} frame(s)
                                </span>
                              </div>
                              <div className="flex items-center space-x-2">
                                <span className="text-slate-400">OCR Confidence:</span>
                                <span className="font-mono text-emerald-400 font-bold">
                                  {step.best_confidence_percent}
                                </span>
                              </div>
                              {step.first_observed_at && (
                                <p className="text-[11px] text-slate-500 font-mono">
                                  Date: {new Date(step.first_observed_at).toLocaleString()}
                                </p>
                              )}
                            </div>
                          </div>

                          {/* Action Buttons */}
                          <div className="md:col-span-4 flex items-center justify-end space-x-2">
                            {step.has_valid_coordinates && (
                              <button
                                onClick={() => {
                                  setFocusedStep(step);
                                  setActiveSubTab('map');
                                }}
                                className="flex items-center space-x-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition"
                              >
                                <MapPin className="w-3.5 h-3.5 text-blue-400" />
                                <span>Center on Map</span>
                              </button>
                            )}

                            {onPlayFootageEvidence && (
                              <button
                                onClick={() =>
                                  onPlayFootageEvidence(
                                    { id: step.primary_footage_id, filename: `Footage #${step.primary_footage_id}` },
                                    {
                                      id: step.camera_id,
                                      camera_name: step.camera_name,
                                      camera_code: step.camera_code,
                                      location_name: step.location_name,
                                    },
                                    step.first_timestamp_seconds
                                  )
                                }
                                className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition shadow"
                              >
                                <Play className="w-3.5 h-3.5 fill-current" />
                                <span>Jump to Detection</span>
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Tab 3: Detailed Sighting Logs Table */}
          {activeSubTab === 'table' && (
            <div className="bg-[#0b1424] border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-[#081120] text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                      <th className="py-3 px-4">Observation Time</th>
                      <th className="py-3 px-4">Camera</th>
                      <th className="py-3 px-4">Location & Dept</th>
                      <th className="py-3 px-4">Vehicle Class</th>
                      <th className="py-3 px-4">Plate Crop</th>
                      <th className="py-3 px-4">Confidence</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-xs">
                    {data.observations.map((obs) => (
                      <tr key={obs.id} className="hover:bg-slate-800/30 transition">
                        <td className="py-3.5 px-4 font-mono">
                          <div className="text-amber-300 font-bold">{obs.formatted_timestamp}</div>
                          <div className="text-[10px] text-slate-500">{obs.formatted_datetime}</div>
                        </td>

                        <td className="py-3.5 px-4">
                          <div className="font-bold text-white">{obs.camera_name}</div>
                          <div className="text-[10px] text-blue-400 font-mono">{obs.camera_code}</div>
                        </td>

                        <td className="py-3.5 px-4">
                          <div className="text-slate-200">{obs.location_name}</div>
                          <div className="text-[10px] text-slate-500">{obs.department}</div>
                        </td>

                        <td className="py-3.5 px-4 capitalize text-slate-300">
                          {obs.vehicle_class}
                          {obs.track_id && (
                            <span className="text-[10px] text-slate-500 block font-mono">
                              Track #{obs.track_id}
                            </span>
                          )}
                        </td>

                        <td className="py-3.5 px-4">
                          {obs.has_crop && obs.plate_crop_url ? (
                            <img
                              src={obs.plate_crop_url}
                              alt="Crop"
                              onClick={() => setZoomedCrop(obs.plate_crop_url)}
                              className="h-9 w-18 object-contain bg-black rounded border border-slate-700 cursor-pointer hover:scale-105 transition"
                              title="Click to zoom crop"
                            />
                          ) : (
                            <span className="text-slate-600 text-[10px]">No crop</span>
                          )}
                        </td>

                        <td className="py-3.5 px-4 font-mono font-bold text-emerald-400">
                          {obs.confidence_percent}
                        </td>

                        <td className="py-3.5 px-4 text-right">
                          {onPlayFootageEvidence && (
                            <button
                              onClick={() =>
                                onPlayFootageEvidence(
                                  { id: obs.footage_id, filename: obs.footage_filename },
                                  {
                                    id: obs.camera_id,
                                    camera_name: obs.camera_name,
                                    camera_code: obs.camera_code,
                                    location_name: obs.location_name,
                                  },
                                  obs.timestamp_seconds
                                )
                              }
                              className="inline-flex items-center space-x-1 px-2.5 py-1 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/40 rounded-lg text-xs font-bold transition"
                            >
                              <Play className="w-3 h-3 fill-current" />
                              <span>Play</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State: No Results Found */}
      {data && searched && data.observations.length === 0 && (
        <div className="bg-[#0b1424] border border-slate-800 rounded-2xl p-12 text-center text-slate-400 space-y-3">
          <Car className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-base font-bold text-white">No matching vehicle observations found</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            No CCTV ANPR sightings were found matching registration <span className="font-mono font-bold text-white">"{data.query_plate_raw}"</span>. Try another registration number or adjust the date/department search filters.
          </p>
        </div>
      )}

      {/* Initial State (Before searching) */}
      {!searched && (
        <div className="bg-[#0b1424]/60 border border-slate-800/80 rounded-2xl p-12 text-center text-slate-400 space-y-3">
          <Shield className="w-12 h-12 text-blue-500/60 mx-auto" />
          <h3 className="text-base font-bold text-white">Investigative Vehicle Surveillance Search</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Enter an authorized vehicle registration number above to reconstruct observed camera encounters, view detection sequence maps, and inspect recorded video evidence.
          </p>
          <div className="pt-2 flex items-center justify-center space-x-2 text-xs">
            <span className="text-slate-500">Quick Test Plates:</span>
            <button
              onClick={() => {
                setPlateInput('GJ01AB1234');
                executeSearch('GJ01AB1234');
              }}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-blue-300 rounded font-mono text-xs border border-slate-700 transition"
            >
              GJ01AB1234
            </button>
            <button
              onClick={() => {
                setPlateInput('CGCE');
                executeSearch('CGCE');
              }}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-emerald-300 rounded font-mono text-xs border border-slate-700 transition"
            >
              CGCE
            </button>
          </div>
        </div>
      )}

      {/* Plate Crop Zoom Modal */}
      {zoomedCrop && (
        <div
          onClick={() => setZoomedCrop(null)}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md cursor-pointer animate-fadeIn"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="bg-[#0b1424] border border-slate-700 rounded-2xl p-4 max-w-lg w-full text-center space-y-3"
          >
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-xs font-bold text-slate-300">ANPR High-Resolution License Plate Crop</span>
              <button
                onClick={() => setZoomedCrop(null)}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 bg-slate-800 rounded"
              >
                Close
              </button>
            </div>
            <div className="bg-black rounded-xl p-2 border border-slate-800">
              <img src={zoomedCrop} alt="Plate Zoom" className="w-full h-auto object-contain rounded-lg" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
