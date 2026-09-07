import React, { useState, useEffect, useRef } from 'react';
import {
  Grid,
  Maximize2,
  Minimize2,
  X,
  Plus,
  Search,
  Filter,
  RefreshCw,
  MapPin,
  Play,
  Pause,
  Volume2,
  VolumeX,
  RotateCcw,
  Info,
  Shield,
  ShieldAlert,
  AlertTriangle,
  Camera as CamIcon,
  Video,
  Radio,
  Layers,
  ChevronDown,
  SlidersHorizontal,
  ExternalLink,
  CheckCircle2,
  Tv,
} from 'lucide-react';
import CameraDetailsModal from './CameraDetailsModal';

// Grid Layout Configurations
const GRID_LAYOUTS = [
  { id: '1x1', label: '1x1', name: 'Single View', slots: 1, cols: 'grid-cols-1', rows: 'grid-rows-1' },
  { id: '2x1', label: '2x1', name: '2-Split View', slots: 2, cols: 'grid-cols-1 md:grid-cols-2', rows: '' },
  { id: '2x2', label: '2x2', name: '4-Grid (Default)', slots: 4, cols: 'grid-cols-1 md:grid-cols-2', rows: '' },
  { id: '3x2', label: '3x2', name: '6-Grid View', slots: 6, cols: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3', rows: '' },
  { id: '3x3', label: '3x3', name: '9-Grid View', slots: 9, cols: 'grid-cols-1 md:grid-cols-3', rows: '' },
];

export default function UnifiedViewerPage({
  initialConfig = null,
  onOpenInGis = () => {},
  onOpenAlerts = () => {},
  onOpenVehicleSearch = () => {},
}) {
  // Viewer Layout: default '2x2' (4 slots)
  const [layoutId, setLayoutId] = useState('2x2');
  const activeLayout = GRID_LAYOUTS.find((l) => l.id === layoutId) || GRID_LAYOUTS[2];

  // Grid slots state: Array of objects or null { camera, footageId, seekTime, autoPlay }
  const [gridSlots, setGridSlots] = useState(Array(4).fill(null));

  // Registered Cameras from Backend
  const [cameras, setCameras] = useState([]);
  const [loadingCameras, setLoadingCameras] = useState(true);
  const [viewerStats, setViewerStats] = useState(null);

  // Camera Selection Sidebar & Filters
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceTypeFilter, setSourceTypeFilter] = useState('');
  const [cameraTypeFilter, setCameraTypeFilter] = useState('');

  // Selected Camera for Details Modal
  const [detailsCamera, setDetailsCamera] = useState(null);

  // Quick Camera Picker for a specific empty slot index
  const [pickerSlotIndex, setPickerSlotIndex] = useState(null);

  // Expanded Solo Tile Mode (Slot index or null)
  const [expandedSlotIndex, setExpandedSlotIndex] = useState(null);

  // Fetch all registered cameras and viewer stats
  const fetchCamerasAndStats = async () => {
    setLoadingCameras(true);
    try {
      const [camsRes, statsRes] = await Promise.all([
        fetch('/api/cameras?limit=500'),
        fetch('/api/viewer/stats'),
      ]);

      if (camsRes.ok) {
        const cams = await camsRes.json();
        setCameras(cams || []);
      }
      if (statsRes.ok) {
        const stats = await statsRes.json();
        setViewerStats(stats);
      }
    } catch (err) {
      console.error('Failed to load viewer data:', err);
    } finally {
      setLoadingCameras(false);
    }
  };

  useEffect(() => {
    fetchCamerasAndStats();
  }, []);

  // Handle Initial Config passed from Milestone 8 (Vehicle Search) or Milestone 7 (Alerts)
  useEffect(() => {
    if (initialConfig && initialConfig.camera) {
      const targetCam = initialConfig.camera;
      const targetSeek = initialConfig.seekTime !== undefined ? initialConfig.seekTime : 0;
      const targetFootageId = initialConfig.footageId || (initialConfig.footage && initialConfig.footage.id);

      setGridSlots((prev) => {
        const next = [...prev];
        // Check if camera is already in any slot
        const existingIdx = next.findIndex((s) => s && s.camera && s.camera.id === targetCam.id);
        if (existingIdx !== -1) {
          next[existingIdx] = {
            ...next[existingIdx],
            seekTime: targetSeek,
            footageId: targetFootageId || next[existingIdx].footageId,
            timestampKey: Date.now(),
          };
        } else {
          // Place into first empty slot or replace slot 0
          const emptyIdx = next.findIndex((s) => s === null);
          const insertIdx = emptyIdx !== -1 ? emptyIdx : 0;
          next[insertIdx] = {
            camera: targetCam,
            footageId: targetFootageId,
            seekTime: targetSeek,
            timestampKey: Date.now(),
          };
        }
        return next;
      });
    }
  }, [initialConfig]);

  // Adjust grid slots array size when layout changes
  const handleLayoutChange = (newLayoutId) => {
    setLayoutId(newLayoutId);
    setExpandedSlotIndex(null);
    const layout = GRID_LAYOUTS.find((l) => l.id === newLayoutId) || GRID_LAYOUTS[2];
    setGridSlots((prev) => {
      const next = Array(layout.slots).fill(null);
      for (let i = 0; i < layout.slots; i++) {
        if (i < prev.length && prev[i]) {
          next[i] = prev[i];
        }
      }
      return next;
    });
  };

  // Add camera to specific slot or first available slot
  const handleAddCameraToGrid = (camera, targetSlotIndex = null) => {
    setGridSlots((prev) => {
      const next = [...prev];
      // Check if already in grid
      const existingIdx = next.findIndex((s) => s && s.camera && s.camera.id === camera.id);
      if (existingIdx !== -1 && targetSlotIndex === null) {
        // Already in grid, highlight it
        return next;
      }

      let slotToFill = targetSlotIndex;
      if (slotToFill === null || slotToFill >= next.length) {
        const firstEmpty = next.findIndex((s) => s === null);
        slotToFill = firstEmpty !== -1 ? firstEmpty : 0;
      }

      next[slotToFill] = {
        camera,
        footageId: null,
        seekTime: 0,
        timestampKey: Date.now(),
      };
      return next;
    });
    setPickerSlotIndex(null);
  };

  // Remove camera from slot
  const handleRemoveCameraFromSlot = (slotIndex) => {
    setGridSlots((prev) => {
      const next = [...prev];
      next[slotIndex] = null;
      return next;
    });
    if (expandedSlotIndex === slotIndex) {
      setExpandedSlotIndex(null);
    }
  };

  // Auto-fill all empty slots with available online cameras
  const handleAutoFill = () => {
    const availableCams = cameras.filter((c) => c.status === 'ONLINE');
    setGridSlots((prev) => {
      const next = [...prev];
      let camIdx = 0;
      for (let i = 0; i < next.length; i++) {
        if (!next[i] && camIdx < availableCams.length) {
          // Find camera not already in grid
          while (
            camIdx < availableCams.length &&
            next.some((s) => s && s.camera && s.camera.id === availableCams[camIdx].id)
          ) {
            camIdx++;
          }
          if (camIdx < availableCams.length) {
            next[i] = {
              camera: availableCams[camIdx],
              footageId: null,
              seekTime: 0,
              timestampKey: Date.now(),
            };
            camIdx++;
          }
        }
      }
      return next;
    });
  };

  // Clear all slots
  const handleClearGrid = () => {
    setGridSlots(Array(activeLayout.slots).fill(null));
    setExpandedSlotIndex(null);
  };

  // Show all selected cameras on GIS Map
  const handleShowOnGisMap = () => {
    const activeCams = gridSlots.filter((s) => s && s.camera).map((s) => s.camera);
    if (activeCams.length === 0) {
      alert('No cameras currently active in the viewer grid.');
      return;
    }
    onOpenInGis(activeCams[0]);
  };

  // Filtered cameras for sidebar
  const uniqueDepartments = Array.from(new Set(cameras.map((c) => c.department))).filter(Boolean);
  const filteredCameras = cameras.filter((cam) => {
    const q = search.toLowerCase().trim();
    const matchesSearch =
      !q ||
      cam.camera_name.toLowerCase().includes(q) ||
      cam.camera_code.toLowerCase().includes(q) ||
      cam.location_name.toLowerCase().includes(q) ||
      cam.department.toLowerCase().includes(q);

    const matchesDept = !deptFilter || cam.department === deptFilter;
    const matchesStatus = !statusFilter || cam.status === statusFilter;
    const matchesSource = !sourceTypeFilter || cam.source_type === sourceTypeFilter;
    const matchesType = !cameraTypeFilter || cam.camera_type === cameraTypeFilter;

    return matchesSearch && matchesDept && matchesStatus && matchesSource && matchesType;
  });

  const activeCamerasCount = gridSlots.filter((s) => s && s.camera).length;

  return (
    <div className="space-y-4">
      {/* Top Header & Command Toolbar */}
      <div className="bg-[#081120] border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-600/20 border border-blue-500/40 rounded-lg text-blue-400">
              <Tv className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-lg font-bold text-white tracking-tight">Unified CCTV Viewer</h1>
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-emerald-900/60 text-emerald-300 border border-emerald-700/50 rounded-full font-mono">
                  Milestone 10: Stream Adapter & RTSP Layer
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Centralized live stream relay & recorded CCTV footage viewing platform
              </p>
            </div>
          </div>
        </div>

        {/* Toolbar Actions & Layout Selector */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs">
          {/* Layout Selector */}
          <div className="flex items-center bg-[#070d18] border border-slate-800 rounded-lg p-1 space-x-1">
            <span className="px-2 text-[11px] font-bold text-slate-400 uppercase tracking-wider hidden sm:inline">
              Layout:
            </span>
            {GRID_LAYOUTS.map((layout) => (
              <button
                key={layout.id}
                onClick={() => handleLayoutChange(layout.id)}
                className={`px-2.5 py-1 rounded text-xs font-mono font-bold transition ${
                  layoutId === layout.id && expandedSlotIndex === null
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
                title={`${layout.name} (${layout.slots} Cameras)`}
              >
                {layout.label}
              </button>
            ))}
          </div>

          {/* Quick Actions */}
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className={`px-3 py-1.5 rounded-lg border text-xs font-bold transition flex items-center space-x-1.5 ${
              isSidebarOpen
                ? 'bg-blue-900/30 border-blue-600 text-blue-300'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:text-white'
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Camera List</span>
          </button>

          <button
            onClick={handleShowOnGisMap}
            disabled={activeCamerasCount === 0}
            className="px-3 py-1.5 rounded-lg bg-emerald-600/20 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-600/30 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-bold transition flex items-center space-x-1.5 shadow-sm"
            title="Open active grid cameras on GIS map"
          >
            <MapPin className="w-3.5 h-3.5 text-emerald-400" />
            <span>Show on Map ({activeCamerasCount})</span>
          </button>

          <button
            onClick={handleAutoFill}
            disabled={activeCamerasCount >= activeLayout.slots || cameras.length === 0}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 disabled:opacity-50 text-xs font-medium transition flex items-center space-x-1"
            title="Auto-fill empty slots with online cameras"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Auto-Fill</span>
          </button>

          {activeCamerasCount > 0 && (
            <button
              onClick={handleClearGrid}
              className="px-3 py-1.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 border border-rose-800/60 text-xs font-medium transition"
              title="Clear all cameras from grid"
            >
              Clear Grid
            </button>
          )}
        </div>
      </div>

      {/* Main Multi-Camera Viewer Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* Left Camera Selection Sidebar */}
        {isSidebarOpen && (
          <div className="lg:col-span-3 bg-[#081120] border border-slate-800 rounded-xl p-4 shadow-xl space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
              <div className="flex items-center space-x-2">
                <CamIcon className="w-4 h-4 text-blue-400" />
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                  Registered Cameras ({filteredCameras.length})
                </h2>
              </div>
              <button
                onClick={() => setIsSidebarOpen(false)}
                className="text-slate-500 hover:text-slate-300"
                title="Hide sidebar"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Search & Filters */}
            <div className="space-y-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  placeholder="Search code, name, location..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-8 pr-2 py-1.5 bg-[#070d18] border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-1.5 text-[11px]">
                <select
                  value={deptFilter}
                  onChange={(e) => setDeptFilter(e.target.value)}
                  className="px-2 py-1 bg-[#070d18] border border-slate-700 rounded text-slate-300 focus:outline-none focus:border-blue-500"
                >
                  <option value="">All Depts</option>
                  {uniqueDepartments.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>

                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-2 py-1 bg-[#070d18] border border-slate-700 rounded text-slate-300 focus:outline-none focus:border-blue-500"
                >
                  <option value="">All Statuses</option>
                  <option value="ONLINE">ONLINE</option>
                  <option value="OFFLINE">OFFLINE</option>
                </select>

                <select
                  value={sourceTypeFilter}
                  onChange={(e) => setSourceTypeFilter(e.target.value)}
                  className="px-2 py-1 bg-[#070d18] border border-slate-700 rounded text-slate-300 focus:outline-none focus:border-blue-500 col-span-2"
                >
                  <option value="">All Sources</option>
                  <option value="RECORDED_FOOTAGE">Recorded Footage (File)</option>
                  <option value="LIVE_CAMERA">Live Camera (Stream)</option>
                </select>
              </div>
            </div>

            {/* Cameras List */}
            <div className="overflow-y-auto space-y-2 flex-1 pr-1 custom-scrollbar">
              {loadingCameras ? (
                <div className="text-center py-8 text-xs text-slate-500">Loading registered cameras...</div>
              ) : filteredCameras.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-500">No cameras match search filters.</div>
              ) : (
                filteredCameras.map((cam) => {
                  const isAlreadyInGrid = gridSlots.some((s) => s && s.camera && s.camera.id === cam.id);
                  return (
                    <div
                      key={cam.id}
                      className={`p-2.5 rounded-lg border transition text-xs ${
                        isAlreadyInGrid
                          ? 'bg-blue-950/20 border-blue-600/50'
                          : 'bg-[#070d18] border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center space-x-1.5">
                            <span className="font-mono font-bold text-blue-400">{cam.camera_code}</span>
                            <span
                              className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                                cam.status === 'ONLINE'
                                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-700/50'
                                  : 'bg-rose-950 text-rose-400 border border-rose-700/50'
                              }`}
                            >
                              {cam.status}
                            </span>
                          </div>
                          <div className="text-slate-300 font-medium truncate max-w-[170px] mt-0.5">
                            {cam.camera_name}
                          </div>
                          <div className="text-[11px] text-slate-500 flex items-center space-x-1 mt-0.5">
                            <span>{cam.location_name}</span>
                            <span>•</span>
                            <span>{cam.department}</span>
                          </div>
                        </div>

                        <div className="flex flex-col items-end space-y-1">
                          <button
                            onClick={() => handleAddCameraToGrid(cam)}
                            className={`px-2 py-1 rounded text-[11px] font-bold transition flex items-center space-x-1 ${
                              isAlreadyInGrid
                                ? 'bg-blue-600/30 text-blue-300 border border-blue-500/40 cursor-default'
                                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-sm'
                            }`}
                          >
                            <Plus className="w-3 h-3" />
                            <span>{isAlreadyInGrid ? 'In Grid' : 'Add'}</span>
                          </button>

                          <button
                            onClick={() => setDetailsCamera(cam)}
                            className="text-[10px] text-slate-500 hover:text-slate-300 underline"
                          >
                            Details
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}

        {/* Right Multi-Camera Grid Area */}
        <div className={`${isSidebarOpen ? 'lg:col-span-9' : 'lg:col-span-12'} space-y-4`}>
          {/* Expanded Solo View Mode */}
          {expandedSlotIndex !== null && gridSlots[expandedSlotIndex] ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between bg-[#081120] border border-blue-500/40 rounded-t-xl px-4 py-2 text-xs">
                <div className="flex items-center space-x-2 text-blue-300 font-bold">
                  <Maximize2 className="w-4 h-4 text-blue-400" />
                  <span>Maximized View: {gridSlots[expandedSlotIndex].camera.camera_code}</span>
                </div>
                <button
                  onClick={() => setExpandedSlotIndex(null)}
                  className="flex items-center space-x-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-bold"
                >
                  <Minimize2 className="w-3.5 h-3.5" />
                  <span>Exit Solo View</span>
                </button>
              </div>
              <CameraTile
                slotData={gridSlots[expandedSlotIndex]}
                slotIndex={expandedSlotIndex}
                isExpanded={true}
                onRemove={() => handleRemoveCameraFromSlot(expandedSlotIndex)}
                onToggleExpand={() => setExpandedSlotIndex(null)}
                onOpenDetails={(cam) => setDetailsCamera(cam)}
                onOpenInGis={onOpenInGis}
                onOpenAlerts={onOpenAlerts}
              />
            </div>
          ) : (
            /* Multi-Camera Grid Container */
            <div className={`grid ${activeLayout.cols} gap-4`}>
              {gridSlots.map((slotData, index) => {
                if (!slotData) {
                  return (
                    <EmptySlotPlaceholder
                      key={`empty-${index}`}
                      slotIndex={index}
                      onSelectCamera={() => setPickerSlotIndex(index)}
                    />
                  );
                }
                return (
                  <CameraTile
                    key={`slot-${index}-${slotData.camera.id}-${slotData.timestampKey || index}`}
                    slotData={slotData}
                    slotIndex={index}
                    isExpanded={false}
                    onRemove={() => handleRemoveCameraFromSlot(index)}
                    onToggleExpand={() => setExpandedSlotIndex(index)}
                    onOpenDetails={(cam) => setDetailsCamera(cam)}
                    onOpenInGis={onOpenInGis}
                    onOpenAlerts={onOpenAlerts}
                  />
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Camera Details Modal */}
      {detailsCamera && (
        <CameraDetailsModal
          camera={detailsCamera}
          onClose={() => setDetailsCamera(null)}
          onViewOnMap={(cam) => {
            setDetailsCamera(null);
            onOpenInGis(cam);
          }}
        />
      )}

      {/* Quick Camera Picker Modal for Empty Slot */}
      {pickerSlotIndex !== null && (
        <QuickCameraPickerModal
          slotIndex={pickerSlotIndex}
          cameras={cameras}
          onClose={() => setPickerSlotIndex(null)}
          onSelectCamera={(cam) => handleAddCameraToGrid(cam, pickerSlotIndex)}
        />
      )}
    </div>
  );
}

// ----------------------------------------------------------------------
// CAMERA TILE COMPONENT (Milestone 10: Stream Adapter & Live Relay)
// ----------------------------------------------------------------------
function CameraTile({
  slotData,
  slotIndex,
  isExpanded,
  onRemove,
  onToggleExpand,
  onOpenDetails,
  onOpenInGis,
  onOpenAlerts,
}) {
  const { camera, seekTime = 0 } = slotData;

  const [streamInfo, setStreamInfo] = useState(null);
  const [loadingStream, setLoadingStream] = useState(true);
  const [selectedFootageId, setSelectedFootageId] = useState(slotData.footageId || null);

  // Live Stream Connection States
  const [isConnecting, setIsConnecting] = useState(false);
  const [isLiveConnected, setIsLiveConnected] = useState(false);
  const [streamStatus, setStreamStatus] = useState('NOT_CONFIGURED');
  const [streamErrorMessage, setStreamErrorMessage] = useState(null);
  const [liveFeedKey, setLiveFeedKey] = useState(Date.now());

  // Video Player state (for Recorded Footage)
  const videoRef = useRef(null);
  const tileContainerRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [hasSeekedInitial, setHasSeekedInitial] = useState(false);

  // Load Stream info and check current status
  useEffect(() => {
    let isMounted = true;
    setLoadingStream(true);

    fetch(`/api/viewer/cameras/${camera.id}/stream-info`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (isMounted && data) {
          setStreamInfo(data);
          setStreamStatus(data.stream_status);
          if (!selectedFootageId && data.available_footage && data.available_footage.length > 0) {
            setSelectedFootageId(data.available_footage[0].id);
          }
          // If already connected live stream
          if (data.stream_status === 'CONNECTED' && data.source_type === 'LIVE_CAMERA') {
            setIsLiveConnected(true);
          }
        }
      })
      .catch((err) => console.error('Failed to load stream info:', err))
      .finally(() => {
        if (isMounted) setLoadingStream(false);
      });

    return () => {
      isMounted = false;
    };
  }, [camera.id]);

  // Connect to live stream
  const handleConnectStream = async () => {
    setIsConnecting(true);
    setStreamErrorMessage(null);
    try {
      const res = await fetch(`/api/streams/${camera.id}/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force_reconnect: true }),
      });
      const data = await res.json();
      if (res.ok) {
        setStreamStatus(data.status);
        if (data.status === 'CONNECTED') {
          setIsLiveConnected(true);
          setLiveFeedKey(Date.now());
        } else {
          setIsLiveConnected(false);
          setStreamErrorMessage(data.error || data.message || 'Connecting to stream...');
        }
      } else {
        setStreamStatus('ERROR');
        setIsLiveConnected(false);
        setStreamErrorMessage(data.detail || 'Connection failed.');
      }
    } catch (err) {
      setStreamStatus('ERROR');
      setIsLiveConnected(false);
      setStreamErrorMessage('Unable to reach backend stream service.');
    } finally {
      setIsConnecting(false);
    }
  };

  // Disconnect live stream
  const handleDisconnectStream = async () => {
    setIsConnecting(true);
    try {
      const res = await fetch(`/api/streams/${camera.id}/disconnect`, { method: 'POST' });
      if (res.ok) {
        setIsLiveConnected(false);
        setStreamStatus('DISCONNECTED');
        setStreamErrorMessage(null);
      }
    } catch (err) {
      console.error('Failed to disconnect stream:', err);
    } finally {
      setIsConnecting(false);
    }
  };

  // Handle Initial Seek Time when video metadata is loaded
  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration || 0);
      if (seekTime > 0 && !hasSeekedInitial) {
        videoRef.current.currentTime = seekTime;
        setHasSeekedInitial(true);
      }
      videoRef.current.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
        setIsPlaying(false);
      } else {
        videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
      }
    }
  };

  const handleSeek = (e) => {
    const target = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.currentTime = target;
      setCurrentTime(target);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const toggleNativeFullscreen = () => {
    if (!tileContainerRef.current) return;
    if (!document.fullscreenElement) {
      tileContainerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  useEffect(() => {
    const handleFsChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFsChange);
    return () => document.removeEventListener('fullscreenchange', handleFsChange);
  }, []);

  const formatSeconds = (sec) => {
    if (isNaN(sec) || sec < 0) return '00:00';
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const activeFootage =
    streamInfo && streamInfo.available_footage
      ? streamInfo.available_footage.find((f) => f.id === selectedFootageId) || streamInfo.available_footage[0]
      : null;

  const isLiveCamera = camera.source_type === 'LIVE_CAMERA';

  return (
    <div
      ref={tileContainerRef}
      className={`bg-[#060c18] border rounded-xl overflow-hidden shadow-2xl flex flex-col transition ${
        isFullscreen ? 'p-4 bg-[#050b14]' : 'border-slate-800 hover:border-slate-700'
      } ${isExpanded ? 'h-[75vh]' : 'h-[360px]'}`}
    >
      {/* Tile Header Bar */}
      <div className="bg-[#081120] border-b border-slate-800/80 px-3 py-2 flex items-center justify-between text-xs select-none">
        <div className="flex items-center space-x-2 truncate">
          <span className="font-mono font-bold text-blue-400">{camera.camera_code}</span>
          <span className="text-slate-400 truncate max-w-[120px] hidden sm:inline">{camera.location_name}</span>

          {/* Status Badge */}
          <span
            className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
              camera.status === 'ONLINE'
                ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-700/50'
                : 'bg-rose-950/80 text-rose-400 border border-rose-700/50'
            }`}
          >
            {camera.status}
          </span>

          {/* Source & Connectivity Protocol Badge */}
          <span className="px-1.5 py-0.2 rounded text-[9px] font-mono bg-slate-800 text-slate-300 hidden md:inline">
            {isLiveCamera ? `● LIVE (${camera.connectivity_type})` : '● RECORDING'}
          </span>

          {/* Active Watchlist Alert Badge */}
          {streamInfo && streamInfo.active_alerts_count > 0 && (
            <button
              onClick={() => onOpenAlerts(camera.camera_code)}
              className="px-1.5 py-0.2 rounded bg-rose-900/60 border border-rose-500 text-rose-200 text-[10px] font-bold flex items-center space-x-1 animate-pulse"
              title={`${streamInfo.active_alerts_count} Watchlist Alert(s) on this camera`}
            >
              <ShieldAlert className="w-3 h-3 text-rose-400" />
              <span>{streamInfo.active_alerts_count} ALERT</span>
            </button>
          )}
        </div>

        {/* Tile Control Actions */}
        <div className="flex items-center space-x-1">
          <button
            onClick={() => onOpenInGis(camera)}
            className="p-1 rounded text-slate-400 hover:text-emerald-400 hover:bg-slate-800"
            title="Locate on GIS Map"
          >
            <MapPin className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => onOpenDetails(camera)}
            className="p-1 rounded text-slate-400 hover:text-blue-400 hover:bg-slate-800"
            title="Camera Details"
          >
            <Info className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={onToggleExpand}
            className="p-1 rounded text-slate-400 hover:text-cyan-400 hover:bg-slate-800"
            title={isExpanded ? 'Restore Grid' : 'Maximize Tile'}
          >
            {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={toggleNativeFullscreen}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800"
            title="Fullscreen"
          >
            <Grid className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={onRemove}
            className="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800 ml-1"
            title="Remove from Viewer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Video / Stream Content Area */}
      <div className="flex-1 bg-black relative flex items-center justify-center overflow-hidden group">
        {loadingStream ? (
          <div className="text-center text-xs text-slate-500">Inspecting CCTV stream capabilities...</div>
        ) : camera.status === 'OFFLINE' ? (
          /* Offline Standby Screen */
          <div className="text-center space-y-2 p-4">
            <AlertTriangle className="w-8 h-8 text-rose-500 mx-auto opacity-70" />
            <div className="text-xs font-bold text-rose-400 uppercase tracking-wider">Camera Offline</div>
            <div className="text-[11px] text-slate-500 max-w-xs">
              No signal received from {camera.camera_code}. Check network connectivity in CCTV Registry.
            </div>
          </div>
        ) : !isLiveCamera && activeFootage ? (
          /* Recorded Video Player (HTTP 206 Byte Range) */
          <div className="w-full h-full relative flex items-center justify-center bg-black">
            <video
              ref={videoRef}
              src={activeFootage.stream_url}
              className="w-full h-full object-contain"
              onLoadedMetadata={handleLoadedMetadata}
              onTimeUpdate={handleTimeUpdate}
              onEnded={() => setIsPlaying(false)}
              muted={isMuted}
              playsInline
            />

            {/* Play/Pause Center Overlay on Hover */}
            <button
              onClick={togglePlay}
              className="absolute inset-0 m-auto w-12 h-12 rounded-full bg-black/60 border border-white/20 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition shadow-2xl hover:scale-110"
            >
              {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 ml-0.5" />}
            </button>
          </div>
        ) : isLiveCamera && isLiveConnected ? (
          /* Live Stream Connected (Browser-Compatible MJPEG Media Relay) */
          <div className="w-full h-full relative flex items-center justify-center bg-black">
            <img
              key={`live-${liveFeedKey}`}
              src={`/api/streams/${camera.id}/live?t=${liveFeedKey}`}
              alt={`Live feed from ${camera.camera_code}`}
              className="w-full h-full object-contain"
              onError={() => {
                setIsLiveConnected(false);
                setStreamStatus('ERROR');
                setStreamErrorMessage('Live stream feed interrupted.');
              }}
            />

            {/* Live Active Badge */}
            <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-emerald-950/90 border border-emerald-500/80 text-[10px] text-emerald-300 font-bold flex items-center space-x-1.5 shadow-lg backdrop-blur-sm select-none">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>LIVE</span>
              <span className="text-[9px] text-emerald-400/80 font-mono">({camera.connectivity_type})</span>
            </div>
          </div>
        ) : isLiveCamera && isConnecting ? (
          /* Connecting Live Screen */
          <div className="text-center space-y-3 p-4">
            <RefreshCw className="w-7 h-7 text-blue-400 animate-spin mx-auto" />
            <div className="text-xs font-bold text-blue-300">Connecting to authorized CCTV stream...</div>
            <div className="text-[11px] text-slate-500 font-mono">Protocol: {camera.connectivity_type} • StreamManager Adapter</div>
          </div>
        ) : (
          /* Live Stream Standby / Disconnected / Unconfigured Screen */
          <div className="text-center space-y-3 p-4">
            <Video className="w-8 h-8 text-slate-600 mx-auto" />
            <div className="text-xs font-bold text-slate-300">
              {streamErrorMessage || (streamInfo ? streamInfo.status_message : 'Live stream is not configured.')}
            </div>
            <div className="text-[11px] text-slate-500 font-mono">
              Source: {camera.source_type} • Connectivity: {camera.connectivity_type}
            </div>

            {/* Quick Connect Action Button for Live Cameras */}
            {isLiveCamera && (
              <div className="pt-1">
                <button
                  onClick={handleConnectStream}
                  disabled={isConnecting}
                  className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md transition disabled:opacity-50"
                >
                  {isConnecting ? 'Connecting...' : 'Connect Live Stream'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom Controls Bar: Recorded Footage Seek Controls */}
      {!isLiveCamera && activeFootage && (
        <div className="bg-[#081120] border-t border-slate-800/80 px-3 py-2 space-y-1.5 text-xs">
          <div className="flex items-center space-x-2">
            <span className="font-mono text-[10px] text-slate-400 w-10 text-right">
              {formatSeconds(currentTime)}
            </span>
            <input
              type="range"
              min="0"
              max={duration || 100}
              step="0.1"
              value={currentTime}
              onChange={handleSeek}
              className="flex-1 h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
            />
            <span className="font-mono text-[10px] text-slate-500 w-10">
              {formatSeconds(duration)}
            </span>
          </div>

          <div className="flex items-center justify-between text-slate-400">
            <div className="flex items-center space-x-2">
              <button
                onClick={togglePlay}
                className="p-1 rounded text-slate-200 hover:text-white hover:bg-slate-800"
                title={isPlaying ? 'Pause' : 'Play'}
              >
                {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              </button>

              <button
                onClick={toggleMute}
                className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800"
                title={isMuted ? 'Unmute' : 'Mute'}
              >
                {isMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
              </button>

              <button
                onClick={() => {
                  if (videoRef.current) {
                    videoRef.current.currentTime = 0;
                  }
                }}
                className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800"
                title="Restart"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>

            {streamInfo && streamInfo.available_footage && streamInfo.available_footage.length > 1 && (
              <div className="flex items-center space-x-1">
                <select
                  value={selectedFootageId || ''}
                  onChange={(e) => setSelectedFootageId(parseInt(e.target.value))}
                  className="px-2 py-0.5 bg-[#070d18] border border-slate-700 rounded text-[11px] text-slate-300 focus:outline-none focus:border-blue-500"
                >
                  {streamInfo.available_footage.map((ft, fIdx) => (
                    <option key={ft.id} value={ft.id}>
                      Recording {fIdx + 1} ({ft.formatted_duration})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Bottom Controls Bar: Live Camera Stream Controls */}
      {isLiveCamera && (
        <div className="bg-[#081120] border-t border-slate-800/80 px-3 py-2 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2">
            {isLiveConnected ? (
              <button
                onClick={handleDisconnectStream}
                disabled={isConnecting}
                className="px-2.5 py-1 rounded bg-rose-950/60 hover:bg-rose-900/70 border border-rose-700 text-rose-200 text-xs font-bold transition flex items-center space-x-1"
                title="Disconnect live stream session"
              >
                <span>Disconnect</span>
              </button>
            ) : (
              <button
                onClick={handleConnectStream}
                disabled={isConnecting}
                className="px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition flex items-center space-x-1 shadow-sm disabled:opacity-50"
                title="Connect to authorized live stream"
              >
                <Radio className="w-3.5 h-3.5" />
                <span>{isConnecting ? 'Connecting...' : 'Connect'}</span>
              </button>
            )}

            <span className="text-[11px] text-slate-400 font-mono hidden sm:inline">
              Relay: {isLiveConnected ? 'Active (MJPEG)' : 'Standby'}
            </span>
          </div>

          <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-500">
            <span>Status:</span>
            <span
              className={`font-bold ${
                isLiveConnected
                  ? 'text-emerald-400'
                  : streamStatus === 'ERROR'
                  ? 'text-rose-400'
                  : 'text-slate-400'
              }`}
            >
              {streamStatus}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// ----------------------------------------------------------------------
// EMPTY SLOT PLACEHOLDER
// ----------------------------------------------------------------------
function EmptySlotPlaceholder({ slotIndex, onSelectCamera }) {
  return (
    <div
      onClick={onSelectCamera}
      className="h-[360px] border-2 border-dashed border-slate-800 hover:border-blue-500/60 bg-[#070d18]/60 hover:bg-blue-950/10 rounded-xl flex flex-col items-center justify-center p-6 text-center cursor-pointer transition group shadow-inner"
    >
      <div className="p-3 rounded-full bg-slate-800/80 group-hover:bg-blue-600/20 text-slate-500 group-hover:text-blue-400 transition mb-3">
        <Plus className="w-6 h-6" />
      </div>
      <div className="text-xs font-bold text-slate-300 group-hover:text-blue-300">
        Slot #{slotIndex + 1} — Empty
      </div>
      <div className="text-[11px] text-slate-500 mt-1">
        Click to assign a registered CCTV camera
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------
// QUICK CAMERA PICKER MODAL
// ----------------------------------------------------------------------
function QuickCameraPickerModal({ slotIndex, cameras, onClose, onSelectCamera }) {
  const [search, setSearch] = useState('');

  const filtered = cameras.filter((c) => {
    const q = search.toLowerCase().trim();
    return (
      !q ||
      c.camera_name.toLowerCase().includes(q) ||
      c.camera_code.toLowerCase().includes(q) ||
      c.location_name.toLowerCase().includes(q) ||
      c.department.toLowerCase().includes(q)
    );
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="bg-[#081120] border border-slate-800 rounded-xl max-w-lg w-full p-4 shadow-2xl space-y-4 max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center space-x-2">
            <CamIcon className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-bold text-white">Select Camera for Slot #{slotIndex + 1}</h3>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search camera code, location, department..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-[#070d18] border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            autoFocus
          />
        </div>

        <div className="overflow-y-auto space-y-2 flex-1 pr-1 custom-scrollbar">
          {filtered.map((cam) => (
            <div
              key={cam.id}
              onClick={() => onSelectCamera(cam)}
              className="p-3 bg-[#070d18] border border-slate-800 hover:border-blue-500/50 hover:bg-blue-950/20 rounded-lg cursor-pointer transition flex items-center justify-between text-xs"
            >
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-mono font-bold text-blue-400">{cam.camera_code}</span>
                  <span
                    className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                      cam.status === 'ONLINE' ? 'bg-emerald-950 text-emerald-400' : 'bg-rose-950 text-rose-400'
                    }`}
                  >
                    {cam.status}
                  </span>
                </div>
                <div className="text-slate-200 font-medium mt-0.5">{cam.camera_name}</div>
                <div className="text-[11px] text-slate-500">
                  {cam.location_name} • {cam.department}
                </div>
              </div>

              <span className="px-2.5 py-1 bg-blue-600/30 text-blue-300 border border-blue-500/40 rounded text-xs font-bold">
                Select
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
