import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Cpu,
  Play,
  Film,
  Car,
  Bike,
  Bus,
  Truck,
  Layers,
  Clock,
  Shield,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Search,
  Filter,
  Eye,
  SlidersHorizontal,
  ChevronRight,
  Maximize2,
  Navigation,
  Compass,
  ArrowRight,
  ExternalLink,
  Target,
  Image as ImageIcon,
} from 'lucide-react';

export default function DetectionResultsModal({
  isOpen,
  onClose,
  footage,
  camera,
  autoStart = false,
}) {
  const [job, setJob] = useState(null);
  const [tracksData, setTracksData] = useState(null);
  const [detectionData, setDetectionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedClassFilter, setSelectedClassFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeVideoTab, setActiveVideoTab] = useState('processed'); // 'processed' | 'original'
  const [activeViewTab, setActiveViewTab] = useState('tracks'); // 'tracks' | 'detections'
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [selectedTrackDetails, setSelectedTrackDetails] = useState(null);
  const [selectedCropPreview, setSelectedCropPreview] = useState(null);
  const [analysisMode, setAnalysisMode] = useState('VEHICLE_TRACKING'); // 'VEHICLE_TRACKING' | 'VEHICLE_DETECTION'

  const videoRef = useRef(null);

  // Polling function for active job
  const pollJobStatus = async (jobId) => {
    try {
      const res = await fetch(`/api/analysis/jobs/${jobId}`);
      if (res.ok) {
        const data = await res.json();
        setJob(data);

        if (data.status === 'COMPLETED') {
          fetchResults();
          return true; // Stop polling
        } else if (data.status === 'FAILED') {
          return true; // Stop polling
        }
      }
    } catch (err) {
      console.error('Error polling job status:', err);
    }
    return false;
  };

  // Trigger analysis (Tracking or Detection)
  const startAnalysis = async (mode = analysisMode) => {
    if (!footage) return;
    try {
      const res = await fetch(`/api/footage/${footage.id}/analyze?job_type=${mode}`, { method: 'POST' });
      if (res.ok) {
        const newJob = await res.json();
        setJob(newJob);
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Failed to start vehicle analysis');
      }
    } catch (err) {
      alert(`Network error starting analysis: ${err.message}`);
    }
  };

  // Fetch both track summaries and frame detections
  const fetchResults = async () => {
    if (!footage) return;
    try {
      // 1. Fetch Tracks
      const tracksRes = await fetch(`/api/footage/${footage.id}/tracks`);
      if (tracksRes.ok) {
        const tData = await tracksRes.json();
        setTracksData(tData);
        if (tData.latest_job) {
          setJob(tData.latest_job);
        }
      }

      // 2. Fetch Detections
      const detsRes = await fetch(`/api/footage/${footage.id}/detections`);
      if (detsRes.ok) {
        const dData = await detsRes.json();
        setDetectionData(dData);
      }
    } catch (err) {
      console.error('Error fetching tracking results:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch individual track details when clicked
  const fetchTrackDetail = async (trackId) => {
    if (!footage) return;
    try {
      const res = await fetch(`/api/footage/${footage.id}/tracks/${trackId}`);
      if (res.ok) {
        const detail = await res.json();
        setSelectedTrackDetails(detail);
      }
    } catch (err) {
      console.error('Failed to load track details:', err);
    }
  };

  useEffect(() => {
    if (isOpen && footage) {
      setLoading(true);
      setSelectedTrack(null);
      setSelectedTrackDetails(null);
      fetchResults();
    }
  }, [isOpen, footage]);

  // If autoStart requested and there is no active/completed job yet, start it
  useEffect(() => {
    if (isOpen && footage && autoStart && job && job.status !== 'PROCESSING' && job.status !== 'QUEUED' && job.status !== 'COMPLETED') {
      startAnalysis();
    }
  }, [isOpen, footage, autoStart]);

  // Set up polling interval if job is currently active
  useEffect(() => {
    let interval = null;
    if (job && (job.status === 'QUEUED' || job.status === 'PROCESSING')) {
      interval = setInterval(async () => {
        const shouldStop = await pollJobStatus(job.id);
        if (shouldStop && interval) clearInterval(interval);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [job]);

  if (!isOpen || !footage) return null;

  // Seek video player to exact timestamp
  const seekToTimestamp = (seconds) => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(0, seconds);
      videoRef.current.play().catch(() => {});
    }
  };

  const getVehicleIcon = (vClass) => {
    switch (vClass?.toLowerCase()) {
      case 'car':
        return <Car className="w-3.5 h-3.5 text-amber-400" />;
      case 'motorcycle':
        return <Bike className="w-3.5 h-3.5 text-cyan-400" />;
      case 'bus':
        return <Bus className="w-3.5 h-3.5 text-purple-400" />;
      case 'truck':
        return <Truck className="w-3.5 h-3.5 text-orange-400" />;
      default:
        return <Car className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  const isProcessing = job?.status === 'QUEUED' || job?.status === 'PROCESSING';

  // Filtered tracks
  const filteredTracks = (tracksData?.tracks || []).filter((t) => {
    if (selectedClassFilter !== 'ALL' && t.vehicle_class.toUpperCase() !== selectedClassFilter) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      return (
        t.vehicle_class.toLowerCase().includes(q) ||
        t.track_id.toString().includes(q) ||
        t.first_seen_formatted.includes(q)
      );
    }
    return true;
  });

  // Filtered detections
  const filteredDetections = (detectionData?.detections || []).filter((det) => {
    if (selectedClassFilter !== 'ALL' && det.vehicle_class.toUpperCase() !== selectedClassFilter) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      return (
        det.vehicle_class.toLowerCase().includes(q) ||
        det.formatted_timestamp.includes(q) ||
        (det.track_id && det.track_id.toString().includes(q))
      );
    }
    return true;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md overflow-y-auto">
      <div className="bg-[#0b1424] border border-slate-700/80 rounded-2xl w-full max-w-6xl shadow-2xl overflow-hidden my-6">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#080f1c]">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-400">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-white tracking-tight">
                  Vehicle Tracking & Multi-Object Analytics
                </h2>
                <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-blue-900/60 text-blue-300 border border-blue-700/50">
                  {camera?.camera_code || `Footage #${footage.id}`}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-emerald-950/60 text-emerald-300 border border-emerald-700/40">
                  ByteTrack Active
                </span>
              </div>
              <p className="text-xs text-slate-400">
                {footage.original_file_name} • Gujarat Police CCTV AI Intelligence
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {job && (
              <span className="hidden sm:inline-flex items-center px-2.5 py-1 rounded-lg bg-[#070d18] border border-slate-800 text-xs font-mono text-slate-300">
                <Cpu className="w-3.5 h-3.5 text-emerald-400 mr-1.5" />
                {job.device || 'CPU'}
              </span>
            )}

            {!isProcessing && (
              <div className="flex items-center space-x-1 bg-[#070d18] p-1 rounded-lg border border-slate-800">
                <button
                  onClick={() => {
                    setAnalysisMode('VEHICLE_TRACKING');
                    startAnalysis('VEHICLE_TRACKING');
                  }}
                  className="px-3 py-1 rounded text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white flex items-center space-x-1.5 transition shadow"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Track Vehicles</span>
                </button>
              </div>
            )}

            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 max-h-[84vh] overflow-y-auto">
          
          {/* Active Processing Banner */}
          {isProcessing && (
            <div className="p-5 rounded-xl bg-gradient-to-r from-blue-950/40 via-[#0a1832] to-[#070d18] border border-blue-500/40 shadow-xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <RefreshCw className="w-5 h-5 text-blue-400 animate-spin" />
                  <div>
                    <h3 className="font-bold text-white text-sm">
                      Running YOLO + ByteTrack Multi-Object Tracking ({job.progress}%)
                    </h3>
                    <p className="text-xs text-slate-400">
                      Tracking physical vehicles across consecutive frames and associating Track IDs...
                    </p>
                  </div>
                </div>

                <div className="text-right font-mono text-xs text-slate-300">
                  <span className="text-emerald-400 font-bold">{job.total_tracks}</span> Unique Tracks •{' '}
                  <span className="text-blue-400 font-bold">{job.total_detections}</span> Sightings
                </div>
              </div>

              <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
                <div
                  className="bg-gradient-to-r from-blue-500 via-indigo-500 to-emerald-400 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${Math.max(job.progress, 5)}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Job Failed Alert */}
          {job?.status === 'FAILED' && (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold text-sm">Vehicle Tracking Failed</h4>
                <p className="mt-1 text-slate-300">{job.error_message || 'An unexpected error occurred during processing.'}</p>
              </div>
            </div>
          )}

          {/* Vehicle Tracking Statistics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
            {/* Total Tracks */}
            <div className="p-3.5 rounded-xl bg-[#070d18] border border-blue-500/30 shadow">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Unique Tracks</span>
                <Target className="w-4 h-4 text-blue-400" />
              </div>
              <div className="text-2xl font-bold font-mono text-white mt-1">
                {tracksData?.total_tracks || job?.total_tracks || 0}
              </div>
            </div>

            {/* Car Tracks */}
            <div className="p-3.5 rounded-xl bg-[#070d18] border border-amber-500/20 shadow">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Car Tracks</span>
                <Car className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
                {tracksData?.car_tracks || job?.car_tracks || 0}
              </div>
            </div>

            {/* Motorcycle Tracks */}
            <div className="p-3.5 rounded-xl bg-[#070d18] border border-cyan-500/20 shadow">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>2-Wheelers</span>
                <Bike className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">
                {tracksData?.motorcycle_tracks || job?.motorcycle_tracks || 0}
              </div>
            </div>

            {/* Bus Tracks */}
            <div className="p-3.5 rounded-xl bg-[#070d18] border border-purple-500/20 shadow">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Bus Tracks</span>
                <Bus className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-2xl font-bold font-mono text-purple-400 mt-1">
                {tracksData?.bus_tracks || job?.bus_tracks || 0}
              </div>
            </div>

            {/* Truck Tracks */}
            <div className="p-3.5 rounded-xl bg-[#070d18] border border-orange-500/20 shadow">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Truck Tracks</span>
                <Truck className="w-4 h-4 text-orange-400" />
              </div>
              <div className="text-2xl font-bold font-mono text-orange-400 mt-1">
                {tracksData?.truck_tracks || job?.truck_tracks || 0}
              </div>
            </div>

            {/* Total Frame Detections */}
            <div className="p-3.5 rounded-xl bg-[#070d18] border border-emerald-500/20 shadow">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Total Sightings</span>
                <Layers className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                {tracksData?.total_detections || job?.total_detections || 0}
              </div>
            </div>
          </div>

          {/* Dual Video Player Section with Click-To-Seek */}
          <div className="bg-[#070d18] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            {/* Player Tabs Header */}
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-800 bg-[#050912]">
              <div className="flex items-center space-x-2 text-xs font-bold">
                <button
                  onClick={() => setActiveVideoTab('processed')}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition ${
                    activeVideoTab === 'processed'
                      ? 'bg-blue-600 text-white shadow'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  <Compass className="w-3.5 h-3.5" />
                  <span>Annotated Tracking Video (ByteTrack)</span>
                </button>

                <button
                  onClick={() => setActiveVideoTab('original')}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition ${
                    activeVideoTab === 'original'
                      ? 'bg-blue-600 text-white shadow'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  <Film className="w-3.5 h-3.5" />
                  <span>Original CCTV Footage</span>
                </button>
              </div>

              <span className="text-[11px] font-mono text-slate-400">
                {activeVideoTab === 'processed'
                  ? 'Showing Track IDs, Bounding Accents & Centroid Trails'
                  : 'Raw Video Feed'}
              </span>
            </div>

            {/* Video Container */}
            <div className="aspect-video bg-black flex items-center justify-center relative">
              {activeVideoTab === 'processed' ? (
                tracksData?.has_processed_video || detectionData?.has_processed_video ? (
                  <video
                    key="processed-video"
                    ref={videoRef}
                    controls
                    autoPlay
                    className="w-full h-full object-contain"
                  >
                    <source
                      src={tracksData?.processed_video_stream_url || `/api/footage/${footage.id}/processed/stream`}
                      type="video/mp4"
                    />
                    Your browser does not support video playback.
                  </video>
                ) : (
                  <div className="p-8 text-center text-slate-400 space-y-2">
                    <Compass className="w-12 h-12 text-slate-600 mx-auto" />
                    <p className="font-semibold text-slate-300">
                      {isProcessing
                        ? 'Annotated tracking video is generating...'
                        : 'No processed tracking video generated yet.'}
                    </p>
                  </div>
                )
              ) : (
                <video
                  key="original-video"
                  ref={videoRef}
                  controls
                  className="w-full h-full object-contain"
                >
                  <source
                    src={tracksData?.original_video_stream_url || `/api/footage/${footage.id}/stream`}
                    type={footage.mime_type || 'video/mp4'}
                  />
                  Your browser does not support video playback.
                </video>
              )}
            </div>
          </div>

          {/* Analytics Explorer Tabs (Track Summaries vs Detections) */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => {
                    setActiveViewTab('tracks');
                    setSelectedTrack(null);
                  }}
                  className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition ${
                    activeViewTab === 'tracks'
                      ? 'bg-blue-600/20 text-blue-300 border border-blue-500/40 shadow-inner'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Target className="w-4 h-4 text-blue-400" />
                  <span>Track Summary Table ({tracksData?.total_tracks || 0})</span>
                </button>

                <button
                  onClick={() => {
                    setActiveViewTab('detections');
                    setSelectedTrack(null);
                  }}
                  className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition ${
                    activeViewTab === 'detections'
                      ? 'bg-blue-600/20 text-blue-300 border border-blue-500/40 shadow-inner'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Clock className="w-4 h-4 text-emerald-400" />
                  <span>Timestamped Sightings Log ({detectionData?.total_detections || 0})</span>
                </button>
              </div>

              {/* Class Filter & Search */}
              <div className="flex items-center space-x-2 text-xs">
                <div className="flex rounded-lg bg-[#070d18] border border-slate-800 p-0.5 font-mono text-[11px]">
                  {['ALL', 'CAR', 'MOTORCYCLE', 'BUS', 'TRUCK'].map((cls) => (
                    <button
                      key={cls}
                      onClick={() => setSelectedClassFilter(cls)}
                      className={`px-2 py-1 rounded transition ${
                        selectedClassFilter === cls
                          ? 'bg-blue-600 text-white font-bold'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      {cls}
                    </button>
                  ))}
                </div>

                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2" />
                  <input
                    type="text"
                    placeholder="Search..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-32 pl-7 pr-2 py-1 rounded-lg bg-[#070d18] border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Content Tab 1: Vehicle Tracks Table */}
            {activeViewTab === 'tracks' && (
              <div className="space-y-4">
                <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#080f1c]">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 bg-[#050912] text-slate-400 font-mono">
                        <th className="py-2.5 px-3">Vehicle Crop</th>
                        <th className="py-2.5 px-3">Track ID</th>
                        <th className="py-2.5 px-3">Vehicle Class</th>
                        <th className="py-2.5 px-3">First Seen</th>
                        <th className="py-2.5 px-3">Last Seen</th>
                        <th className="py-2.5 px-3">Duration</th>
                        <th className="py-2.5 px-3">Sightings</th>
                        <th className="py-2.5 px-3">Avg Confidence</th>
                        <th className="py-2.5 px-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {filteredTracks.length === 0 ? (
                        <tr>
                          <td colSpan={9} className="py-8 text-center text-slate-500">
                            {isProcessing
                              ? 'Tracking vehicles in progress... Track summaries will appear shortly.'
                              : 'No vehicle tracks found.'}
                          </td>
                        </tr>
                      ) : (
                        filteredTracks.map((t) => (
                          <tr
                            key={t.id}
                            className={`hover:bg-slate-800/40 transition cursor-pointer ${
                              selectedTrack?.track_id === t.track_id ? 'bg-blue-900/20' : ''
                            }`}
                            onClick={() => {
                              setSelectedTrack(t);
                              fetchTrackDetail(t.track_id);
                            }}
                          >
                            {/* Crop Thumbnail */}
                            <td className="py-2.5 px-3">
                              {t.crop_url ? (
                                <img
                                  src={t.crop_url}
                                  alt={`Track #${t.track_id}`}
                                  className="w-12 h-8 object-cover rounded bg-slate-900 border border-slate-700 hover:scale-110 transition shadow cursor-pointer"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedCropPreview(t.crop_url);
                                  }}
                                />
                              ) : (
                                <div className="w-12 h-8 rounded bg-[#070d18] border border-slate-800 flex items-center justify-center text-slate-600">
                                  <ImageIcon className="w-4 h-4" />
                                </div>
                              )}
                            </td>

                            {/* Track ID Badge */}
                            <td className="py-2.5 px-3">
                              <span className="px-2 py-0.5 rounded font-bold text-[11px] bg-blue-600/20 text-blue-300 border border-blue-500/40">
                                Track #{t.track_id}
                              </span>
                            </td>

                            {/* Class */}
                            <td className="py-2.5 px-3">
                              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-bold bg-[#070d18] border border-slate-800 uppercase">
                                {getVehicleIcon(t.vehicle_class)}
                                <span className="text-white ml-1">{t.vehicle_class}</span>
                              </span>
                            </td>

                            {/* First Seen */}
                            <td className="py-2.5 px-3 text-emerald-400 font-semibold">
                              {t.first_seen_formatted}
                            </td>

                            {/* Last Seen */}
                            <td className="py-2.5 px-3 text-slate-300">
                              {t.last_seen_formatted}
                            </td>

                            {/* Duration */}
                            <td className="py-2.5 px-3 text-slate-400">
                              {t.duration_seconds}s
                            </td>

                            {/* Detection Count */}
                            <td className="py-2.5 px-3 text-slate-300">
                              {t.detection_count} frames
                            </td>

                            {/* Confidence */}
                            <td className="py-2.5 px-3">
                              <div className="flex items-center space-x-1.5">
                                <div className="w-12 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                                  <div
                                    className="bg-emerald-400 h-1.5 rounded-full"
                                    style={{ width: `${Math.round(t.avg_confidence * 100)}%` }}
                                  ></div>
                                </div>
                                <span className="text-[11px] text-slate-300">{t.avg_confidence_percent}</span>
                              </div>
                            </td>

                            {/* Actions */}
                            <td className="py-2.5 px-3 text-right">
                              <div className="flex items-center justify-end space-x-1">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    seekToTimestamp(t.first_seen_seconds);
                                  }}
                                  className="px-2 py-1 rounded bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/40 flex items-center space-x-1 transition"
                                  title="Jump Video to First Seen"
                                >
                                  <Play className="w-2.5 h-2.5 fill-current" />
                                  <span>Seek</span>
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Selected Track Inspection Panel */}
                {selectedTrack && (
                  <div className="p-5 rounded-xl bg-[#070d18] border border-blue-500/40 shadow-xl space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-400">
                          {getVehicleIcon(selectedTrack.vehicle_class)}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <h3 className="font-bold text-white text-sm">
                              Track #{selectedTrack.track_id} Sightings & Visual Timeline
                            </h3>
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-blue-900/60 text-blue-300">
                              {selectedTrack.vehicle_class}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400">
                            Observed from {selectedTrack.first_seen_formatted} to {selectedTrack.last_seen_formatted} ({selectedTrack.duration_seconds}s across {selectedTrack.detection_count} frames)
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => seekToTimestamp(selectedTrack.first_seen_seconds)}
                          className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center space-x-1.5 shadow"
                        >
                          <Play className="w-3 h-3 fill-current" />
                          <span>Seek to First Sighting ({selectedTrack.first_seen_formatted})</span>
                        </button>

                        <button
                          onClick={() => setSelectedTrack(null)}
                          className="p-1 text-slate-500 hover:text-white"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* Timeline Visual Bar */}
                    <div className="space-y-1 bg-[#050912] p-3 rounded-lg border border-slate-800 text-xs font-mono">
                      <div className="flex justify-between text-slate-400 text-[10px]">
                        <span>Timeline: 00:00.0</span>
                        <span className="text-emerald-400 font-bold">
                          Active: {selectedTrack.first_seen_formatted} ──► {selectedTrack.last_seen_formatted}
                        </span>
                        <span>End of Clip</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-2 relative overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-emerald-500 to-blue-500 h-2 rounded-full absolute"
                          style={{
                            left: `${Math.max(0, (selectedTrack.first_seen_seconds / Math.max(1, footage.duration_seconds || 10)) * 100)}%`,
                            width: `${Math.max(5, (selectedTrack.duration_seconds / Math.max(1, footage.duration_seconds || 10)) * 100)}%`,
                          }}
                        ></div>
                      </div>
                    </div>

                    {/* Track Sightings List */}
                    <div className="max-h-48 overflow-y-auto border border-slate-800 rounded-lg">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-slate-800 bg-[#050912] text-slate-400 font-mono sticky top-0">
                            <th className="py-2 px-3">Timestamp</th>
                            <th className="py-2 px-3">Frame #</th>
                            <th className="py-2 px-3">Confidence</th>
                            <th className="py-2 px-3">Bounding Box [X1, Y1, X2, Y2]</th>
                            <th className="py-2 px-3 text-right">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 font-mono">
                          {(selectedTrackDetails?.detections || []).map((det) => (
                            <tr key={det.id} className="hover:bg-slate-800/30">
                              <td className="py-1.5 px-3 text-emerald-400 font-semibold">{det.formatted_timestamp}</td>
                              <td className="py-1.5 px-3 text-slate-400">#{det.frame_number}</td>
                              <td className="py-1.5 px-3 text-slate-300">{det.confidence_percent}</td>
                              <td className="py-1.5 px-3 text-slate-400 text-[11px]">[{det.x1}, {det.y1}, {det.x2}, {det.y2}]</td>
                              <td className="py-1.5 px-3 text-right">
                                <button
                                  onClick={() => seekToTimestamp(det.timestamp_seconds)}
                                  className="px-2 py-0.5 rounded bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 text-[10px] font-bold"
                                >
                                  Seek
                                </button>
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

            {/* Content Tab 2: Timestamped Detections Log */}
            {activeViewTab === 'detections' && (
              <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#080f1c] max-h-80 overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 bg-[#050912] text-slate-400 font-mono sticky top-0 z-10">
                      <th className="py-2.5 px-4">Timestamp</th>
                      <th className="py-2.5 px-4">Frame #</th>
                      <th className="py-2.5 px-4">Track ID</th>
                      <th className="py-2.5 px-4">Vehicle Class</th>
                      <th className="py-2.5 px-4">Confidence</th>
                      <th className="py-2.5 px-4">Bounding Box [X1, Y1, X2, Y2]</th>
                      <th className="py-2.5 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {filteredDetections.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-slate-500">
                          {isProcessing
                            ? 'Processing video... Sightings will appear shortly.'
                            : 'No vehicle sightings found matching the criteria.'}
                        </td>
                      </tr>
                    ) : (
                      filteredDetections.map((det) => (
                        <tr key={det.id} className="hover:bg-slate-800/30 transition">
                          <td className="py-2 px-4 text-emerald-400 font-bold">
                            {det.formatted_timestamp}
                          </td>

                          <td className="py-2 px-4 text-slate-400">
                            #{det.frame_number}
                          </td>

                          <td className="py-2 px-4">
                            {det.track_id ? (
                              <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-blue-600/20 text-blue-300 border border-blue-500/30">
                                Track #{det.track_id}
                              </span>
                            ) : (
                              <span className="text-slate-500 text-[10px]">Unassigned</span>
                            )}
                          </td>

                          <td className="py-2 px-4">
                            <span className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded text-[11px] font-bold bg-[#070d18] border border-slate-800 uppercase">
                              {getVehicleIcon(det.vehicle_class)}
                              <span className="text-white ml-1">{det.vehicle_class}</span>
                            </span>
                          </td>

                          <td className="py-2 px-4">
                            <div className="flex items-center space-x-2">
                              <div className="w-14 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                                <div
                                  className="bg-emerald-400 h-1.5 rounded-full"
                                  style={{ width: `${Math.round(det.confidence * 100)}%` }}
                                ></div>
                              </div>
                              <span className="text-slate-200">{det.confidence_percent}</span>
                            </div>
                          </td>

                          <td className="py-2 px-4 text-[11px] text-slate-400">
                            [{det.x1}, {det.y1}, {det.x2}, {det.y2}]
                          </td>

                          <td className="py-2 px-4 text-right">
                            <button
                              onClick={() => seekToTimestamp(det.timestamp_seconds)}
                              className="px-2.5 py-1 rounded bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 font-semibold transition"
                            >
                              Seek
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>

      </div>

      {/* Crop Zoom Lightbox Modal */}
      {selectedCropPreview && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md"
          onClick={() => setSelectedCropPreview(null)}
        >
          <div className="relative max-w-lg bg-[#0b1424] p-3 rounded-2xl border border-slate-700 shadow-2xl">
            <button
              onClick={() => setSelectedCropPreview(null)}
              className="absolute -top-3 -right-3 p-1 rounded-full bg-slate-800 text-slate-300 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
            <img
              src={selectedCropPreview}
              alt="Representative Vehicle Crop"
              className="rounded-xl w-full h-auto object-contain max-h-[70vh]"
            />
            <div className="mt-2 text-center text-xs font-mono text-slate-400">
              Representative High-Confidence Crop for Future ANPR & Vehicle Recognition
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

