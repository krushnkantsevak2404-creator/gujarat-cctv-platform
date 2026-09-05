import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Search,
  Filter,
  Shield,
  Car,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  HelpCircle,
  Clock,
  Play,
  Pause,
  RotateCcw,
  Sparkles,
  Layers,
  ChevronRight,
  ZoomIn,
  RefreshCw,
  Eye,
  Info,
  SlidersHorizontal,
  FileCheck,
} from 'lucide-react';

export default function AnprResultsModal({
  footage,
  camera,
  isOpen,
  onClose,
  onRerunAnpr,
}) {
  const [summaryData, setSummaryData] = useState(null);
  const [detections, setDetections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [formatFilter, setFormatFilter] = useState('ALL');
  const [classFilter, setClassFilter] = useState('ALL');
  const [consolidatedOnly, setConsolidatedOnly] = useState(true);

  // Video Player & Seeking
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  // Selected Plate for Details Drawer & Zoom Modal
  const [selectedPlate, setSelectedPlate] = useState(null);
  const [zoomedCropUrl, setZoomedCropUrl] = useState(null);

  // Polling state for in-progress job
  const [jobProgress, setJobProgress] = useState(null);

  useEffect(() => {
    if (isOpen && footage) {
      fetchAnprData();
    }
  }, [isOpen, footage, consolidatedOnly]);

  const fetchAnprData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch summary
      const summaryRes = await fetch(`/api/footage/${footage.id}/anpr/summary`);
      if (!summaryRes.ok) {
        throw new Error(`Failed to load ANPR summary: ${summaryRes.statusText}`);
      }
      const summary = await summaryRes.json();
      setSummaryData(summary);

      // Check if job is still processing
      if (summary.latest_job && (summary.latest_job.status === 'PROCESSING' || summary.latest_job.status === 'QUEUED')) {
        setJobProgress(summary.latest_job);
        pollJobStatus(summary.latest_job.id);
        return;
      }

      // Fetch detections with current consolidated setting
      const detRes = await fetch(
        `/api/footage/${footage.id}/anpr?consolidated_only=${consolidatedOnly}`
      );
      if (detRes.ok) {
        const dets = await detRes.json();
        setDetections(dets);
        if (dets.length > 0 && !selectedPlate) {
          setSelectedPlate(dets[0]);
        }
      }
    } catch (err) {
      console.error('Error fetching ANPR data:', err);
      setError(err.message || 'Error loading ANPR records.');
    } finally {
      setLoading(false);
    }
  };

  const pollJobStatus = (jobId) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/analysis/jobs/${jobId}`);
        if (res.ok) {
          const job = await res.json();
          setJobProgress(job);
          if (job.status === 'COMPLETED') {
            clearInterval(interval);
            setJobProgress(null);
            fetchAnprData();
          } else if (job.status === 'FAILED') {
            clearInterval(interval);
            setJobProgress(null);
            setError(job.error_message || 'ANPR processing failed.');
          }
        }
      } catch (e) {
        console.error('Error polling job:', e);
      }
    }, 1500);
  };

  const handleSeekVideo = (seconds) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      setCurrentTime(seconds);
      if (videoRef.current.paused) {
        videoRef.current.play().catch(() => {});
        setIsPlaying(true);
      }
    }
  };

  const handleVideoTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration || 0);
    }
  };

  const togglePlayPause = () => {
    if (videoRef.current) {
      if (videoRef.current.paused) {
        videoRef.current.play().catch(() => {});
        setIsPlaying(true);
      } else {
        videoRef.current.pause();
        setIsPlaying(false);
      }
    }
  };

  const filteredDetections = detections.filter((d) => {
    if (searchQuery) {
      const q = searchQuery.toUpperCase().replace(/[^A-Z0-9]/g, '');
      const norm = (d.plate_number_normalized || '').toUpperCase();
      const raw = (d.plate_number_raw || '').toUpperCase();
      if (!norm.includes(q) && !raw.includes(q)) return false;
    }
    if (statusFilter !== 'ALL' && d.status !== statusFilter) return false;
    if (formatFilter !== 'ALL' && d.format_status !== formatFilter) return false;
    if (classFilter !== 'ALL' && d.vehicle_class.toUpperCase() !== classFilter) return false;
    return true;
  });

  const formatSecs = (sec) => {
    if (sec == null) return '00:00.0';
    const m = Math.floor(sec / 60);
    const s = (sec % 60).toFixed(1);
    return `${m.toString().padStart(2, '0')}:${s.padStart(4, '0')}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/85 backdrop-blur-md animate-fadeIn">
      <div className="bg-[#070d18] border border-slate-700/80 rounded-2xl w-full max-w-7xl max-h-[95vh] flex flex-col shadow-2xl overflow-hidden">
        
        {/* Header Bar */}
        <div className="px-6 py-4 bg-[#0a1324] border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 shadow-inner">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-white tracking-wide">
                  ANPR & License Plate Intelligence
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                  MILESTONE 6
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/20 text-blue-300 border border-blue-500/30">
                  EasyOCR + Indian Syntax
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Camera: <span className="text-slate-200 font-semibold">{camera?.camera_code} — {camera?.camera_name}</span> ({camera?.location_name || 'Gujarat'}) | File: <span className="font-mono text-slate-300">{footage?.original_file_name}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => onRerunAnpr && onRerunAnpr(footage, camera)}
              className="px-3 py-1.5 rounded-lg bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/40 text-xs font-semibold flex items-center space-x-1.5 transition"
              title="Re-run ANPR & OCR Extraction"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Re-run ANPR</span>
            </button>

            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Processing State Banner */}
        {jobProgress && (
          <div className="px-6 py-4 bg-blue-950/40 border-b border-blue-500/30">
            <div className="flex items-center justify-between text-xs text-blue-300 mb-2">
              <div className="flex items-center space-x-2">
                <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
                <span className="font-semibold">
                  Processing CCTV Footage with YOLO + ByteTrack + EasyOCR...
                </span>
                <span className="font-mono text-slate-400">({jobProgress.device || 'CPU'})</span>
              </div>
              <span className="font-mono font-bold text-amber-400">{jobProgress.progress}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
              <div
                className="bg-gradient-to-r from-blue-500 via-amber-500 to-emerald-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${jobProgress.progress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-[#0c1629] border border-slate-800/90 flex items-center justify-between shadow">
              <div>
                <p className="text-[11px] font-mono uppercase text-slate-400 font-semibold">Total Plates Detected</p>
                <p className="text-2xl font-black text-white mt-1 font-mono">
                  {summaryData?.total_plates_detected || detections.length}
                </p>
                <p className="text-[10px] text-slate-500 mt-0.5">Across all sampled video frames</p>
              </div>
              <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
                <Layers className="w-5 h-5" />
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#0c1629] border border-slate-800/90 flex items-center justify-between shadow">
              <div>
                <p className="text-[11px] font-mono uppercase text-slate-400 font-semibold">Unique Vehicles</p>
                <p className="text-2xl font-black text-amber-400 mt-1 font-mono">
                  {summaryData?.unique_plates_count || (consolidatedOnly ? detections.length : 0)}
                </p>
                <p className="text-[10px] text-slate-500 mt-0.5">ByteTrack deduplicated records</p>
              </div>
              <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Car className="w-5 h-5" />
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#0c1629] border border-slate-800/90 flex items-center justify-between shadow">
              <div>
                <p className="text-[11px] font-mono uppercase text-slate-400 font-semibold">Valid Indian Formats</p>
                <p className="text-2xl font-black text-emerald-400 mt-1 font-mono">
                  {summaryData?.valid_format_count || 0}
                </p>
                <p className="text-[10px] text-slate-500 mt-0.5">GJ/MH/DL/Bharat syntax verified</p>
              </div>
              <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <FileCheck className="w-5 h-5" />
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#0c1629] border border-slate-800/90 flex items-center justify-between shadow">
              <div>
                <p className="text-[11px] font-mono uppercase text-slate-400 font-semibold">OCR Success Rate</p>
                <p className="text-2xl font-black text-indigo-400 mt-1 font-mono">
                  {summaryData?.successful_ocr_count || 0}
                </p>
                <p className="text-[10px] text-slate-500 mt-0.5">High/medium OCR confidence</p>
              </div>
              <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Sparkles className="w-5 h-5" />
              </div>
            </div>
          </div>

          {/* Video Player & Inspector Section */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Left: Video Player with Click-to-Seek Synchronization */}
            <div className="lg:col-span-7 bg-[#08101f] border border-slate-800 rounded-xl overflow-hidden flex flex-col">
              <div className="px-4 py-2.5 bg-[#0a1426] border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center space-x-2 text-xs font-bold text-slate-200">
                  <Play className="w-3.5 h-3.5 text-amber-400" />
                  <span>CCTV Video Playback & Timestamp Synchronization</span>
                </div>
                <div className="text-[11px] font-mono text-slate-400">
                  Time: <span className="text-amber-300 font-bold">{formatSecs(currentTime)}</span> / {formatSecs(duration)}
                </div>
              </div>

              <div className="relative bg-black flex items-center justify-center min-h-[260px] max-h-[360px]">
                <video
                  ref={videoRef}
                  src={`/api/footage/${footage.id}/stream`}
                  className="w-full h-full object-contain max-h-[340px]"
                  onTimeUpdate={handleVideoTimeUpdate}
                  onLoadedMetadata={handleLoadedMetadata}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  controls
                />
              </div>

              {/* Video Timeline Guidance */}
              <div className="p-3 bg-[#060c18] border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <div className="flex items-center space-x-2">
                  <Clock className="w-3.5 h-3.5 text-blue-400" />
                  <span>Click any plate row or timestamp to jump video directly to that frame.</span>
                </div>
                {selectedPlate && (
                  <button
                    onClick={() => handleSeekVideo(selectedPlate.timestamp_seconds)}
                    className="px-2.5 py-1 rounded bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/40 text-[11px] font-bold flex items-center space-x-1 transition"
                  >
                    <span>Jump to {selectedPlate.formatted_timestamp}</span>
                  </button>
                )}
              </div>
            </div>

            {/* Right: Selected Plate Detail Inspector */}
            <div className="lg:col-span-5 bg-[#08101f] border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
              {selectedPlate ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div className="flex items-center space-x-2">
                      <Shield className="w-4 h-4 text-amber-400" />
                      <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                        Plate Intelligence Dossier
                      </h4>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      selectedPlate.status === 'OCR_SUCCESS'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : selectedPlate.status === 'OCR_LOW_CONFIDENCE'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}>
                      {selectedPlate.status}
                    </span>
                  </div>

                  {/* High Contrast Authentic Indian Plate Display */}
                  <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-gradient-to-b from-[#0e1b33] to-[#08101f] border border-slate-700/80 shadow-inner">
                    <div className="relative inline-flex items-center rounded-lg border-2 border-slate-900 bg-[#f8fafc] text-slate-950 font-black shadow-2xl px-4 py-2 select-all tracking-wider font-mono text-xl sm:text-2xl">
                      {/* Indian Blue Flag Emblem Strip */}
                      <div className="absolute left-1 top-1 bottom-1 w-4 bg-[#003893] rounded-l flex flex-col items-center justify-between py-1 text-[7px] text-white font-bold font-sans select-none">
                        <span className="text-[6px] text-amber-400 font-extrabold">IND</span>
                        <div className="w-2 h-2 rounded-full border border-white/80 flex items-center justify-center">
                          <div className="w-1 h-1 bg-amber-400 rounded-full"></div>
                        </div>
                      </div>

                      <div className="pl-5 flex items-center space-x-2">
                        <span>
                          {selectedPlate.plate_number_normalized || selectedPlate.plate_number_raw || 'UNREADABLE'}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3 mt-3 text-xs">
                      <span className="text-slate-400 font-mono">Format:</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        selectedPlate.format_status === 'VALID_FORMAT'
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          : selectedPlate.format_status === 'POSSIBLE_FORMAT'
                          ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                          : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                      }`}>
                        {selectedPlate.format_status}
                      </span>
                      <span className="text-slate-400 font-mono">Confidence:</span>
                      <span className="font-mono font-bold text-amber-400">
                        {selectedPlate.confidence_percent}
                      </span>
                    </div>
                  </div>

                  {/* Plate Crop Preview */}
                  <div>
                    <p className="text-[11px] font-mono text-slate-400 mb-1.5 flex items-center justify-between">
                      <span>Localized Plate Region Crop:</span>
                      {selectedPlate.has_crop && (
                        <button
                          onClick={() => setZoomedCropUrl(selectedPlate.plate_crop_url)}
                          className="text-amber-400 hover:text-amber-300 flex items-center space-x-1 text-[10px]"
                        >
                          <ZoomIn className="w-3 h-3" />
                          <span>Zoom Full-Res</span>
                        </button>
                      )}
                    </p>
                    <div className="p-2 bg-[#040812] border border-slate-800 rounded-lg flex items-center justify-center min-h-[90px]">
                      {selectedPlate.has_crop ? (
                        <img
                          src={selectedPlate.plate_crop_url}
                          alt="Plate Crop"
                          className="max-h-20 rounded border border-slate-700 object-contain shadow cursor-pointer hover:scale-105 transition"
                          onClick={() => setZoomedCropUrl(selectedPlate.plate_crop_url)}
                        />
                      ) : (
                        <div className="text-slate-500 text-xs flex items-center space-x-1 font-mono">
                          <AlertCircle className="w-3.5 h-3.5" />
                          <span>No cropped image saved</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Metadata Key-Value List */}
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono bg-[#050b16] p-3 rounded-lg border border-slate-800/80">
                    <div>
                      <span className="text-slate-500">Vehicle Type:</span>
                      <p className="text-slate-200 font-semibold uppercase">{selectedPlate.vehicle_class}</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Track ID:</span>
                      <p className="text-amber-300 font-bold">#{selectedPlate.track_id || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Video Timestamp:</span>
                      <p className="text-blue-300 font-semibold">{selectedPlate.formatted_timestamp} (frame {selectedPlate.frame_number})</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Frame Sightings:</span>
                      <p className="text-emerald-300 font-semibold">{selectedPlate.sighting_count} occurrences</p>
                    </div>
                    <div className="col-span-2 pt-1 border-t border-slate-800">
                      <span className="text-slate-500">Raw OCR Output:</span>
                      <p className="text-slate-300 font-mono break-all">{selectedPlate.plate_number_raw || 'None'}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs font-mono p-8 text-center">
                  <Shield className="w-10 h-10 text-slate-700 mb-2" />
                  <span>Select any plate detection from the table below to inspect details.</span>
                </div>
              )}
            </div>
          </div>

          {/* Search, Filter Toolbar & Detections Table */}
          <div className="space-y-3">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-3 bg-[#08101f] border border-slate-800 rounded-xl">
              
              {/* Search Bar */}
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search license plate (e.g. GJ01, 1234, MH)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-[#050a14] border border-slate-700/80 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 font-mono"
                />
              </div>

              {/* Filter Selectors */}
              <div className="flex flex-wrap items-center gap-2 text-xs">
                
                {/* Status Filter */}
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-[#050a14] border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-slate-300 focus:outline-none font-mono"
                >
                  <option value="ALL">All OCR Statuses</option>
                  <option value="OCR_SUCCESS">OCR Success</option>
                  <option value="OCR_LOW_CONFIDENCE">Low Confidence</option>
                  <option value="OCR_UNREADABLE">Unreadable</option>
                  <option value="PLATE_DETECTED">Plate Detected</option>
                </select>

                {/* Format Filter */}
                <select
                  value={formatFilter}
                  onChange={(e) => setFormatFilter(e.target.value)}
                  className="bg-[#050a14] border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-slate-300 focus:outline-none font-mono"
                >
                  <option value="ALL">All Formats</option>
                  <option value="VALID_FORMAT">Valid Indian Format</option>
                  <option value="POSSIBLE_FORMAT">Possible Format</option>
                  <option value="UNCERTAIN">Uncertain Syntax</option>
                </select>

                {/* Vehicle Class Filter */}
                <select
                  value={classFilter}
                  onChange={(e) => setClassFilter(e.target.value)}
                  className="bg-[#050a14] border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-slate-300 focus:outline-none font-mono"
                >
                  <option value="ALL">All Vehicle Classes</option>
                  <option value="CAR">Cars</option>
                  <option value="MOTORCYCLE">Motorcycles</option>
                  <option value="BUS">Buses</option>
                  <option value="TRUCK">Trucks</option>
                </select>

                {/* Consolidated Toggle */}
                <button
                  onClick={() => setConsolidatedOnly(!consolidatedOnly)}
                  className={`px-3 py-1.5 rounded-lg border font-mono font-semibold transition ${
                    consolidatedOnly
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}
                  title="Toggle between consolidated vehicle plates and raw frame sightings"
                >
                  {consolidatedOnly ? 'Unique Plates' : 'All Frame Sightings'}
                </button>
              </div>
            </div>

            {/* Detections Records Table */}
            <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#080f1c] shadow">
              <div className="overflow-x-auto max-h-[380px]">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-[#050912] border-b border-slate-800 text-slate-400 font-mono z-10">
                    <tr>
                      <th className="py-2.5 px-3">Crop</th>
                      <th className="py-2.5 px-3">License Plate Number</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Format Syntax</th>
                      <th className="py-2.5 px-3">Vehicle Class</th>
                      <th className="py-2.5 px-3">Track ID</th>
                      <th className="py-2.5 px-3">Timestamp</th>
                      <th className="py-2.5 px-3">Confidence</th>
                      <th className="py-2.5 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredDetections.length === 0 ? (
                      <tr>
                        <td colSpan="9" className="py-8 text-center text-slate-500 font-mono">
                          {loading ? 'Loading ANPR records...' : 'No license plate detections match current filters.'}
                        </td>
                      </tr>
                    ) : (
                      filteredDetections.map((det) => {
                        const isSelected = selectedPlate?.id === det.id;
                        return (
                          <tr
                            key={det.id}
                            onClick={() => setSelectedPlate(det)}
                            className={`cursor-pointer transition ${
                              isSelected
                                ? 'bg-amber-500/10 border-l-2 border-amber-400'
                                : 'hover:bg-slate-800/30'
                            }`}
                          >
                            {/* Crop Thumbnail */}
                            <td className="py-2 px-3">
                              {det.has_crop ? (
                                <img
                                  src={det.plate_crop_url}
                                  alt="Plate"
                                  className="w-14 h-7 object-cover rounded border border-slate-700 bg-black"
                                />
                              ) : (
                                <div className="w-14 h-7 bg-slate-900 border border-slate-800 rounded flex items-center justify-center text-[9px] text-slate-600 font-mono">
                                  N/A
                                </div>
                              )}
                            </td>

                            {/* Normalized License Plate Badge */}
                            <td className="py-2 px-3">
                              <span className="inline-block px-2.5 py-1 rounded bg-[#f8fafc] text-slate-950 font-black font-mono tracking-wider text-xs border border-slate-900 shadow-sm">
                                {det.plate_number_normalized || det.plate_number_raw || 'UNREADABLE'}
                              </span>
                            </td>

                            {/* OCR Status */}
                            <td className="py-2 px-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                                det.status === 'OCR_SUCCESS'
                                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                                  : det.status === 'OCR_LOW_CONFIDENCE'
                                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                                  : 'bg-slate-800 text-slate-400 border border-slate-700'
                              }`}>
                                {det.status}
                              </span>
                            </td>

                            {/* Format Status */}
                            <td className="py-2 px-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                                det.format_status === 'VALID_FORMAT'
                                  ? 'text-emerald-400 font-bold'
                                  : det.format_status === 'POSSIBLE_FORMAT'
                                  ? 'text-blue-400'
                                  : 'text-slate-500'
                              }`}>
                                {det.format_status}
                              </span>
                            </td>

                            {/* Vehicle Class */}
                            <td className="py-2 px-3 font-semibold uppercase text-slate-300">
                              {det.vehicle_class}
                            </td>

                            {/* Track ID */}
                            <td className="py-2 px-3 font-mono text-amber-300 font-bold">
                              #{det.track_id || 'N/A'}
                            </td>

                            {/* Timestamp */}
                            <td className="py-2 px-3 font-mono text-blue-300">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleSeekVideo(det.timestamp_seconds);
                                }}
                                className="hover:underline flex items-center space-x-1"
                                title="Jump video to this timestamp"
                              >
                                <span>{det.formatted_timestamp}</span>
                              </button>
                            </td>

                            {/* Confidence */}
                            <td className="py-2 px-3 font-mono">
                              <div className="flex items-center space-x-2">
                                <div className="w-12 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                                  <div
                                    className={`h-1.5 rounded-full ${
                                      det.confidence >= 0.7
                                        ? 'bg-emerald-400'
                                        : det.confidence >= 0.4
                                        ? 'bg-amber-400'
                                        : 'bg-rose-400'
                                    }`}
                                    style={{ width: det.confidence_percent }}
                                  ></div>
                                </div>
                                <span className="text-slate-300">{det.confidence_percent}</span>
                              </div>
                            </td>

                            {/* Actions */}
                            <td className="py-2 px-3 text-right">
                              <div className="flex items-center justify-end space-x-1">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleSeekVideo(det.timestamp_seconds);
                                  }}
                                  className="p-1 rounded bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 transition"
                                  title="Seek Video to Timestamp"
                                >
                                  <Play className="w-3 h-3 fill-current" />
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedPlate(det);
                                  }}
                                  className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                                  title="Inspect Plate"
                                >
                                  <Eye className="w-3 h-3" />
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

        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-[#0a1324] border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-amber-400" />
            <span>Gujarat Police Innovation Hackathon 2026 — Model 2: Unified CCTV Intelligence</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold transition"
          >
            Close
          </button>
        </div>

      </div>

      {/* Full Resolution Zoom Modal */}
      {zoomedCropUrl && (
        <div
          className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md"
          onClick={() => setZoomedCropUrl(null)}
        >
          <div
            className="relative bg-[#0b1424] p-4 rounded-xl border border-slate-700 max-w-lg shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
              <span className="text-xs font-bold text-white font-mono">High-Resolution License Plate Crop</span>
              <button
                onClick={() => setZoomedCropUrl(null)}
                className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <img
              src={zoomedCropUrl}
              alt="Zoomed Plate Crop"
              className="w-full rounded border border-slate-700 bg-black object-contain max-h-[300px]"
            />
          </div>
        </div>
      )}
    </div>
  );
}
